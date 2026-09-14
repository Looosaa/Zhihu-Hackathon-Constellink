import pytest
from pydantic import BaseModel

from app.core.errors import LLMInvalidOutputError
from app.providers.llm.json_parser import parse_structured_output


class Example(BaseModel):
    value: int


def test_parser_accepts_json_code_block():
    result = parse_structured_output("```json\n{\"value\": 3}\n```", Example)
    assert result.value == 3


def test_parser_extracts_json_from_surrounding_text():
    result = parse_structured_output("Result: {\"value\": 7} done", Example)
    assert result.value == 7


def test_parser_rejects_invalid_json():
    with pytest.raises(LLMInvalidOutputError):
        parse_structured_output("not json", Example)

