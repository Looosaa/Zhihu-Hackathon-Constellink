import html
import re

from app.domain.entities import PreparedSource, RetrievedSource
from app.domain.enums import SourceProvider

_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")


class SourcePreprocessor:
    def prepare(
        self,
        sources: list[RetrievedSource],
        *,
        max_items: int,
        max_chars: int,
    ) -> list[PreparedSource]:
        unique: dict[str, RetrievedSource] = {}
        for source in sources:
            dedupe_key = f"{source.provider}:{source.external_id}"
            if dedupe_key in unique:
                continue
            excerpt = self._clean_text(source.excerpt)
            title = self._clean_text(source.title)
            author = self._clean_text(source.author_name)
            if not excerpt or len(excerpt) < 40 or not title or not author:
                continue
            unique[dedupe_key] = source.model_copy(
                update={
                    "excerpt": excerpt[:max_chars],
                    "title": title,
                    "author_name": author,
                }
            )

        candidates = list(unique.values())
        if candidates and all(item.provider == SourceProvider.DEMO for item in candidates):
            ranked = candidates[:max_items]
        else:
            ranked = sorted(candidates, key=self._score, reverse=True)[:max_items]
        return [
            PreparedSource(**source.model_dump(), source_key=f"S{index}")
            for index, source in enumerate(ranked, start=1)
        ]

    @staticmethod
    def _clean_text(value: str) -> str:
        without_tags = _TAG_RE.sub(" ", html.unescape(value or ""))
        return _SPACE_RE.sub(" ", without_tags).strip()

    @staticmethod
    def _score(source: RetrievedSource) -> float:
        engagement = source.engagement
        upvotes = int(engagement.get("upvotes") or engagement.get("voteup_count") or 0)
        comments = int(engagement.get("comments") or engagement.get("comment_count") or 0)
        badge_bonus = 5 if source.author_badge else 0
        length_bonus = min(len(source.excerpt) / 200, 6)
        return upvotes * 0.02 + comments * 0.01 + badge_bonus + length_bonus
