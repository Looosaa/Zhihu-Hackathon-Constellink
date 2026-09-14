from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(request: Request) -> dict:
    settings = request.app.state.container.settings
    return {
        "status": "ok",
        "content_provider": settings.content_provider,
        "repository": settings.repository_backend,
        "llm": settings.llm_backend,
    }

