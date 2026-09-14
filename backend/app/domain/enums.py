from enum import StrEnum


class UserLevel(StrEnum):
    BEGINNER = "beginner"
    STARTER = "starter"
    EXPERIENCED = "experienced"


class LearningGoal(StrEnum):
    UNDERSTAND = "understand"
    PROJECT = "project"
    INTERVIEW = "interview"


class SpaceStatus(StrEnum):
    CREATED = "created"
    ANALYZING = "analyzing"
    READY = "ready"
    FAILED = "failed"


class SourceProvider(StrEnum):
    ZHIHU = "zhihu"
    DEMO = "demo"


class ConceptCategory(StrEnum):
    CORE = "core"
    PREREQUISITE = "prerequisite"
    PRACTICE = "practice"
    DEBATE = "debate"
    EXTENSION = "extension"


class EdgeType(StrEnum):
    PREREQUISITE_OF = "PREREQUISITE_OF"
    PART_OF = "PART_OF"
    LEARN_AFTER = "LEARN_AFTER"
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    APPLIES_TO = "APPLIES_TO"


class ExecutionMode(StrEnum):
    LIVE = "live"
    DEMO = "demo"
    PRECOMPUTED = "precomputed"

