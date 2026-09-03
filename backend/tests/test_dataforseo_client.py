import httpx
import pytest
import respx

from app.services.keyword_data.base import KeywordDataError, KeywordMetrics
from app.services.keyword_data.dataforseo import DataForSEOProvider


def test_missing_credentials_raises_immediately():
    with pytest.raises(KeywordDataError, match="DATAFORSEO_LOGIN"):
        DataForSEOProvider(login="", password="")


@respx.mock
def test_get_metrics_merges_volume_and_difficulty():
    respx.post("https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live").mock(
        return_value=httpx.Response(
            200,
            json={
                "status_code": 20000,
                "tasks": [{"result": [{"keyword": "widgets", "search_volume": 1200}]}],
            },
        )
    )
    respx.post("https://api.dataforseo.com/v3/dataforseo_labs/google/bulk_keyword_difficulty/live").mock(
        return_value=httpx.Response(
            200,
            json={
                "status_code": 20000,
                "tasks": [{"result": [{"items": [{"keyword": "widgets", "keyword_difficulty": 42}]}]}],
            },
        )
    )

    provider = DataForSEOProvider(login="user", password="pass")
    metrics = provider.get_metrics(["widgets"])

    assert len(metrics) == 1
    assert metrics[0].keyword == "widgets"
    assert metrics[0].volume == 1200
    assert metrics[0].difficulty == 42


@respx.mock
def test_get_metrics_defaults_missing_keyword_to_none():
    respx.post("https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live").mock(
        return_value=httpx.Response(200, json={"status_code": 20000, "tasks": [{"result": []}]})
    )
    respx.post("https://api.dataforseo.com/v3/dataforseo_labs/google/bulk_keyword_difficulty/live").mock(
        return_value=httpx.Response(200, json={"status_code": 20000, "tasks": [{"result": [{"items": []}]}]})
    )

    provider = DataForSEOProvider(login="user", password="pass")
    metrics = provider.get_metrics(["never-seen-keyword"])

    assert metrics == [KeywordMetrics(keyword="never-seen-keyword", volume=None, difficulty=None)]


@respx.mock
def test_non_2xx_status_raises_keyword_data_error():
    respx.post("https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live").mock(
        return_value=httpx.Response(401, json={"status_message": "auth failed"})
    )

    provider = DataForSEOProvider(login="bad", password="creds")
    with pytest.raises(KeywordDataError):
        provider.get_metrics(["widgets"])


@respx.mock
def test_api_level_error_status_code_raises_keyword_data_error():
    respx.post("https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live").mock(
        return_value=httpx.Response(200, json={"status_code": 40000, "status_message": "bad request"})
    )

    provider = DataForSEOProvider(login="user", password="pass")
    with pytest.raises(KeywordDataError, match="bad request"):
        provider.get_metrics(["widgets"])
