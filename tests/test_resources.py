import os

os.environ["DATABASE_URL"] = "sqlite:///./test_resources.db"
os.environ["SECRET_KEY"] = "test-secret-key"

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_invalid_input_does_not_crash():
    response = client.post("/api/v1/auth/login", json={"email": "not-an-email", "password": "x"})
    assert response.status_code == 422
    assert "errors" in response.json()


def test_options_is_not_rejected_by_authentication():
    response = client.options(
        "/api/v1/auth/me",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
    )
    assert response.status_code in (200, 204)
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_user_can_read_own_resources():
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "User12345!"},
    )
    token = login.json()["access_token"]
    response = client.get("/api/v1/resources", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert all(item["owner_id"] == 2 for item in response.json())
