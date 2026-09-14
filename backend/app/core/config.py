from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "Zhijing API"
    frontend_origin: str = "http://localhost:5173"
    render_external_url: str = ""

    repository_backend: str = "memory"
    supabase_url: str = ""
    supabase_service_role_key: str = ""

    llm_backend: str = "fake"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = "fake-zhijing-v1"
    llm_timeout_seconds: float = Field(default=45, ge=5, le=180)
    llm_json_mode: bool = False

    content_provider: str = "demo"
    zhihu_access_secret: str = ""
    zhihu_api_base_url: str = "https://developer.zhihu.com/api/v1"
    zhihu_oauth_app_id: str = "618"
    zhihu_oauth_app_key: str = ""
    zhihu_oauth_redirect_uri: str = ""
    zhihu_oauth_allow_missing_state: bool = False
    oauth_cookie_secure: bool = True

    max_sources: int = Field(default=12, ge=3, le=20)
    max_source_chars: int = Field(default=1200, ge=300, le=5000)
    extract_concurrency: int = Field(default=4, ge=1, le=8)
    use_precomputed_demo: bool = False
    prompt_version: str = "v1"

    data_dir: Path = BACKEND_DIR / "data"
    prompts_dir: Path = BACKEND_DIR / "app" / "prompts"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_selected_backends(self) -> "Settings":
        # Render assigns the public URL only after the service is created. Derive
        # the same-origin frontend and OAuth callback there so no deploy-time URL
        # needs to be hard-coded into the repository.
        if self.app_env == "production" and self.render_external_url:
            render_url = self.render_external_url.rstrip("/")
            parsed = urlsplit(render_url)
            if parsed.scheme != "https" or not parsed.hostname or parsed.username:
                raise ValueError("RENDER_EXTERNAL_URL must be a public HTTPS URL")
            if self.frontend_origin in {"", "http://localhost:5173", "http://127.0.0.1:5173"}:
                self.frontend_origin = render_url
            if not self.zhihu_oauth_redirect_uri:
                self.zhihu_oauth_redirect_uri = f"{render_url}/auth/callback"
        if self.repository_backend not in {"memory", "supabase"}:
            raise ValueError("REPOSITORY_BACKEND must be memory or supabase")
        if self.llm_backend not in {"fake", "openai_compatible"}:
            raise ValueError("LLM_BACKEND must be fake or openai_compatible")
        if self.content_provider not in {"demo", "zhihu"}:
            raise ValueError("CONTENT_PROVIDER must be demo or zhihu")
        if self.repository_backend == "supabase" and not (
            self.supabase_url and self.supabase_service_role_key
        ):
            raise ValueError("Supabase URL and service role key are required")
        if self.llm_backend == "openai_compatible" and not (
            self.llm_base_url and self.llm_api_key and self.llm_model
        ):
            raise ValueError("LLM base URL, API key, and model are required")
        if self.content_provider == "zhihu" and not self.zhihu_access_secret:
            raise ValueError("ZHIHU_ACCESS_SECRET is required for Zhihu provider")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
