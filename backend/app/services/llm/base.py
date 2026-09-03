from abc import ABC, abstractmethod
from typing import Any


class LLMError(Exception):
    """Raised after retries are exhausted, or on a non-retryable failure
    (e.g. auth). Callers should catch this and degrade gracefully rather
    than letting a pipeline run crash outright."""


class LLMClient(ABC):
    """Interface every pipeline codes against, never the Anthropic SDK
    directly. Keeps provider swaps and test-mocking cheap."""

    @abstractmethod
    def complete_json(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """Return a parsed JSON object. Implementations must guarantee the
        return value is valid JSON or raise LLMError — never return a raw
        string for callers to parse themselves."""

    @abstractmethod
    def complete_text(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int = 4096,
    ) -> str:
        """Return raw text (used for prose generation, e.g. article
        sections, where forcing JSON would hurt output quality)."""
