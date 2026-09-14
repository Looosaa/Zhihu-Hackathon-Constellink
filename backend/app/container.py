from dataclasses import dataclass

from app.core.config import Settings
from app.domain.ports import ContentProviderPort, LearningRepositoryPort, LLMPort
from app.providers.content.demo import DemoContentProvider
from app.providers.content.fallback import FallbackContentProvider
from app.providers.content.zhihu import ZhihuContentProvider
from app.providers.llm.fake import FakeLLM
from app.providers.llm.openai_compatible import OpenAICompatibleLLM
from app.repositories.memory_repository import MemoryLearningRepository
from app.repositories.supabase_repository import SupabaseLearningRepository
from app.services.analysis_orchestrator import AnalysisOrchestrator
from app.services.plan_service import PlanService
from app.services.prompt_loader import PromptLoader
from app.services.quiz_service import QuizService
from app.services.source_preprocessor import SourcePreprocessor
from app.services.space_service import SpaceService


@dataclass
class AppContainer:
    settings: Settings
    repository: LearningRepositoryPort
    content_provider: ContentProviderPort
    llm: LLMPort
    space_service: SpaceService
    analysis_orchestrator: AnalysisOrchestrator
    plan_service: PlanService
    quiz_service: QuizService


def build_container(settings: Settings) -> AppContainer:
    repository: LearningRepositoryPort
    if settings.repository_backend == "supabase":
        repository = SupabaseLearningRepository(
            settings.supabase_url, settings.supabase_service_role_key
        )
    else:
        repository = MemoryLearningRepository()

    demo_provider = DemoContentProvider(settings.data_dir / "demo_sources.json")
    content_provider: ContentProviderPort
    if settings.content_provider == "zhihu":
        content_provider = FallbackContentProvider(
            primary=ZhihuContentProvider(
                base_url=settings.zhihu_api_base_url,
                access_secret=settings.zhihu_access_secret,
            ),
            fallback=demo_provider,
        )
    else:
        content_provider = demo_provider

    llm: LLMPort
    if settings.llm_backend == "openai_compatible":
        llm = OpenAICompatibleLLM(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            timeout_seconds=settings.llm_timeout_seconds,
            json_mode=settings.llm_json_mode,
        )
    else:
        llm = FakeLLM()

    prompt_loader = PromptLoader(settings.prompts_dir, settings.prompt_version)
    preprocessor = SourcePreprocessor()

    return AppContainer(
        settings=settings,
        repository=repository,
        content_provider=content_provider,
        llm=llm,
        space_service=SpaceService(repository),
        analysis_orchestrator=AnalysisOrchestrator(
            repository=repository,
            content_provider=content_provider,
            llm=llm,
            preprocessor=preprocessor,
            prompt_loader=prompt_loader,
            settings=settings,
        ),
        plan_service=PlanService(
            repository=repository,
            llm=llm,
            prompt_loader=prompt_loader,
            settings=settings,
        ),
        quiz_service=QuizService(
            repository=repository,
            llm=llm,
            prompt_loader=prompt_loader,
        ),
    )

