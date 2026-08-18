import os

os.environ["DATABASE_URL"] = "sqlite:///./test_auth.db"
os.environ["SECRET_KEY"] = "test-secret-key"

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_login_and_current_user():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "User12345!"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "user@example.com"


def test_missing_token_is_401():
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_wrong_password_is_401():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401
