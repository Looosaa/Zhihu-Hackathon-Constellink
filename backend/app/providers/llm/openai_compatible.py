import asyncio
import logging
import time
from typing import TypeVar

import httpx
from pydantic import BaseModel

from app.core.errors import LLMInvalidOutputError, LLMProviderError, LLMTimeoutError
from app.providers.llm.json_parser import parse_structured_output

ModelT = TypeVar("ModelT", bound=BaseModel)
logger = logging.getLogger("zhijing.llm")


class OpenAICompatibleLLM:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 45,
        json_mode: bool = False,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._model_name = model
        self.timeout_seconds = timeout_seconds
        self.json_mode = json_mode

    @property
    def model_name(self) -> str:
        return self._model_name

    async def generate_structured(
        self,
        *,
        task_name: str,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ModelT],
        timeout_seconds: float | None = None,
        max_tokens: int | None = None,
    ) -> ModelT:
        started = time.perf_counter()
        request_timeout = timeout_seconds or self.timeout_seconds
        output_token_limit = max_tokens or 4096
        try:
            # One deadline covers both the initial completion and an optional
            # JSON-repair completion, rather than allowing the budget twice.
            async with asyncio.timeout(request_timeout):
                text = await self._request(
                    system_prompt,
                    user_prompt,
                    request_timeout,
                    output_token_limit,
                )
                try:
                    result = parse_structured_output(text, response_model)
                    retries = 0
                except LLMInvalidOutputError as first_error:
                    repair_prompt = (
                        "请修复下面的输出，使它严格符合给定 JSON Schema。"
                        "只返回 JSON，不要解释。\n\n"
                        f"Schema:\n{response_model.model_json_schema()}\n\n"
                        f"校验错误:\n{first_error.detail}\n\n"
                        f"原始输出:\n{text[:8000]}"
                    )
                    repaired = await self._request(
                        "你是 JSON 格式修复器。",
                        repair_prompt,
                        request_timeout,
                        output_token_limit,
                    )
                    result = parse_structured_output(repaired, response_model)
                    retries = 1
            logger.info(
                "llm_completed",
                extra={
                    "task_name": task_name,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                    "retry_count": retries,
                },
            )
            return result
        except (TimeoutError, httpx.TimeoutException) as exc:
            raise LLMTimeoutError(str(exc)) from exc
        except LLMInvalidOutputError:
            raise
        except httpx.HTTPError as exc:
            raise LLMProviderError(str(exc)) from exc

    async def _request(
        self,
        system_prompt: str,
        user_prompt: str,
        timeout_seconds: float,
        max_tokens: int,
    ) -> str:
        payload = {
            "model": self._model_name,
            "temperature": 0.2,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if self.json_mode:
            payload["response_format"] = {"type": "json_object"}
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions", json=payload, headers=headers
            )
        response.raise_for_status()
        body = response.json()
        try:
            return body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError("Missing assistant content in LLM response") from exc
