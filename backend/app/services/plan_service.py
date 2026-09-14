import json
from uuid import UUID

from app.core.config import Settings
from app.core.errors import AnalysisNotReadyError, SpaceNotFoundError
from app.domain.analysis_models import StudyPlan
from app.domain.ports import LearningRepositoryPort, LLMPort
from app.services.prompt_loader import PromptLoader


class PlanService:
    def __init__(
        self,
        *,
        repository: LearningRepositoryPort,
        llm: LLMPort,
        prompt_loader: PromptLoader,
        settings: Settings,
    ):
        self.repository = repository
        self.llm = llm
        self.prompt_loader = prompt_loader
        self.settings = settings

    async def generate(
        self, *, space_id: UUID, client_id: str, force: bool = False
    ) -> StudyPlan:
        space = await self.repository.get_owned_space(space_id, client_id)
        if space is None:
            raise SpaceNotFoundError()
        analysis = await self.repository.get_analysis(space_id)
        if analysis is None:
            raise AnalysisNotReadyError()
        existing = await self.repository.get_plan(space_id)
        if existing is not None and not force:
            return existing

        if self.settings.use_precomputed_demo and self._is_demo_topic(space.topic):
            path = self.settings.data_dir / "demo_plan.json"
            plan = StudyPlan.model_validate_json(path.read_text(encoding="utf-8"))
            plan.validate_context(
                daily_minutes=space.daily_minutes,
                valid_concept_ids={item.id for item in analysis.concepts},
                valid_source_keys={item.source_key for item in await self.repository.get_sources(space_id)},
            )
            return await self.repository.save_plan(space_id, plan)

        sources = await self.repository.get_sources(space_id)
        prompt = self.prompt_loader.render(
            "create_plan",
            user_profile_json=json.dumps(
                {
                    "topic": space.topic,
                    "level": space.level.value,
                    "goal": space.goal.value,
                    "daily_minutes": space.daily_minutes,
                },
                ensure_ascii=False,
            ),
            analysis_json=json.dumps(analysis.model_dump(mode="json"), ensure_ascii=False),
        )
        plan = await self.llm.generate_structured(
            task_name="create_plan",
            system_prompt="你是个性化学习规划师。",
            user_prompt=prompt,
            response_model=StudyPlan,
        )
        plan.validate_context(
            daily_minutes=space.daily_minutes,
            valid_concept_ids={item.id for item in analysis.concepts},
            valid_source_keys={item.source_key for item in sources},
        )
        return await self.repository.save_plan(space_id, plan)

    @staticmethod
    def _is_demo_topic(topic: str) -> bool:
        normalized = topic.replace(" ", "")
        return "机器学习" in normalized and "数学" in normalized
