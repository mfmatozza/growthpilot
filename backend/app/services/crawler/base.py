from abc import ABC, abstractmethod
from dataclasses import dataclass


class FetchError(Exception):
    """Raised after retries are exhausted for a single URL. Callers (the
    crawl pipeline) should skip the page and continue, not abort the whole
    crawl — see app/services/crawler/site_crawler.py."""


@dataclass
class FetchedPage:
    url: str
    status_code: int
    html: str


class PageFetcher(ABC):
    """Interface so the crawl pipeline doesn't care whether pages come from
    httpx or a headless browser (see docs/DECISIONS.md #3)."""

    @abstractmethod
    def fetch(self, url: str) -> FetchedPage: ...
