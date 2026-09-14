import json
from pathlib import Path
from uuid import UUID

from app.core.config import Settings
from app.core.errors import (
    AnalysisInProgressError,
    ContentUnavailableError,
    SpaceNotFoundError,
    safe_message_for,
)
from app.domain.analysis_models import (
    AnalysisBundle,
    AnalysisResult,
    SourceViewpoint,
)
from app.domain.enums import ExecutionMode, SourceProvider, SpaceStatus
from app.domain.ports import ContentProviderPort, LearningRepositoryPort, LLMPort
from app.services.prompt_loader import PromptLoader
from app.services.source_preprocessor import SourcePreprocessor


class AnalysisOrchestrator:
    def __init__(
        self,
        *,
        repository: LearningRepositoryPort,
        content_provider: ContentProviderPort,
        llm: LLMPort,
        preprocessor: SourcePreprocessor,
        prompt_loader: PromptLoader,
        settings: Settings,
    ):
        self.repository = repository
        self.content_provider = content_provider
        self.llm = llm
        self.preprocessor = preprocessor
        self.prompt_loader = prompt_loader
        self.settings = settings

    async def run(
        self,
        *,
        space_id: UUID,
        client_id: str,
        force: bool = False,
    ) -> AnalysisBundle:
        space = await self.repository.get_owned_space(space_id, client_id)
        if space is None:
            raise SpaceNotFoundError()

        if space.status == SpaceStatus.READY and not force:
            analysis = await self.repository.get_analysis(space_id)
            sources = await self.repository.get_sources(space_id)
            if analysis is not None:
                return AnalysisBundle(
                    space=space,
                    sources=sources,
                    analysis=analysis,
                    execution_mode=self._execution_mode(sources),
                )

        acquired = await self.repository.try_mark_analyzing(
            space_id, allow_ready=force
        )
        if not acquired:
            raise AnalysisInProgressError()

        try:
            raw_sources = await self.content_provider.search(
                space.topic, self.settings.max_sources
            )
            sources = self.preprocessor.prepare(
                raw_sources,
                max_items=self.settings.max_sources,
                # Keep real-time analysis responsive even when an older cloud
                # environment still has the previous 1200-character setting.
                max_chars=min(self.settings.max_source_chars, 800),
            )
            if len(sources) < 3:
                raise ContentUnavailableError()

            await self.repository.replace_sources(space.id, sources)

            if self.settings.use_precomputed_demo and self._is_demo_topic(space.topic):
                analysis = self._load_precomputed_analysis()
                viewpoints: list[SourceViewpoint] = []
                mode = ExecutionMode.PRECOMPUTED
            else:
                # A single structured request keeps live analysis fast enough for
                # interactive use. The previous extract-then-synthesize pipeline
                # generated two large JSON responses and frequently exceeded the
                # provider timeout even after the HTTP request moved off-thread.
                analysis = await self._analyze_sources(space, sources)
                viewpoints = []
                mode = self._execution_mode(sources)

            analysis.validate_references({item.source_key for item in sources})
            await self.repository.save_analysis(
                space.id,
                analysis,
                viewpoints,
                model_name=self.llm.model_name,
                prompt_version=self.settings.prompt_version,
            )
            await self.repository.mark_ready(space.id)
            refreshed = await self.repository.get_owned_space(space.id, client_id)
            return AnalysisBundle(
                space=refreshed or space.model_copy(update={"status": SpaceStatus.READY}),
                sources=sources,
                analysis=analysis,
                execution_mode=mode,
            )
        except Exception as exc:
            if space.status == SpaceStatus.READY:
                await self.repository.mark_ready(space.id)
            else:
                await self.repository.mark_failed(space.id, safe_message_for(exc))
            raise

    async def _analyze_sources(self, space, sources) -> AnalysisResult:
        sources_json = json.dumps(
            [
                {
                    "source_key": source.source_key,
                    "title": source.title,
                    "author_name": source.author_name,
                    "excerpt": source.excerpt,
                }
                for source in sources
            ],
            ensure_ascii=False,
        )
        prompt = self.prompt_loader.render(
            "analyze_sources",
            topic=space.topic,
            level=space.level.value,
            goal=space.goal.value,
            daily_minutes=space.daily_minutes,
            sources_json=sources_json,
        )
        return await self.llm.generate_structured(
            task_name="analyze_sources",
            system_prompt="你是严谨、简洁的 AI 学习教练。",
            user_prompt=prompt,
            response_model=AnalysisResult,
            timeout_seconds=self.settings.analysis_timeout_seconds,
            max_tokens=3072,
        )

    def _load_precomputed_analysis(self) -> AnalysisResult:
        path = self.settings.data_dir / "demo_analysis.json"
        return AnalysisResult.model_validate_json(path.read_text(encoding="utf-8"))

    @staticmethod
    def _is_demo_topic(topic: str) -> bool:
        normalized = topic.replace(" ", "")
        return "机器学习" in normalized and "数学" in normalized

    @staticmethod
    def _execution_mode(sources) -> ExecutionMode:
        if sources and all(item.provider == SourceProvider.ZHIHU for item in sources):
            return ExecutionMode.LIVE
        return ExecutionMode.DEMO
