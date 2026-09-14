from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from app.api.dependencies import get_quiz_service
from app.schemas.common import ResponseMeta
from app.schemas.quizzes import (
    CreateQuizRequest,
    GradeResponse,
    QuizResponse,
    SubmitAttemptRequest,
)
from app.services.quiz_service import QuizService

router = APIRouter(tags=["quizzes"])


def _meta(request: Request) -> ResponseMeta:
    settings = request.app.state.container.settings
    return ResponseMeta(
        request_id=request.state.request_id,
        prompt_version=settings.prompt_version,
    )


@router.post(
    "/api/spaces/{space_id}/quizzes",
    response_model=QuizResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_quiz(
    space_id: UUID,
    payload: CreateQuizRequest,
    request: Request,
    service: QuizService = Depends(get_quiz_service),
) -> QuizResponse:
    quiz = await service.create(
        space_id=space_id,
        client_id=payload.client_id,
        concept_id=payload.concept_id,
    )
    return QuizResponse(data=quiz, meta=_meta(request))


@router.post("/api/quizzes/{quiz_id}/attempts", response_model=GradeResponse)
async def submit_attempt(
    quiz_id: UUID,
    payload: SubmitAttemptRequest,
    request: Request,
    service: QuizService = Depends(get_quiz_service),
) -> GradeResponse:
    result = await service.grade(
        quiz_id=quiz_id, client_id=payload.client_id, answer=payload.answer
    )
    return GradeResponse(data=result, meta=_meta(request))

