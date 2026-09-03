from typing import Any

from app.services.llm.base import LLMClient


class FakeLLMClient(LLMClient):
    """Test double. Construct with canned responses so pipeline tests never
    hit the network or need an API key."""

    def __init__(self, json_response: dict[str, Any] | None = None, text_response: str = "") -> None:
        self.json_response = json_response or {}
        self.text_response = text_response
        self.calls: list[dict[str, Any]] = []

    def complete_json(self, *, system: str, user: str, max_tokens: int = 4096) -> dict[str, Any]:
        self.calls.append({"kind": "json", "system": system, "user": user})
        return self.json_response

    def complete_text(self, *, system: str, user: str, max_tokens: int = 4096) -> str:
        self.calls.append({"kind": "text", "system": system, "user": user})
        return self.text_response
