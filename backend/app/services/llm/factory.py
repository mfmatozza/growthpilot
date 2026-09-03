from app.core.config import get_settings
from app.services.llm.base import LLMClient, LLMError


def get_default_llm_client() -> LLMClient:
    """Single place pipelines/routes go for "the" LLM client, so switching
    providers is a config change (LLM_PROVIDER) not a code change across
    every call site. See docs/DECISIONS.md #15."""
    provider = get_settings().llm_provider
    if provider == "openai":
        from app.services.llm.openai_client import OpenAIClient

        return OpenAIClient()
    if provider == "anthropic":
        from app.services.llm.anthropic_client import AnthropicClient

        return AnthropicClient()
    raise LLMError(f"Unknown LLM_PROVIDER: {provider!r} (expected 'openai' or 'anthropic')")
