from fastapi.testclient import TestClient

from app.main import app


def test_login_succeeds_with_correct_credentials(client):
    response = client.post("/api/auth/login", json={"email": "test@example.com", "password": "test-password"})
    assert response.status_code == 200
    assert response.json() == {"token": "test-secret-key"}


def test_login_rejects_wrong_password(client):
    response = client.post("/api/auth/login", json={"email": "test@example.com", "password": "not-it"})
    assert response.status_code == 401


def test_login_rejects_wrong_email(client):
    response = client.post("/api/auth/login", json={"email": "nope@example.com", "password": "test-password"})
    assert response.status_code == 401


def test_login_rejects_garbage_credentials(client):
    response = client.post("/api/auth/login", json={"email": "a@a", "password": "a"})
    assert response.status_code == 401


def test_protected_route_401s_without_a_token(db_session):
    from app.api.deps import get_db

    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as unauthenticated_client:
        response = unauthenticated_client.get("/api/sites")
    app.dependency_overrides.clear()

    assert response.status_code == 401


def test_protected_route_401s_with_a_wrong_token(db_session):
    from app.api.deps import get_db

    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app, headers={"Authorization": "Bearer wrong-token"}) as bad_client:
        response = bad_client.get("/api/sites")
    app.dependency_overrides.clear()

    assert response.status_code == 401


def test_health_needs_no_auth():
    with TestClient(app) as unauthenticated_client:
        response = unauthenticated_client.get("/health")
    assert response.status_code == 200
