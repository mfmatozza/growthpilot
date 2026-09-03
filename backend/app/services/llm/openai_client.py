import json
from typing import Any

import openai

from app.core.config import get_settings
from app.services.llm.base import LLMClient, LLMError
from app.services.retry import external_api_retry

_RETRYABLE = (
    openai.APIConnectionError,
    openai.RateLimitError,
    openai.InternalServerError,
)


class OpenAIClient(LLMClient):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        settings = get_settings()
        self._api_key = api_key or settings.openai_api_key
        self._model = model or settings.openai_model
        if not self._api_key:
            raise LLMError(
                "OPENAI_API_KEY is not set. Add it to .env before running "
                "any pipeline that generates content."
            )
        self._client = openai.OpenAI(api_key=self._api_key)

    @external_api_retry(_RETRYABLE)
    def complete_json(self, *, system: str, user: str, max_tokens: int = 4096) -> dict[str, Any]:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                max_completion_tokens=max_tokens,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
        except openai.APIStatusError as exc:
            raise LLMError(f"OpenAI API error: {exc}") from exc

        content = response.choices[0].message.content
        if not content:
            raise LLMError("OpenAI response contained no content")
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise LLMError(f"OpenAI response was not valid JSON: {exc}") from exc

    @external_api_retry(_RETRYABLE)
    def complete_text(self, *, system: str, user: str, max_tokens: int = 4096) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                max_completion_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
        except openai.APIStatusError as exc:
            raise LLMError(f"OpenAI API error: {exc}") from exc

        content = response.choices[0].message.content
        if not content:
            raise LLMError("OpenAI response contained no content")
        return content
