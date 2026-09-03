from abc import ABC, abstractmethod
from dataclasses import dataclass


class RedditError(Exception):
    """Raised on missing credentials or after retries are exhausted.
    Callers should skip that subreddit/keyword pair and continue, not fail
    the whole monitoring run — see app/pipelines/reddit_monitor.py."""


@dataclass
class RedditThread:
    url: str
    subreddit: str
    title: str
    body: str


class RedditMonitorClient(ABC):
    """Interface so PRAW is never imported outside this package — keeps it
    mockable in tests without real Reddit credentials."""

    @abstractmethod
    def search(self, subreddit: str, query: str, limit: int = 5) -> list[RedditThread]: ...
