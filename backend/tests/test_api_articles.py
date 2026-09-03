from app.models.keyword import Keyword, KeywordStatus


def test_trigger_generation_404_for_missing_site(client):
    response = client.post("/api/articles/generate", json={"site_id": 999, "keyword_id": 1})
    assert response.status_code == 404


def test_trigger_generation_404_for_keyword_not_belonging_to_site(client, db_session, site):
    other_site_resp = client.post("/api/sites", json={"url": "https://other.com", "name": "Other"})
    other_site_id = other_site_resp.json()["id"]
    keyword = Keyword(site_id=other_site_id, keyword="x", status=KeywordStatus.approved)
    db_session.add(keyword)
    db_session.commit()
    db_session.refresh(keyword)

    response = client.post("/api/articles/generate", json={"site_id": site.id, "keyword_id": keyword.id})
    assert response.status_code == 404


def test_trigger_generation_400_without_llm_key(client, db_session, site):
    keyword = Keyword(site_id=site.id, keyword="x", status=KeywordStatus.approved)
    db_session.add(keyword)
    db_session.commit()
    db_session.refresh(keyword)

    response = client.post("/api/articles/generate", json={"site_id": site.id, "keyword_id": keyword.id})
    assert response.status_code == 400
    assert "OPENAI_API_KEY" in response.json()["detail"]


def test_get_article_404_for_missing(client):
    response = client.get("/api/articles/999")
    assert response.status_code == 404


def test_update_article_status_404_for_missing(client):
    response = client.patch("/api/articles/999", json={"status": "published"})
    assert response.status_code == 404
