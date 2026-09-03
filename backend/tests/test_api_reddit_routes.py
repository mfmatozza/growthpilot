def test_trigger_reddit_monitor_400_without_subreddits(client, site):
    response = client.post("/api/reddit-opportunities/run", json={"site_id": site.id})
    assert response.status_code == 400
    assert "subreddit" in response.json()["detail"].lower()


def test_trigger_reddit_monitor_400_without_reddit_credentials(client, db_session, site):
    site.subreddits = "SaaS"
    db_session.commit()

    response = client.post("/api/reddit-opportunities/run", json={"site_id": site.id})

    assert response.status_code == 400
    assert "REDDIT_CLIENT_ID" in response.json()["detail"]


def test_trigger_reddit_monitor_404_for_missing_site(client):
    response = client.post("/api/reddit-opportunities/run", json={"site_id": 999})
    assert response.status_code == 404


def test_update_site_sets_subreddits(client, site):
    response = client.patch(f"/api/sites/{site.id}", json={"subreddits": "SaaS, Entrepreneur"})
    assert response.status_code == 200
    assert response.json()["subreddits"] == "SaaS, Entrepreneur"
