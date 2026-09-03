"""Perplexity's API is OpenAI-compatible (same chat.completions shape), so
this reuses the openai SDK pointed at Perplexity's base URL instead of
writing a second HTTP client from scratch."""

import openai

from app.core.config import get_settings
from app.services.llm.base import LLMClient, LLMError
from app.services.retry import external_api_retry

_RETRYABLE = (
    openai.APIConnectionError,
    openai.RateLimitError,
    openai.InternalServerError,
)


class PerplexityClient(LLMClient):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        settings = get_settings()
        self._api_key = api_key or settings.perplexity_api_key
        self._model = model or settings.perplexity_model
        if not self._api_key:
            raise LLMError("PERPLEXITY_API_KEY is not set.")
        self._client = openai.OpenAI(api_key=self._api_key, base_url="https://api.perplexity.ai")

    @external_api_retry(_RETRYABLE)
    def complete_text(self, *, system: str, user: str, max_tokens: int = 4096) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
        except openai.APIStatusError as exc:
            raise LLMError(f"Perplexity API error: {exc}") from exc

        content = response.choices[0].message.content
        if not content:
            raise LLMError("Perplexity response contained no content")
        return content

    def complete_json(self, *, system: str, user: str, max_tokens: int = 4096) -> dict:
        raise NotImplementedError("PerplexityClient.complete_json is not implemented — see docstring")
