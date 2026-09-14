import asyncio
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from app.domain.analysis_models import (
    AnalysisResult,
    GradeResult,
    QuizDraft,
    SourceViewpoint,
    StudyPlan,
)
from app.domain.entities import CreateSpaceCommand, LearningSpace, PreparedSource
from app.domain.enums import SpaceStatus


class MemoryLearningRepository:
    """Process-local repository used for development, tests, and offline demos."""

    def __init__(self):
        self.spaces: dict[UUID, LearningSpace] = {}
        self.sources: dict[UUID, list[PreparedSource]] = {}
        self.analyses: dict[UUID, AnalysisResult] = {}
        self.source_viewpoints: dict[UUID, list[SourceViewpoint]] = {}
        self.plans: dict[UUID, StudyPlan] = {}
        self.quizzes: dict[UUID, dict[str, Any]] = {}
        self.attempts: dict[UUID, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def create_space(self, command: CreateSpaceCommand) -> LearningSpace:
        space = LearningSpace(**command.model_dump())
        async with self._lock:
            self.spaces[space.id] = space
        return space.model_copy(deep=True)

    async def get_owned_space(
        self, space_id: UUID, client_id: str
    ) -> LearningSpace | None:
        space = self.spaces.get(space_id)
        if space is None or space.client_id != client_id:
            return None
        return space.model_copy(deep=True)

    async def try_mark_analyzing(
        self, space_id: UUID, *, allow_ready: bool = False
    ) -> bool:
        async with self._lock:
            space = self.spaces.get(space_id)
            if space is None:
                return False
            allowed = {SpaceStatus.CREATED, SpaceStatus.FAILED}
            if allow_ready:
                allowed.add(SpaceStatus.READY)
            if space.status not in allowed:
                return False
            self.spaces[space_id] = space.model_copy(
                update={
                    "status": SpaceStatus.ANALYZING,
                    "error_message": None,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
            return True

    async def mark_ready(self, space_id: UUID) -> None:
        await self._update_status(space_id, SpaceStatus.READY, None)

    async def mark_failed(self, space_id: UUID, safe_message: str) -> None:
        await self._update_status(space_id, SpaceStatus.FAILED, safe_message)

    async def _update_status(
        self, space_id: UUID, status: SpaceStatus, error_message: str | None
    ) -> None:
        async with self._lock:
            space = self.spaces.get(space_id)
            if space is not None:
                self.spaces[space_id] = space.model_copy(
                    update={
                        "status": status,
                        "error_message": error_message,
                        "updated_at": datetime.now(timezone.utc),
                    }
                )

    async def replace_sources(
        self, space_id: UUID, sources: list[PreparedSource]
    ) -> None:
        self.sources[space_id] = [item.model_copy(deep=True) for item in sources]

    async def get_sources(self, space_id: UUID) -> list[PreparedSource]:
        return [item.model_copy(deep=True) for item in self.sources.get(space_id, [])]

    async def save_analysis(
        self,
        space_id: UUID,
        result: AnalysisResult,
        source_viewpoints: list[SourceViewpoint],
        model_name: str,
        prompt_version: str,
    ) -> None:
        self.analyses[space_id] = result.model_copy(deep=True)
        self.source_viewpoints[space_id] = [
            item.model_copy(deep=True) for item in source_viewpoints
        ]

    async def get_analysis(self, space_id: UUID) -> AnalysisResult | None:
        item = self.analyses.get(space_id)
        return item.model_copy(deep=True) if item else None

    async def get_complete_space(
        self, space_id: UUID, client_id: str
    ) -> dict[str, Any] | None:
        space = await self.get_owned_space(space_id, client_id)
        if space is None:
            return None
        quizzes = [
            self._public_quiz(item)
            for item in self.quizzes.values()
            if item["learning_space_id"] == space_id
        ]
        return {
            "space": space,
            "sources": await self.get_sources(space_id),
            "analysis": await self.get_analysis(space_id),
            "plan": await self.get_plan(space_id),
            "quizzes": quizzes,
        }

    async def save_plan(self, space_id: UUID, plan: StudyPlan) -> StudyPlan:
        self.plans[space_id] = plan.model_copy(deep=True)
        return plan.model_copy(deep=True)

    async def get_plan(self, space_id: UUID) -> StudyPlan | None:
        plan = self.plans.get(space_id)
        return plan.model_copy(deep=True) if plan else None

    async def save_quiz(self, space_id: UUID, quiz: QuizDraft) -> dict[str, Any]:
        quiz_id = uuid4()
        record = {
            "id": quiz_id,
            "learning_space_id": space_id,
            **quiz.model_dump(),
        }
        self.quizzes[quiz_id] = record
        return self._public_quiz(record)

    async def get_quiz(self, quiz_id: UUID) -> dict[str, Any] | None:
        item = self.quizzes.get(quiz_id)
        return dict(item) if item else None

    async def save_attempt(
        self,
        quiz_id: UUID,
        client_id: str,
        answer: str,
        grade: GradeResult,
    ) -> dict[str, Any]:
        attempt_id = uuid4()
        record = {
            "id": attempt_id,
            "quiz_id": quiz_id,
            "client_id": client_id,
            "answer": answer,
            **grade.model_dump(),
        }
        self.attempts[attempt_id] = record
        return {key: value for key, value in record.items() if key != "answer"}

    @staticmethod
    def _public_quiz(item: dict[str, Any]) -> dict[str, Any]:
        return {
            key: value
            for key, value in item.items()
            if key not in {"reference_answer", "rubric"}
        }

