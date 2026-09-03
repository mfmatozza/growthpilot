import pytest

from app.core.config import get_settings
from app.services.llm.base import LLMError
from app.services.llm.factory import get_default_llm_client
from app.services.llm.openai_client import OpenAIClient


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_defaults_to_openai(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("LLM_PROVIDER", raising=False)

    client = get_default_llm_client()

    assert isinstance(client, OpenAIClient)


def test_unknown_provider_raises_llm_error(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "not-a-real-provider")

    with pytest.raises(LLMError, match="Unknown LLM_PROVIDER"):
        get_default_llm_client()
