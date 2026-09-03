from app.services.reddit.base import RedditMonitorClient, RedditThread


class FakeRedditClient(RedditMonitorClient):
    """Test double. `results_by_query` maps a search query string to the
    threads that "search" should return for it, regardless of subreddit."""

    def __init__(self, results_by_query: dict[str, list[RedditThread]] | None = None) -> None:
        self._results_by_query = results_by_query or {}
        self.calls: list[tuple[str, str]] = []

    def search(self, subreddit: str, query: str, limit: int = 5) -> list[RedditThread]:
        self.calls.append((subreddit, query))
        return self._results_by_query.get(query, [])[:limit]
