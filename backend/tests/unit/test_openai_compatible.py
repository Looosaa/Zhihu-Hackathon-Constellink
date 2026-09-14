import asyncio

import pytest
from pydantic import BaseModel

from app.core.errors import LLMTimeoutError
from app.providers.llm.openai_compatible import OpenAICompatibleLLM


class SmallResult(BaseModel):
    value: str


def test_timeout_budget_includes_json_repair(monkeypatch):
    provider = OpenAICompatibleLLM(
        base_url="https://example.com/v1",
        api_key="test-key",
        model="test-model",
    )
    calls = 0

    async def fake_request(system_prompt, user_prompt, timeout_seconds, max_tokens):
        nonlocal calls
        calls += 1
        if calls == 1:
            return "{}"
        await asyncio.sleep(0.05)
        return '{"value":"ok"}'

    monkeypatch.setattr(provider, "_request", fake_request)

    with pytest.raises(LLMTimeoutError):
        asyncio.run(
            provider.generate_structured(
                task_name="test",
                system_prompt="system",
                user_prompt="user",
                response_model=SmallResult,
                timeout_seconds=0.01,
            )
        )

    assert calls == 2
