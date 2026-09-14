from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ResponseMeta


class CreateQuizRequest(BaseModel):
    client_id: str = Field(min_length=16, max_length=128)
    concept_id: str | None = Field(default=None, max_length=64)


class SubmitAttemptRequest(BaseModel):
    client_id: str = Field(min_length=16, max_length=128)
    answer: str = Field(min_length=1, max_length=5000)


class QuizPublic(BaseModel):
    id: UUID
    learning_space_id: UUID
    concept_id: str | None = None
    question: str
    source_keys: list[str]


class GradePublic(BaseModel):
    id: UUID
    quiz_id: UUID
    score: int
    strengths: list[str]
    improvements: list[str]
    next_step: str


class QuizResponse(BaseModel):
    data: QuizPublic
    meta: ResponseMeta


class GradeResponse(BaseModel):
    data: GradePublic
    meta: ResponseMeta
