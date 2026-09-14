from pydantic import BaseModel, Field, model_validator

from app.domain.entities import LearningSpace, PreparedSource
from app.domain.enums import ConceptCategory, EdgeType, ExecutionMode


class Claim(BaseModel):
    text: str = Field(min_length=1, max_length=300)
    evidence: str = Field(min_length=1, max_length=500)
    confidence: float = Field(ge=0, le=1)


class ExtractedConcept(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    definition: str = Field(min_length=1, max_length=300)


class SourceViewpoint(BaseModel):
    source_key: str = Field(pattern=r"^S[1-9][0-9]*$")
    relevance_score: float = Field(ge=0, le=1)
    position_summary: str = Field(min_length=1, max_length=300)
    claims: list[Claim] = Field(default_factory=list, max_length=8)
    concepts: list[ExtractedConcept] = Field(default_factory=list, max_length=12)
    suitable_for: list[str] = Field(default_factory=list, max_length=8)
    limitations: list[str] = Field(default_factory=list, max_length=8)


class ConsensusItem(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=120)
    detail: str = Field(min_length=1, max_length=600)
    source_keys: list[str] = Field(min_length=2, max_length=12)


class DebateSide(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    reason: str = Field(min_length=1, max_length=500)
    suitable_for: list[str] = Field(default_factory=list, max_length=8)
    source_keys: list[str] = Field(min_length=1, max_length=12)


class DisagreementItem(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    question: str = Field(min_length=1, max_length=200)
    side_a: DebateSide
    side_b: DebateSide
    how_to_choose: str = Field(min_length=1, max_length=600)


class GraphConcept(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9_]{1,64}$")
    label: str = Field(min_length=1, max_length=100)
    category: ConceptCategory
    description: str = Field(min_length=1, max_length=500)
    source_keys: list[str] = Field(min_length=1, max_length=12)


class GraphEdge(BaseModel):
    source: str = Field(pattern=r"^[a-z0-9_]{1,64}$")
    target: str = Field(pattern=r"^[a-z0-9_]{1,64}$")
    type: EdgeType
    label: str = Field(min_length=1, max_length=80)


class AnalysisResult(BaseModel):
    overview: str = Field(min_length=1, max_length=1000)
    consensus: list[ConsensusItem] = Field(default_factory=list, max_length=10)
    disagreements: list[DisagreementItem] = Field(default_factory=list, max_length=6)
    concepts: list[GraphConcept] = Field(default_factory=list, max_length=40)
    edges: list[GraphEdge] = Field(default_factory=list, max_length=100)
    warnings: list[str] = Field(default_factory=list, max_length=10)

    def validate_references(self, valid_source_keys: set[str]) -> None:
        referenced: list[str] = []
        for item in self.consensus:
            referenced.extend(item.source_keys)
        for item in self.disagreements:
            referenced.extend(item.side_a.source_keys)
            referenced.extend(item.side_b.source_keys)
        for item in self.concepts:
            referenced.extend(item.source_keys)

        unknown_sources = set(referenced) - valid_source_keys
        if unknown_sources:
            raise ValueError(f"Unknown source keys: {sorted(unknown_sources)}")

        concept_ids = {item.id for item in self.concepts}
        if len(concept_ids) != len(self.concepts):
            raise ValueError("Concept IDs must be unique")

        for edge in self.edges:
            if edge.source not in concept_ids or edge.target not in concept_ids:
                raise ValueError(
                    f"Edge references unknown concept: {edge.source} -> {edge.target}"
                )


class StudyDay(BaseModel):
    day: int = Field(ge=1, le=7)
    title: str = Field(min_length=1, max_length=120)
    goal: str = Field(min_length=1, max_length=300)
    concept_ids: list[str] = Field(default_factory=list, max_length=12)
    activities: list[str] = Field(min_length=1, max_length=8)
    source_keys: list[str] = Field(default_factory=list, max_length=12)
    output: str = Field(min_length=1, max_length=400)
    self_check: str = Field(min_length=1, max_length=400)
    estimated_minutes: int = Field(ge=5, le=180)


class StudyPlan(BaseModel):
    strategy: str = Field(min_length=1, max_length=1000)
    days: list[StudyDay] = Field(min_length=7, max_length=7)

    @model_validator(mode="after")
    def validate_days(self) -> "StudyPlan":
        if sorted(day.day for day in self.days) != list(range(1, 8)):
            raise ValueError("Plan days must be exactly 1 through 7")
        return self

    def validate_context(
        self,
        *,
        daily_minutes: int,
        valid_concept_ids: set[str],
        valid_source_keys: set[str],
    ) -> None:
        max_minutes = int(daily_minutes * 1.1)
        for day in self.days:
            if day.estimated_minutes > max_minutes:
                raise ValueError(f"Day {day.day} exceeds daily time budget")
            unknown_concepts = set(day.concept_ids) - valid_concept_ids
            unknown_sources = set(day.source_keys) - valid_source_keys
            if unknown_concepts:
                raise ValueError(f"Unknown concept IDs: {sorted(unknown_concepts)}")
            if unknown_sources:
                raise ValueError(f"Unknown source keys: {sorted(unknown_sources)}")


class RubricItem(BaseModel):
    criterion: str = Field(min_length=1, max_length=300)
    points: int = Field(ge=1, le=100)


class QuizDraft(BaseModel):
    concept_id: str | None = None
    question: str = Field(min_length=1, max_length=800)
    reference_answer: str = Field(min_length=1, max_length=2000)
    rubric: list[RubricItem] = Field(min_length=1, max_length=8)
    source_keys: list[str] = Field(default_factory=list, max_length=12)

    @model_validator(mode="after")
    def validate_points(self) -> "QuizDraft":
        if sum(item.points for item in self.rubric) != 100:
            raise ValueError("Rubric points must add up to 100")
        return self


class GradeResult(BaseModel):
    score: int = Field(ge=0, le=100)
    strengths: list[str] = Field(default_factory=list, max_length=3)
    improvements: list[str] = Field(default_factory=list, max_length=3)
    next_step: str = Field(min_length=1, max_length=500)


class AnalysisBundle(BaseModel):
    space: LearningSpace
    sources: list[PreparedSource]
    analysis: AnalysisResult
    execution_mode: ExecutionMode
