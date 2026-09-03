from app.models.keyword import Keyword, KeywordStatus


def test_create_and_list_sites(client):
    response = client.post("/api/sites", json={"url": "https://acme.com", "name": "Acme"})
    assert response.status_code == 201

    response = client.get("/api/sites")
    assert response.status_code == 200
    assert response.json()[0]["name"] == "Acme"


def test_delete_site_removes_it_and_its_keywords(client, db_session, site):
    db_session.add(Keyword(site_id=site.id, keyword="a", status=KeywordStatus.candidate))
    db_session.commit()

    response = client.delete(f"/api/sites/{site.id}")
    assert response.status_code == 204

    assert client.get(f"/api/sites/{site.id}").status_code == 404
    assert client.get(f"/api/keywords?site_id={site.id}").json() == []


def test_delete_site_404_for_missing_site(client):
    response = client.delete("/api/sites/999")
    assert response.status_code == 404


def test_create_site_conflicts_on_duplicate_url(client):
    client.post("/api/sites", json={"url": "https://acme.com", "name": "Acme"})
    response = client.post("/api/sites", json={"url": "https://acme.com", "name": "Acme Again"})
    assert response.status_code == 409


def test_list_keywords_filters_by_site_and_status(client, db_session, site):
    other_site_response = client.post("/api/sites", json={"url": "https://other.com", "name": "Other"})
    other_site_id = other_site_response.json()["id"]

    db_session.add_all(
        [
            Keyword(site_id=site.id, keyword="a", status=KeywordStatus.candidate),
            Keyword(site_id=site.id, keyword="b", status=KeywordStatus.approved),
            Keyword(site_id=other_site_id, keyword="c", status=KeywordStatus.candidate),
        ]
    )
    db_session.commit()

    response = client.get(f"/api/keywords?site_id={site.id}&status=candidate")
    assert response.status_code == 200
    keywords = response.json()
    assert len(keywords) == 1
    assert keywords[0]["keyword"] == "a"


def test_update_keyword_status_approves_a_candidate(client, db_session, site):
    keyword = Keyword(site_id=site.id, keyword="widget guide", status=KeywordStatus.candidate)
    db_session.add(keyword)
    db_session.commit()
    db_session.refresh(keyword)

    response = client.patch(f"/api/keywords/{keyword.id}", json={"status": "approved"})

    assert response.status_code == 200
    assert response.json()["status"] == "approved"


def test_update_keyword_status_404_for_missing_keyword(client):
    response = client.patch("/api/keywords/999", json={"status": "approved"})
    assert response.status_code == 404


def test_trigger_keyword_research_400_without_llm_key(client, site):
    # No OPENAI_API_KEY configured in the test environment (default
    # LLM_PROVIDER) — the endpoint should fail clearly rather than crash.
    response = client.post("/api/keywords/research", json={"site_id": site.id})
    assert response.status_code == 400
    assert "OPENAI_API_KEY" in response.json()["detail"]


def test_trigger_keyword_research_404_for_missing_site(client):
    response = client.post("/api/keywords/research", json={"site_id": 999})
    assert response.status_code == 404
