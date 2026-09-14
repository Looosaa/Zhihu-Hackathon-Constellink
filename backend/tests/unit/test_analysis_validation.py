import pytest

from app.domain.analysis_models import AnalysisResult


def valid_payload() -> dict:
    return {
        "overview": "Overview",
        "consensus": [
            {"id": "c1", "title": "Common view", "detail": "Details", "source_keys": ["S1", "S2"]}
        ],
        "disagreements": [],
        "concepts": [
            {"id": "python", "label": "Python", "category": "core", "description": "Basics", "source_keys": ["S1"]}
        ],
        "edges": [],
        "warnings": [],
    }


def test_analysis_rejects_unknown_source_reference():
    result = AnalysisResult.model_validate(valid_payload())
    with pytest.raises(ValueError, match="Unknown source keys"):
        result.validate_references({"S2"})


def test_analysis_rejects_edge_to_unknown_concept():
    payload = valid_payload()
    payload["edges"] = [
        {"source": "python", "target": "missing", "type": "PREREQUISITE_OF", "label": "before"}
    ]
    result = AnalysisResult.model_validate(payload)
    with pytest.raises(ValueError, match="unknown concept"):
        result.validate_references({"S1", "S2"})

