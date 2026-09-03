from app.services.keyword_data.base import KeywordDataProvider, KeywordMetrics


class FakeKeywordDataProvider(KeywordDataProvider):
    """Test double. Returns deterministic metrics keyed off a lookup dict,
    falling back to (0, 0.0) for unknown keywords."""

    def __init__(self, metrics: dict[str, tuple[int, float]] | None = None) -> None:
        self._metrics = metrics or {}

    def get_metrics(self, keywords: list[str]) -> list[KeywordMetrics]:
        return [
            KeywordMetrics(
                keyword=kw,
                volume=self._metrics.get(kw, (0, 0.0))[0],
                difficulty=self._metrics.get(kw, (0, 0.0))[1],
            )
            for kw in keywords
        ]
