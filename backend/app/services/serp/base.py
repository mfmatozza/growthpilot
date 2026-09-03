from abc import ABC, abstractmethod


class SerpError(Exception):
    """Raised on missing credentials or after retries are exhausted.
    Module 2's outline generation treats "no SERP provider" as a normal,
    expected state — it just generates the outline from the model's own
    knowledge plus the site profile instead. See docs/DECISIONS.md #25 for
    why there's no free scraper fallback despite the brief allowing one."""


class SerpProvider(ABC):
    @abstractmethod
    def top_results(self, query: str, num_results: int = 8) -> list[str]:
        """Returns ranking page URLs, best-ranked first."""
