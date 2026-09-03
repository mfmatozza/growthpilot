from typing import Any

import anthropic

from app.core.config import get_settings
from app.services.llm.base import LLMClient, LLMError
from app.services.retry import external_api_retry

_RETRYABLE = (
    anthropic.APIConnectionError,
    anthropic.RateLimitError,
    anthropic.InternalServerError,
)

# A single forced tool call is how we get guaranteed-valid-JSON output from
# Claude without relying on the model to format free text correctly (brief:
# "use structured JSON outputs wherever the result feeds into the DB or UI").
_JSON_TOOL_NAME = "emit_result"


class AnthropicClient(LLMClient):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        settings = get_settings()
        self._api_key = api_key or settings.anthropic_api_key
        self._model = model or settings.claude_model
        if not self._api_key:
            # Fail loudly and early rather than at the first pipeline call —
            # this is a config problem, not a transient failure, so it is
            # intentionally NOT wrapped in retry logic.
            raise LLMError(
                "ANTHROPIC_API_KEY is not set. Add it to .env before running "
                "any pipeline that generates content."
            )
        self._client = anthropic.Anthropic(api_key=self._api_key)

    @external_api_retry(_RETRYABLE)
    def complete_json(self, *, system: str, user: str, max_tokens: int = 4096) -> dict[str, Any]:
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
                tools=[
                    {
                        "name": _JSON_TOOL_NAME,
                        "description": "Emit the final structured result.",
                        "input_schema": {"type": "object"},
                    }
                ],
                tool_choice={"type": "tool", "name": _JSON_TOOL_NAME},
            )
        except anthropic.APIStatusError as exc:
            raise LLMError(f"Anthropic API error: {exc}") from exc

        for block in response.content:
            if block.type == "tool_use" and block.name == _JSON_TOOL_NAME:
                return block.input  # already a dict — SDK parses tool_use JSON for us

        raise LLMError("Anthropic response did not include the expected tool_use block")

    @external_api_retry(_RETRYABLE)
    def complete_text(self, *, system: str, user: str, max_tokens: int = 4096) -> str:
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
        except anthropic.APIStatusError as exc:
            raise LLMError(f"Anthropic API error: {exc}") from exc

        text_blocks = [b.text for b in response.content if b.type == "text"]
        if not text_blocks:
            raise LLMError("Anthropic response contained no text content")
        return "\n".join(text_blocks)
