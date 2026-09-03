from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central config. All external-service credentials default to empty
    string so the app boots without them; each service module is
    responsible for raising a clear error if a call is attempted without
    the key it needs (see app/services/*)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    database_url: str = "postgresql+psycopg://growthpilot:growthpilot@localhost:5432/growthpilot"
    secret_key: str = "change-me-dev-only"

    # Single-operator login (docs/DECISIONS.md #16). Real server-side check,
    # not a client-side gate — every /api/* route except /health and
    # /api/auth/login requires the bearer token issued at login.
    admin_email: str = ""
    admin_password: str = ""

    # LLM. "openai" is the default provider (docs/DECISIONS.md #15); set
    # LLM_PROVIDER=anthropic to switch back, no code change needed.
    # openai_api_key is also reused as-is by Module 4's GEO tracker (querying
    # ChatGPT) once that's built — one key, two consumers.
    llm_provider: str = "openai"
    openai_api_key: str = ""
    # NOT gpt-5 — its hidden reasoning-token spend can consume the entire
    # max_completion_tokens budget before emitting any visible content on a
    # large structured-JSON prompt (confirmed: a 30-50 item keyword list
    # request returned empty). gpt-4o has no reasoning tax and is cheaper.
    # See docs/DECISIONS.md #15.
    openai_model: str = "gpt-4o"
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-5"

    # Keyword data
    dataforseo_login: str = ""
    dataforseo_password: str = ""

    # SERP research
    serpapi_key: str = ""

    # Images
    flux_api_key: str = ""
    openai_api_key_for_images: str = ""
    unsplash_access_key: str = ""

    # GEO tracker
    google_gemini_api_key: str = ""
    perplexity_api_key: str = ""

    # Reddit
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "growthpilot/0.1"

    # Single-site mode
    target_site_url: str = "https://example.com"

    # Comma-separated. Always includes the local Vite dev server; add the
    # deployed frontend's origin here in production (e.g. Railway's
    # generated domain) — see docs/DECISIONS.md #14.
    cors_allowed_origins: str = "http://localhost:3100"

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


def normalize_database_url(url: str) -> str:
    """Railway's Postgres plugin (and most hosted Postgres providers) inject
    DATABASE_URL as `postgres://` or `postgresql://`, not the
    `postgresql+psycopg://` scheme SQLAlchemy needs to pick psycopg3. Rewrite
    rather than requiring every deploy target to know our driver choice."""
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url
