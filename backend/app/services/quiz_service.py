import json
from uuid import UUID

from app.core.errors import AnalysisNotReadyError, QuizNotFoundError, SpaceNotFoundError
from app.domain.analysis_models import GradeResult, QuizDraft
from app.domain.ports import LearningRepositoryPort, LLMPort
from app.services.prompt_loader import PromptLoader


class QuizService:
    def __init__(
        self,
        *,
        repository: LearningRepositoryPort,
        llm: LLMPort,
        prompt_loader: PromptLoader,
    ):
        self.repository = repository
        self.llm = llm
        self.prompt_loader = prompt_loader

    async def create(
        self, *, space_id: UUID, client_id: str, concept_id: str | None
    ) -> dict:
        space = await self.repository.get_owned_space(space_id, client_id)
        if space is None:
            raise SpaceNotFoundError()
        analysis = await self.repository.get_analysis(space_id)
        if analysis is None:
            raise AnalysisNotReadyError()

        valid_concepts = {item.id for item in analysis.concepts}
        selected = concept_id if concept_id in valid_concepts else None
        sources = await self.repository.get_sources(space_id)
        prompt = self.prompt_loader.render(
            "create_quiz",
            topic=space.topic,
            concept_id=selected or "请自动选择核心概念",
            analysis_json=json.dumps(analysis.model_dump(mode="json"), ensure_ascii=False),
        )
        quiz = await self.llm.generate_structured(
            task_name="create_quiz",
            system_prompt="你是负责检验真实理解的学习教练。",
            user_prompt=prompt,
            response_model=QuizDraft,
        )
        unknown_sources = set(quiz.source_keys) - {item.source_key for item in sources}
        if unknown_sources:
            raise ValueError(f"Quiz references unknown sources: {unknown_sources}")
        if quiz.concept_id and quiz.concept_id not in valid_concepts:
            raise ValueError("Quiz references unknown concept")
        return await self.repository.save_quiz(space_id, quiz)

    async def grade(
        self, *, quiz_id: UUID, client_id: str, answer: str
    ) -> dict:
        quiz = await self.repository.get_quiz(quiz_id)
        if quiz is None:
            raise QuizNotFoundError()
        space = await self.repository.get_owned_space(
            UUID(str(quiz["learning_space_id"])), client_id
        )
        if space is None:
            raise QuizNotFoundError()

        prompt = self.prompt_loader.render(
            "grade_quiz",
            question=quiz["question"],
            rubric_json=json.dumps(quiz["rubric"], ensure_ascii=False),
            reference_answer=quiz["reference_answer"],
            user_answer=answer,
        )
        grade = await self.llm.generate_structured(
            task_name="grade_quiz",
            system_prompt="你是耐心但严格的学习教练。",
            user_prompt=prompt,
            response_model=GradeResult,
        )
        return await self.repository.save_attempt(quiz_id, client_id, answer, grade)

