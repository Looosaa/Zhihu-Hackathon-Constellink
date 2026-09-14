import json
from pathlib import Path

from app.core.errors import ContentProviderError
from app.domain.entities import RetrievedSource


class DemoContentProvider:
    def __init__(self, file_path: Path):
        self.file_path = file_path

    async def search(self, query: str, limit: int) -> list[RetrievedSource]:
        try:
            payload = json.loads(self.file_path.read_text(encoding="utf-8"))
            return [
                RetrievedSource.model_validate(item)
                for item in payload.get("sources", [])[:limit]
            ]
        except (OSError, ValueError) as exc:
            raise ContentProviderError(str(exc)) from exc

