from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.domain.analysis_models import AnalysisResult, StudyPlan
from app.domain.entities import LearningSpace, PreparedSource
from app.domain.enums import LearningGoal, UserLevel
from app.schemas.common import ResponseMeta


class CreateSpaceRequest(BaseModel):
    client_id: str = Field(min_length=16, max_length=128)
    topic: str = Field(min_length=2, max_length=100)
    level: UserLevel
    goal: LearningGoal
    daily_minutes: int

    @field_validator("topic")
    @classmethod
    def normalize_topic(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("daily_minutes")
    @classmethod
    def validate_minutes(cls, value: int) -> int:
        if value not in {15, 30, 60, 90}:
            raise ValueError("daily_minutes must be 15, 30, 60, or 90")
        return value


class AnalyzeSpaceRequest(BaseModel):
    client_id: str = Field(min_length=16, max_length=128)
    force: bool = False


class OwnedSpaceRequest(BaseModel):
    client_id: str = Field(min_length=16, max_length=128)
    force: bool = False


class AnalysisData(BaseModel):
    space: LearningSpace
    sources: list[PreparedSource]
    analysis: AnalysisResult


class CompleteSpaceData(BaseModel):
    space: LearningSpace
    sources: list[PreparedSource] = Field(default_factory=list)
    analysis: AnalysisResult | None = None
    plan: StudyPlan | None = None
    quizzes: list[dict[str, Any]] = Field(default_factory=list)


class PlanData(BaseModel):
    plan: StudyPlan


class GeneratePlanRequest(BaseModel):
    client_id: str = Field(min_length=16, max_length=128)
    force: bool = False


class SpaceResponse(BaseModel):
    data: LearningSpace
    meta: ResponseMeta


class AnalysisResponse(BaseModel):
    data: AnalysisData
    meta: ResponseMeta


class CompleteSpaceResponse(BaseModel):
    data: CompleteSpaceData
    meta: ResponseMeta


class PlanResponse(BaseModel):
    data: StudyPlan
    meta: ResponseMeta
