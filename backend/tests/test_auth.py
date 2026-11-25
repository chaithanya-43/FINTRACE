from fastapi.testclient import TestClient

from tests.conftest import register


def test_register_returns_token_and_citizen_role(client: TestClient) -> None:
    payload = register(client, email="new.user@example.com")

    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["user"]["role"] == "citizen"
    assert payload["user"]["email"] == "new.user@example.com"


def test_registration_rejects_duplicate_email(client: TestClient) -> None:
    register(client, email="duplicate@example.com")
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "DUPLICATE@example.com",
            "password": "correct-horse-battery",
            "full_name": "Second Person",
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "email_taken"


def test_registration_cannot_set_role(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "sneaky@example.com",
            "password": "correct-horse-battery",
            "full_name": "Sneaky Person",
            "role": "administrator",
        },
    )
    assert response.status_code == 422


def test_short_password_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "weak@example.com", "password": "short", "full_name": "Weak"},
    )
    assert response.status_code == 422


def test_login_and_current_user(client: TestClient, account) -> None:
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "victim@example.com", "password": "correct-horse-battery"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "victim@example.com"


def test_wrong_password_is_unauthorized(client: TestClient, account) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "victim@example.com", "password": "definitely-wrong"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_missing_token_is_unauthorized(client: TestClient) -> None:
    response = client.get("/api/v1/cases")
    assert response.status_code == 401


def test_admin_endpoints_require_administrator(client: TestClient, account) -> None:
    response = client.get("/api/v1/admin/users", headers=account["headers"])
    assert response.status_code == 403
