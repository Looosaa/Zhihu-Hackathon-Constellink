import logging

from app.core.errors import AppError, ContentProviderError
from app.domain.entities import RetrievedSource
from app.domain.ports import ContentProviderPort

logger = logging.getLogger("zhijing.content")


class FallbackContentProvider:
    def __init__(
        self,
        *,
        primary: ContentProviderPort,
        fallback: ContentProviderPort,
        minimum_sources: int = 3,
    ):
        self.primary = primary
        self.fallback = fallback
        self.minimum_sources = minimum_sources

    async def search(self, query: str, limit: int) -> list[RetrievedSource]:
        try:
            items = await self.primary.search(query, limit)
            if len(items) >= self.minimum_sources:
                return items
            logger.warning("primary_content_insufficient")
        except (AppError, OSError, ValueError) as exc:
            logger.warning("primary_content_failed", exc_info=exc)
        try:
            return await self.fallback.search(query, limit)
        except Exception as exc:
            raise ContentProviderError(str(exc)) from exc

