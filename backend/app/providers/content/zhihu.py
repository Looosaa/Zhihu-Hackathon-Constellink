import time
from typing import Any

import httpx
from pydantic import ValidationError

from app.core.errors import ContentProviderError
from app.domain.entities import RetrievedSource
from app.domain.enums import SourceProvider


class ZhihuContentProvider:
    def __init__(
        self,
        *,
        base_url: str,
        access_secret: str,
        timeout_seconds: float = 20,
    ):
        self.base_url = base_url.rstrip("/")
        self.access_secret = access_secret
        self.timeout_seconds = timeout_seconds

    async def search(self, query: str, limit: int) -> list[RetrievedSource]:
        headers = {
            "Authorization": f"Bearer {self.access_secret}",
            "X-Request-Timestamp": str(int(time.time())),
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(
                    f"{self.base_url}/content/zhihu_search",
                    params={"Query": query},
                    headers=headers,
                )
            response.raise_for_status()
            return self._normalize_payload(response.json(), limit)
        except (httpx.HTTPError, ValueError, ValidationError) as exc:
            raise ContentProviderError(str(exc)) from exc

    def _normalize_payload(self, payload: Any, limit: int) -> list[RetrievedSource]:
        """Normalize defensively; update mappings from an authorized response fixture."""
        candidates = self._find_items(payload)
        normalized: list[RetrievedSource] = []
        for index, item in enumerate(candidates[:limit], start=1):
            if not isinstance(item, dict):
                continue
            author = item.get("author") or item.get("creator") or {}
            if isinstance(author, str):
                author = {"name": author}
            external_id = str(
                item.get("id")
                or item.get("content_id")
                or item.get("object_id")
                or index
            )
            title = item.get("title") or item.get("question_title") or "知乎内容"
            excerpt = (
                item.get("excerpt")
                or item.get("content")
                or item.get("description")
                or item.get("summary")
                or ""
            )
            url = item.get("url") or item.get("source_url") or item.get("link")
            if not url or not excerpt:
                continue
            normalized.append(
                RetrievedSource(
                    external_id=external_id,
                    provider=SourceProvider.ZHIHU,
                    content_type=str(item.get("type") or "answer"),
                    title=str(title),
                    author_name=str(author.get("name") or author.get("headline") or "知乎用户"),
                    author_badge=author.get("badge") or author.get("headline"),
                    source_url=url,
                    excerpt=str(excerpt),
                    engagement={
                        "upvotes": item.get("voteup_count") or item.get("upvotes") or 0,
                        "comments": item.get("comment_count") or item.get("comments") or 0,
                    },
                    metadata={"raw_type": item.get("type")},
                )
            )
        return normalized

    @staticmethod
    def _find_items(payload: Any) -> list:
        if isinstance(payload, list):
            return payload
        if not isinstance(payload, dict):
            return []
        for key in ("data", "results", "items", "list"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
            if isinstance(value, dict):
                nested = ZhihuContentProvider._find_items(value)
                if nested:
                    return nested
        return []

