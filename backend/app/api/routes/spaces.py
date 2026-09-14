from uuid import UUID

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request, status

from app.api.dependencies import (
    get_analysis_orchestrator,
    get_plan_service,
    get_space_service,
)
from app.domain.entities import CreateSpaceCommand
from app.schemas.common import ResponseMeta
from app.schemas.spaces import (
    AnalysisAcceptedResponse,
    AnalyzeSpaceRequest,
    CompleteSpaceResponse,
    CreateSpaceRequest,
    GeneratePlanRequest,
    PlanResponse,
    SpaceResponse,
)
from app.services.analysis_orchestrator import AnalysisOrchestrator
from app.services.plan_service import PlanService
from app.services.space_service import SpaceService

router = APIRouter(prefix="/api/spaces", tags=["spaces"])
logger = logging.getLogger("zhijing.analysis.background")


def _meta(request: Request, execution_mode=None) -> ResponseMeta:
    settings = request.app.state.container.settings
    return ResponseMeta(
        request_id=request.state.request_id,
        execution_mode=execution_mode,
        prompt_version=settings.prompt_version,
    )


@router.post("", response_model=SpaceResponse, status_code=status.HTTP_201_CREATED)
async def create_space(
    payload: CreateSpaceRequest,
    request: Request,
    service: SpaceService = Depends(get_space_service),
) -> SpaceResponse:
    space = await service.create(CreateSpaceCommand(**payload.model_dump()))
    return SpaceResponse(data=space, meta=_meta(request))


@router.get("/{space_id}", response_model=CompleteSpaceResponse)
async def get_space(
    space_id: UUID,
    request: Request,
    client_id: str = Query(min_length=16, max_length=128),
    service: SpaceService = Depends(get_space_service),
) -> CompleteSpaceResponse:
    result = await service.get_complete(space_id, client_id)
    return CompleteSpaceResponse(data=result, meta=_meta(request))


async def _run_analysis_background(
    *,
    service: AnalysisOrchestrator,
    space_id: UUID,
    client_id: str,
    force: bool,
) -> None:
    try:
        await service.run(space_id=space_id, client_id=client_id, force=force)
    except Exception:
        # The orchestrator has already persisted the safe failure state. Logging
        # here keeps the background exception visible without breaking the 202.
        logger.exception("background_analysis_failed", extra={"space_id": str(space_id)})


@router.post(
    "/{space_id}/analyze",
    response_model=AnalysisAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def analyze_space(
    space_id: UUID,
    payload: AnalyzeSpaceRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    service: AnalysisOrchestrator = Depends(get_analysis_orchestrator),
) -> AnalysisAcceptedResponse:
    background_tasks.add_task(
        _run_analysis_background,
        service=service,
        space_id=space_id,
        client_id=payload.client_id,
        force=payload.force,
    )
    return AnalysisAcceptedResponse(
        data={"space_id": space_id, "status": "accepted"},
        meta=_meta(request),
    )


@router.post("/{space_id}/plan", response_model=PlanResponse)
async def generate_plan(
    space_id: UUID,
    payload: GeneratePlanRequest,
    request: Request,
    service: PlanService = Depends(get_plan_service),
) -> PlanResponse:
    plan = await service.generate(
        space_id=space_id, client_id=payload.client_id, force=payload.force
    )
    return PlanResponse(data=plan, meta=_meta(request))
