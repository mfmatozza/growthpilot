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

    # LLM
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
    openai_api_key: str = ""
    google_gemini_api_key: str = ""
    perplexity_api_key: str = ""

    # Reddit
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "growthpilot/0.1"

    # Single-site mode
    target_site_url: str = "https://example.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()
