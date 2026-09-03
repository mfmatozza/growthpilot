import httpx

from app.services.crawler.base import FetchedPage, FetchError, PageFetcher
from app.services.retry import external_api_retry

_RETRYABLE = (httpx.TransportError, httpx.TimeoutException)

_USER_AGENT = "GrowthPilotBot/0.1 (+https://github.com/; self-hosted SEO tool)"


class HttpxFetcher(PageFetcher):
    def __init__(self, timeout: float = 15.0) -> None:
        self._timeout = timeout

    @external_api_retry(_RETRYABLE)
    def fetch(self, url: str) -> FetchedPage:
        try:
            with httpx.Client(
                timeout=self._timeout,
                follow_redirects=True,
                headers={"User-Agent": _USER_AGENT},
            ) as client:
                response = client.get(url)
        except httpx.HTTPError as exc:
            raise FetchError(f"Failed to fetch {url}: {exc}") from exc

        return FetchedPage(url=str(response.url), status_code=response.status_code, html=response.text)
