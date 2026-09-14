from fastapi import Request

from app.container import AppContainer
from app.services.analysis_orchestrator import AnalysisOrchestrator
from app.services.plan_service import PlanService
from app.services.quiz_service import QuizService
from app.services.space_service import SpaceService


def get_container(request: Request) -> AppContainer:
    return request.app.state.container


def get_space_service(request: Request) -> SpaceService:
    return get_container(request).space_service


def get_analysis_orchestrator(request: Request) -> AnalysisOrchestrator:
    return get_container(request).analysis_orchestrator


def get_plan_service(request: Request) -> PlanService:
    return get_container(request).plan_service


def get_quiz_service(request: Request) -> QuizService:
    return get_container(request).quiz_service

