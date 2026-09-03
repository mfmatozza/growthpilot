"""Minimal REST client for Google's Generative Language API — deliberately
not the google-generativeai SDK, to avoid a new heavy dependency for what
Module 4 needs: ask a plain-text question, get a plain-text answer."""

import httpx

from app.core.config import get_settings
from app.services.llm.base import LLMClient, LLMError
from app.services.retry import external_api_retry

_RETRYABLE = (httpx.TransportError, httpx.TimeoutException)


class GeminiClient(LLMClient):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        settings = get_settings()
        self._api_key = api_key or settings.google_gemini_api_key
        self._model = model or settings.gemini_model
        if not self._api_key:
            raise LLMError("GOOGLE_GEMINI_API_KEY is not set.")

    @external_api_retry(_RETRYABLE)
    def complete_text(self, *, system: str, user: str, max_tokens: int = 4096) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:generateContent"
        payload = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"maxOutputTokens": max_tokens},
        }
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, params={"key": self._api_key}, json=payload)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise LLMError(f"Gemini API error: {exc}") from exc

        body = response.json()
        try:
            return body["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            raise LLMError(f"Gemini response had no text content: {body}") from exc

    def complete_json(self, *, system: str, user: str, max_tokens: int = 4096) -> dict:
        # Not needed by Module 4 (plain-text Q&A only) — implement if a
        # future caller needs structured output from Gemini specifically.
        raise NotImplementedError("GeminiClient.complete_json is not implemented — see docstring")
