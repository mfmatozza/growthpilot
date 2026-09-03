from abc import ABC, abstractmethod
from dataclasses import dataclass


class KeywordDataError(Exception):
    """Raised after retries are exhausted or on a non-retryable failure
    (bad credentials, malformed request). Callers should leave volume/
    difficulty as null on a given keyword rather than fail the whole batch."""


@dataclass
class KeywordMetrics:
    keyword: str
    volume: int | None
    difficulty: float | None  # 0-100, provider-normalized


class KeywordDataProvider(ABC):
    """Interface so DataForSEO can be swapped (or mocked in tests) without
    touching the scoring/pipeline code."""

    @abstractmethod
    def get_metrics(self, keywords: list[str]) -> list[KeywordMetrics]: ...
