from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.dependencies import (
    get_analysis_orchestrator,
    get_plan_service,
    get_space_service,
)
from app.domain.entities import CreateSpaceCommand
from app.schemas.common import ResponseMeta
from app.schemas.spaces import (
    AnalysisResponse,
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


@router.post("/{space_id}/analyze", response_model=AnalysisResponse)
async def analyze_space(
    space_id: UUID,
    payload: AnalyzeSpaceRequest,
    request: Request,
    service: AnalysisOrchestrator = Depends(get_analysis_orchestrator),
) -> AnalysisResponse:
    bundle = await service.run(
        space_id=space_id, client_id=payload.client_id, force=payload.force
    )
    return AnalysisResponse(
        data={
            "space": bundle.space,
            "sources": bundle.sources,
            "analysis": bundle.analysis,
        },
        meta=_meta(request, bundle.execution_mode),
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

