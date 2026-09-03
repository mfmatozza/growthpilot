import httpx

from app.core.config import get_settings
from app.services.retry import external_api_retry
from app.services.serp.base import SerpError, SerpProvider

_RETRYABLE = (httpx.TransportError, httpx.TimeoutException)
_API_URL = "https://serpapi.com/search.json"


class SerpApiProvider(SerpProvider):
    def __init__(self, api_key: str | None = None) -> None:
        settings = get_settings()
        self._api_key = api_key or settings.serpapi_key
        if not self._api_key:
            raise SerpError("SERPAPI_KEY is not set.")

    @external_api_retry(_RETRYABLE)
    def top_results(self, query: str, num_results: int = 8) -> list[str]:
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    _API_URL,
                    params={"q": query, "engine": "google", "num": num_results, "api_key": self._api_key},
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise SerpError(f"SerpAPI request failed: {exc}") from exc

        body = response.json()
        if "error" in body:
            raise SerpError(f"SerpAPI error: {body['error']}")

        return [r["link"] for r in body.get("organic_results", []) if r.get("link")][:num_results]
