from fastapi.testclient import TestClient


def _transaction(**overrides) -> dict:
    payload = {
        "amount": "5000.00",
        "currency": "INR",
        "transaction_at": "2026-11-20T10:35:00Z",
        "authorization_type": "unauthorized",
        "channel": "upi",
        "counterparty_name": "Refund Desk",
        "utr_reference": "424242424242",
    }
    payload.update(overrides)
    return payload


def test_create_transaction_updates_case_loss(client: TestClient, account, case) -> None:
    response = client.post(
        f"/api/v1/cases/{case['id']}/transactions",
        headers=account["headers"],
        json=_transaction(amount="2500.00"),
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["amount"] == "2500.00"
    assert body["source"] == "user"

    listed = client.get(
        f"/api/v1/cases/{case['id']}/transactions", headers=account["headers"]
    )
    assert len(listed.json()) == 1


def test_duplicate_utr_in_same_case_is_rejected(client: TestClient, account, case) -> None:
    first = client.post(
        f"/api/v1/cases/{case['id']}/transactions",
        headers=account["headers"],
        json=_transaction(),
    )
    assert first.status_code == 201

    duplicate = client.post(
        f"/api/v1/cases/{case['id']}/transactions",
        headers=account["headers"],
        json=_transaction(amount="10.00"),
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "duplicate_utr"


def test_same_utr_in_different_cases_is_allowed(client: TestClient, account, case) -> None:
    second_case = client.post(
        "/api/v1/cases",
        headers=account["headers"],
        json={"title": "Second incident", "incident_type": "card_fraud"},
    ).json()

    for case_id in (case["id"], second_case["id"]):
        response = client.post(
            f"/api/v1/cases/{case_id}/transactions",
            headers=account["headers"],
            json=_transaction(),
        )
        assert response.status_code == 201, response.text


def test_zero_amount_is_rejected(client: TestClient, account, case) -> None:
    response = client.post(
        f"/api/v1/cases/{case['id']}/transactions",
        headers=account["headers"],
        json=_transaction(amount="0"),
    )
    assert response.status_code == 422


def test_authentication_secrets_are_rejected(client: TestClient, account, case) -> None:
    response = client.post(
        f"/api/v1/cases/{case['id']}/transactions",
        headers=account["headers"],
        json=_transaction(notes="The caller asked for the OTP 123456 and I shared it"),
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "sensitive_data_rejected"


def test_transaction_from_another_case_is_not_visible(
    client: TestClient, account, other_account, case
) -> None:
    created = client.post(
        f"/api/v1/cases/{case['id']}/transactions",
        headers=account["headers"],
        json=_transaction(),
    ).json()

    response = client.patch(
        f"/api/v1/cases/{case['id']}/transactions/{created['id']}",
        headers=other_account["headers"],
        json={"status": "disputed"},
    )
    assert response.status_code == 404


def test_update_transaction_verification_status(client: TestClient, account, case) -> None:
    created = client.post(
        f"/api/v1/cases/{case['id']}/transactions",
        headers=account["headers"],
        json=_transaction(),
    ).json()

    response = client.patch(
        f"/api/v1/cases/{case['id']}/transactions/{created['id']}",
        headers=account["headers"],
        json={"verification_status": "disputed", "status": "disputed"},
    )
    assert response.status_code == 200
    assert response.json()["verification_status"] == "disputed"
