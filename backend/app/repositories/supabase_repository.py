import asyncio
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import UUID

from app.core.errors import RepositoryError
from app.domain.analysis_models import (
    AnalysisResult,
    GradeResult,
    QuizDraft,
    SourceViewpoint,
    StudyPlan,
)
from app.domain.entities import CreateSpaceCommand, LearningSpace, PreparedSource


class SupabaseLearningRepository:
    """Supabase adapter. The synchronous SDK is isolated behind asyncio.to_thread."""

    def __init__(self, url: str, service_role_key: str):
        try:
            from supabase import create_client
        except ImportError as exc:
            raise RepositoryError("Install the supabase package") from exc
        self.client = create_client(url, service_role_key)

    async def _execute(self, operation: Callable[[], Any]) -> Any:
        try:
            response = await asyncio.to_thread(operation)
            return response.data
        except Exception as exc:
            raise RepositoryError(str(exc)) from exc

    async def create_space(self, command: CreateSpaceCommand) -> LearningSpace:
        data = await self._execute(
            lambda: self.client.table("learning_spaces")
            .insert(command.model_dump(mode="json"))
            .execute()
        )
        return LearningSpace.model_validate(data[0])

    async def get_owned_space(
        self, space_id: UUID, client_id: str
    ) -> LearningSpace | None:
        data = await self._execute(
            lambda: self.client.table("learning_spaces")
            .select("*")
            .eq("id", str(space_id))
            .eq("client_id", client_id)
            .limit(1)
            .execute()
        )
        return LearningSpace.model_validate(data[0]) if data else None

    async def try_mark_analyzing(
        self, space_id: UUID, *, allow_ready: bool = False
    ) -> bool:
        allowed = ["created", "failed"] + (["ready"] if allow_ready else [])
        data = await self._execute(
            lambda: self.client.table("learning_spaces")
            .update(
                {
                    "status": "analyzing",
                    "error_message": None,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            .eq("id", str(space_id))
            .in_("status", allowed)
            .execute()
        )
        return bool(data)

    async def mark_ready(self, space_id: UUID) -> None:
        await self._set_status(space_id, "ready", None)

    async def mark_failed(self, space_id: UUID, safe_message: str) -> None:
        await self._set_status(space_id, "failed", safe_message)

    async def _set_status(
        self, space_id: UUID, status: str, error_message: str | None
    ) -> None:
        await self._execute(
            lambda: self.client.table("learning_spaces")
            .update(
                {
                    "status": status,
                    "error_message": error_message,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            .eq("id", str(space_id))
            .execute()
        )

    async def replace_sources(
        self, space_id: UUID, sources: list[PreparedSource]
    ) -> None:
        await self._execute(
            lambda: self.client.table("sources")
            .delete()
            .eq("learning_space_id", str(space_id))
            .execute()
        )
        payload = [
            {
                "learning_space_id": str(space_id),
                "source_key": item.source_key,
                "provider": item.provider.value,
                "content_type": item.content_type,
                "title": item.title,
                "author_name": item.author_name,
                "author_badge": item.author_badge,
                "source_url": str(item.source_url),
                "excerpt": item.excerpt,
                "published_at": item.published_at.isoformat() if item.published_at else None,
                "engagement": item.engagement,
                "metadata": {**item.metadata, "external_id": item.external_id},
            }
            for item in sources
        ]
        if payload:
            await self._execute(
                lambda: self.client.table("sources").insert(payload).execute()
            )

    async def get_sources(self, space_id: UUID) -> list[PreparedSource]:
        data = await self._execute(
            lambda: self.client.table("sources")
            .select("*")
            .eq("learning_space_id", str(space_id))
            .order("source_key")
            .execute()
        )
        return [self._source_from_row(item) for item in data]

    async def save_analysis(
        self,
        space_id: UUID,
        result: AnalysisResult,
        source_viewpoints: list[SourceViewpoint],
        model_name: str,
        prompt_version: str,
    ) -> None:
        payload = {
            "learning_space_id": str(space_id),
            "overview": result.overview,
            "consensus": [item.model_dump(mode="json") for item in result.consensus],
            "disagreements": [item.model_dump(mode="json") for item in result.disagreements],
            "concepts": [item.model_dump(mode="json") for item in result.concepts],
            "edges": [item.model_dump(mode="json") for item in result.edges],
            "source_summaries": [item.model_dump(mode="json") for item in source_viewpoints],
            "warnings": result.warnings,
            "model_name": model_name,
            "prompt_version": prompt_version,
        }
        await self._execute(
            lambda: self.client.table("analyses")
            .upsert(payload, on_conflict="learning_space_id")
            .execute()
        )

    async def get_analysis(self, space_id: UUID) -> AnalysisResult | None:
        data = await self._execute(
            lambda: self.client.table("analyses")
            .select("*")
            .eq("learning_space_id", str(space_id))
            .limit(1)
            .execute()
        )
        if not data:
            return None
        row = data[0]
        return AnalysisResult.model_validate(
            {key: row.get(key, [] if key != "overview" else "") for key in (
                "overview", "consensus", "disagreements", "concepts", "edges", "warnings"
            )}
        )

    async def get_complete_space(
        self, space_id: UUID, client_id: str
    ) -> dict[str, Any] | None:
        space = await self.get_owned_space(space_id, client_id)
        if space is None:
            return None
        quizzes = await self._execute(
            lambda: self.client.table("quizzes")
            .select("id,learning_space_id,concept_id,question,source_keys,created_at")
            .eq("learning_space_id", str(space_id))
            .execute()
        )
        return {
            "space": space,
            "sources": await self.get_sources(space_id),
            "analysis": await self.get_analysis(space_id),
            "plan": await self.get_plan(space_id),
            "quizzes": quizzes,
        }

    async def save_plan(self, space_id: UUID, plan: StudyPlan) -> StudyPlan:
        payload = {
            "learning_space_id": str(space_id),
            "strategy": plan.strategy,
            "days": [item.model_dump(mode="json") for item in plan.days],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        await self._execute(
            lambda: self.client.table("study_plans")
            .upsert(payload, on_conflict="learning_space_id")
            .execute()
        )
        return plan

    async def get_plan(self, space_id: UUID) -> StudyPlan | None:
        data = await self._execute(
            lambda: self.client.table("study_plans")
            .select("strategy,days")
            .eq("learning_space_id", str(space_id))
            .limit(1)
            .execute()
        )
        return StudyPlan.model_validate(data[0]) if data else None

    async def save_quiz(self, space_id: UUID, quiz: QuizDraft) -> dict[str, Any]:
        payload = {"learning_space_id": str(space_id), **quiz.model_dump(mode="json")}
        data = await self._execute(
            lambda: self.client.table("quizzes").insert(payload).execute()
        )
        return self._public_quiz(data[0])

    async def get_quiz(self, quiz_id: UUID) -> dict[str, Any] | None:
        data = await self._execute(
            lambda: self.client.table("quizzes")
            .select("*")
            .eq("id", str(quiz_id))
            .limit(1)
            .execute()
        )
        return data[0] if data else None

    async def save_attempt(
        self,
        quiz_id: UUID,
        client_id: str,
        answer: str,
        grade: GradeResult,
    ) -> dict[str, Any]:
        payload = {
            "quiz_id": str(quiz_id),
            "client_id": client_id,
            "answer": answer,
            **grade.model_dump(mode="json"),
        }
        data = await self._execute(
            lambda: self.client.table("quiz_attempts").insert(payload).execute()
        )
        row = dict(data[0])
        row.pop("answer", None)
        return row

    @staticmethod
    def _source_from_row(row: dict[str, Any]) -> PreparedSource:
        metadata = row.get("metadata") or {}
        return PreparedSource.model_validate(
            {
                "external_id": metadata.get("external_id", row["id"]),
                "source_key": row["source_key"],
                "provider": row["provider"],
                "content_type": row["content_type"],
                "title": row["title"],
                "author_name": row["author_name"],
                "author_badge": row.get("author_badge"),
                "source_url": row["source_url"],
                "excerpt": row["excerpt"],
                "published_at": row.get("published_at"),
                "engagement": row.get("engagement") or {},
                "metadata": metadata,
            }
        )

    @staticmethod
    def _public_quiz(row: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in row.items() if key not in {"reference_answer", "rubric"}}

