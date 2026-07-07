from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Anchored to this file's location (backend/app/core/config.py -> backend/.env)
# so .env loads correctly regardless of the process's working directory.
_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE, env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Ashford & Briggs API"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ashfordbriggs"

    # Auth
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # Anthropic — server-side proxy for AI blog generation
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Public site origin (no trailing slash) — used to build absolute URLs in
    # the generated sitemap. Change this when deploying under a different domain.
    site_url: str = "https://ashfordbriggs.com"

    # Rate limiting — in-memory (fine for the current single-worker deploy;
    # move to a shared store if this ever scales to multiple workers/instances)
    rate_limit_enabled: bool = True
    auth_rate_limit: str = "10/minute"
    demo_rate_limit: str = "5/hour"
    ai_rate_limit: str = "20/hour"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def async_database_url(self) -> str:
        """Normalize Railway's postgres:// URL to asyncpg. Cardinal fix."""
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url


settings = Settings()
