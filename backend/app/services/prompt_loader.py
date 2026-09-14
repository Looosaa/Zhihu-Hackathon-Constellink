from functools import lru_cache
from pathlib import Path


class PromptLoader:
    def __init__(self, prompts_dir: Path, version: str = "v1"):
        self.prompts_dir = prompts_dir
        self.version = version

    @lru_cache(maxsize=16)
    def load(self, name: str) -> str:
        path = self.prompts_dir / f"{name}_{self.version}.txt"
        return path.read_text(encoding="utf-8")

    def render(self, name: str, **values: object) -> str:
        prompt = self.load(name)
        for key, value in values.items():
            prompt = prompt.replace(f"{{{{{key}}}}}", str(value))
        return prompt

