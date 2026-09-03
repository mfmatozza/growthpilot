from app.services.serp.base import SerpProvider


class FakeSerpProvider(SerpProvider):
    def __init__(self, results: list[str] | None = None) -> None:
        self._results = results or []

    def top_results(self, query: str, num_results: int = 8) -> list[str]:
        return self._results[:num_results]
