import json
import re
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.core.errors import LLMInvalidOutputError

ModelT = TypeVar("ModelT", bound=BaseModel)
_CODE_BLOCK = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


def parse_structured_output(text: str, response_model: type[ModelT]) -> ModelT:
    candidate = text.strip()
    block = _CODE_BLOCK.search(candidate)
    if block:
        candidate = block.group(1).strip()
    else:
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start >= 0 and end > start:
            candidate = candidate[start : end + 1]
    try:
        payload = json.loads(candidate)
        return response_model.model_validate(payload)
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        raise LLMInvalidOutputError(str(exc)) from exc

