from typing import Any, Protocol, TypeVar
from uuid import UUID

from pydantic import BaseModel

from app.domain.analysis_models import (
    AnalysisResult,
    GradeResult,
    QuizDraft,
    SourceViewpoint,
    StudyPlan,
)
from app.domain.entities import (
    CreateSpaceCommand,
    LearningSpace,
    PreparedSource,
    RetrievedSource,
)

ModelT = TypeVar("ModelT", bound=BaseModel)


class ContentProviderPort(Protocol):
    async def search(self, query: str, limit: int) -> list[RetrievedSource]: ...


class LLMPort(Protocol):
    @property
    def model_name(self) -> str: ...

    async def generate_structured(
        self,
        *,
        task_name: str,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ModelT],
    ) -> ModelT: ...


class LearningRepositoryPort(Protocol):
    async def create_space(self, command: CreateSpaceCommand) -> LearningSpace: ...

    async def get_owned_space(
        self, space_id: UUID, client_id: str
    ) -> LearningSpace | None: ...

    async def try_mark_analyzing(
        self, space_id: UUID, *, allow_ready: bool = False
    ) -> bool: ...

    async def mark_ready(self, space_id: UUID) -> None: ...

    async def mark_failed(self, space_id: UUID, safe_message: str) -> None: ...

    async def replace_sources(
        self, space_id: UUID, sources: list[PreparedSource]
    ) -> None: ...

    async def get_sources(self, space_id: UUID) -> list[PreparedSource]: ...

    async def save_analysis(
        self,
        space_id: UUID,
        result: AnalysisResult,
        source_viewpoints: list[SourceViewpoint],
        model_name: str,
        prompt_version: str,
    ) -> None: ...

    async def get_analysis(self, space_id: UUID) -> AnalysisResult | None: ...

    async def get_complete_space(
        self, space_id: UUID, client_id: str
    ) -> dict[str, Any] | None: ...

    async def save_plan(self, space_id: UUID, plan: StudyPlan) -> StudyPlan: ...

    async def get_plan(self, space_id: UUID) -> StudyPlan | None: ...

    async def save_quiz(self, space_id: UUID, quiz: QuizDraft) -> dict[str, Any]: ...

    async def get_quiz(self, quiz_id: UUID) -> dict[str, Any] | None: ...

    async def save_attempt(
        self,
        quiz_id: UUID,
        client_id: str,
        answer: str,
        grade: GradeResult,
    ) -> dict[str, Any]: ...

