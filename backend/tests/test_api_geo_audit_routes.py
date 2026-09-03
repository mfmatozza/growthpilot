def test_trigger_geo_check_400_without_any_provider_key(client, site):
    response = client.post("/api/geo-mentions/run", json={"site_id": site.id})
    assert response.status_code == 400
    assert "provider" in response.json()["detail"].lower()


def test_trigger_geo_check_404_for_missing_site(client):
    response = client.post("/api/geo-mentions/run", json={"site_id": 999})
    assert response.status_code == 404


def test_trigger_audit_502_when_site_is_unreachable(client, site, monkeypatch):
    import os

    from app.services.crawler.httpx_fetcher import HttpxFetcher
    from app.services.crawler.base import FetchError

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    from app.core.config import get_settings

    get_settings.cache_clear()

    def _always_fails(self, url):
        raise FetchError("DNS resolution failed")

    monkeypatch.setattr(HttpxFetcher, "fetch", _always_fails)

    response = client.post("/api/audit-findings/run", json={"site_id": site.id})

    assert response.status_code == 502
    get_settings.cache_clear()
    os.environ.pop("OPENAI_API_KEY", None)


def test_trigger_audit_400_without_llm_key(client, site):
    response = client.post("/api/audit-findings/run", json={"site_id": site.id})
    assert response.status_code == 400
    assert "OPENAI_API_KEY" in response.json()["detail"]


def test_trigger_audit_404_for_missing_site(client):
    response = client.post("/api/audit-findings/run", json={"site_id": 999})
    assert response.status_code == 404
