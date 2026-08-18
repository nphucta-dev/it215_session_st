import os

os.environ["DATABASE_URL"] = "sqlite:///./test_authorization.db"
os.environ["SECRET_KEY"] = "test-secret-key"

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def token(email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_user_cannot_list_users():
    t = token("user@example.com", "User12345!")
    response = client.get("/api/v1/users", headers={"Authorization": f"Bearer {t}"})
    assert response.status_code == 403


def test_user_cannot_create_resource():
    t = token("user@example.com", "User12345!")
    response = client.post(
        "/api/v1/resources",
        headers={"Authorization": f"Bearer {t}"},
        json={
            "title": "Forbidden resource",
            "description": "Should be rejected",
            "resource_type": "document",
            "owner_id": 2,
        },
    )
    assert response.status_code == 403


def test_user_cannot_access_other_users_resource():
    admin_token = token("admin@example.com", "Admin123!")
    created = client.post(
        "/api/v1/resources",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Admin owned resource",
            "description": "Ownership test",
            "resource_type": "document",
            "owner_id": 1,
        },
    )
    assert created.status_code == 201

    user_token = token("user@example.com", "User12345!")
    resource_id = created.json()["id"]
    response = client.get(f"/api/v1/resources/{resource_id}", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 403
