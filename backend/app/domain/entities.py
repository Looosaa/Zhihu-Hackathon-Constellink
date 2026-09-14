from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl

from app.domain.enums import (
    LearningGoal,
    SourceProvider,
    SpaceStatus,
    UserLevel,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CreateSpaceCommand(BaseModel):
    client_id: str
    topic: str
    level: UserLevel
    goal: LearningGoal
    daily_minutes: int


class LearningSpace(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    client_id: str
    topic: str
    level: UserLevel
    goal: LearningGoal
    daily_minutes: int
    status: SpaceStatus = SpaceStatus.CREATED
    error_message: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class RetrievedSource(BaseModel):
    """Provider-neutral content returned before local ranking and numbering."""

    external_id: str = Field(min_length=1, max_length=256)
    provider: SourceProvider
    content_type: str = Field(default="answer", min_length=1, max_length=40)
    title: str = Field(min_length=1, max_length=500)
    author_name: str = Field(min_length=1, max_length=200)
    author_badge: str | None = Field(default=None, max_length=300)
    source_url: HttpUrl
    excerpt: str = Field(min_length=1)
    published_at: datetime | None = None
    engagement: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)


class PreparedSource(RetrievedSource):
    """Cleaned source with an analysis-local citation key such as S1."""

    source_key: str = Field(pattern=r"^S[1-9][0-9]*$")

