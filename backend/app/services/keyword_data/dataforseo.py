"""DataForSEO client — pay-per-call "live" endpoints, no subscription
(docs/DECISIONS.md #10). Two calls per batch:

  * /v3/keywords_data/google_ads/search_volume/live  -> monthly search volume
  * /v3/dataforseo_labs/google/bulk_keyword_difficulty/live -> 0-100 difficulty

Both are billed per request regardless of batch size, so keywords are sent
in one batch per call rather than one call per keyword.
"""

import httpx

from app.core.config import get_settings
from app.services.keyword_data.base import KeywordDataError, KeywordDataProvider, KeywordMetrics
from app.services.retry import external_api_retry

_BASE_URL = "https://api.dataforseo.com"
_RETRYABLE = (httpx.TransportError, httpx.TimeoutException)

# DataForSEO location/language codes for search volume. Hardcoded to US/English
# for now — expose as config if/when non-US targeting is needed.
_LOCATION_CODE = 2840
_LANGUAGE_CODE = "en"


class DataForSEOProvider(KeywordDataProvider):
    def __init__(self, login: str | None = None, password: str | None = None) -> None:
        settings = get_settings()
        self._login = login or settings.dataforseo_login
        self._password = password or settings.dataforseo_password
        if not self._login or not self._password:
            raise KeywordDataError(
                "DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD are not set. Add them to .env "
                "before running keyword enrichment."
            )

    def get_metrics(self, keywords: list[str]) -> list[KeywordMetrics]:
        volumes = self._fetch_search_volume(keywords)
        difficulties = self._fetch_difficulty(keywords)
        return [
            KeywordMetrics(keyword=kw, volume=volumes.get(kw), difficulty=difficulties.get(kw))
            for kw in keywords
        ]

    @external_api_retry(_RETRYABLE)
    def _post(self, path: str, payload: list[dict]) -> dict:
        try:
            with httpx.Client(auth=(self._login, self._password), timeout=30.0) as client:
                response = client.post(f"{_BASE_URL}{path}", json=payload)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise KeywordDataError(f"DataForSEO request to {path} failed: {exc}") from exc
        except httpx.HTTPError as exc:
            # transport-level: let @external_api_retry catch and retry this
            raise exc

        body = response.json()
        if body.get("status_code") != 20000:
            raise KeywordDataError(f"DataForSEO error on {path}: {body.get('status_message')}")
        return body

    def _fetch_search_volume(self, keywords: list[str]) -> dict[str, int]:
        body = self._post(
            "/v3/keywords_data/google_ads/search_volume/live",
            [{"keywords": keywords, "location_code": _LOCATION_CODE, "language_code": _LANGUAGE_CODE}],
        )
        result: dict[str, int] = {}
        for task in body.get("tasks", []):
            for item in task.get("result") or []:
                if item and item.get("keyword"):
                    result[item["keyword"]] = item.get("search_volume") or 0
        return result

    def _fetch_difficulty(self, keywords: list[str]) -> dict[str, float]:
        body = self._post(
            "/v3/dataforseo_labs/google/bulk_keyword_difficulty/live",
            [{"keywords": keywords, "location_code": _LOCATION_CODE, "language_code": _LANGUAGE_CODE}],
        )
        result: dict[str, float] = {}
        for task in body.get("tasks", []):
            for item in task.get("result") or []:
                for kw_item in (item or {}).get("items") or []:
                    if kw_item.get("keyword"):
                        result[kw_item["keyword"]] = kw_item.get("keyword_difficulty") or 0.0
        return result
