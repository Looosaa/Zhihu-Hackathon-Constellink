import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.quizzes import router as quizzes_router
from app.api.routes.spaces import router as spaces_router
from app.container import build_container
from app.core.config import Settings, get_settings
from app.core.error_handlers import register_error_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.api.routes.auth import router as auth_router
from app.services.oauth_service import OAuthService


class OAuthAccessLogFilter(logging.Filter):
    def filter(self, record):
        if isinstance(record.args, tuple):
            record.args = tuple(
                value.split("?", 1)[0] + "?[redacted]"
                if isinstance(value, str) and "/api/auth/zhihu/callback?" in value else value
                for value in record.args
            )
        return True


def create_app(settings: Settings | None = None) -> FastAPI:
    configure_logging()
    access_logger = logging.getLogger("uvicorn.access")
    if not any(isinstance(f, OAuthAccessLogFilter) for f in access_logger.filters):
        access_logger.addFilter(OAuthAccessLogFilter())
    resolved = settings or get_settings()
    app = FastAPI(
        title=resolved.app_name,
        version="0.1.0",
        description="知径：基于多观点内容的 AI 学习教练后端",
    )
    app.state.container = build_container(resolved)
    app.state.oauth = OAuthService(resolved)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            resolved.frontend_origin,
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
            "http://localhost:5175",
            "http://127.0.0.1:5175",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(spaces_router)
    app.include_router(quizzes_router)
    return app


app = create_app()
