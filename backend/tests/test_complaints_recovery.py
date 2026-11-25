from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient


def test_complaint_lifecycle_and_status_history(client: TestClient, account, case) -> None:
    created = client.post(
        f"/api/v1/cases/{case['id']}/complaints",
        headers=account["headers"],
        json={
            "channel": "cybercrime_portal",
            "organisation_name": "National Cyber Crime Reporting Portal",
            "submission_status": "submitted",
        },
    )
    assert created.status_code == 201, created.text
    complaint = created.json()
    # filed_at is filled in automatically once the user reports submitting it.
    assert complaint["filed_at"] is not None
    assert complaint["official_status"] is None

    observed = client.post(
        f"/api/v1/cases/{case['id']}/complaints/{complaint['id']}/history",
        headers=account["headers"],
        json={
            "observed_status": "acknowledged",
            "status_detail": "Portal shows the complaint under review.",
            "console": "ignored",
        },
    )
    assert observed.status_code == 422  # extra fields are rejected

    observed = client.post(
        f"/api/v1/cases/{case['id']}/complaints/{complaint['id']}/history",
        headers=account["headers"],
        json={"observed_status": "acknowledged", "status_detail": "Portal shows review."},
    )
    assert observed.status_code == 201, observed.text

    listing = client.get(
        f"/api/v1/cases/{case['id']}/complaints", headers=account["headers"]
    ).json()
    assert listing[0]["official_status"] == "acknowledged"
    assert listing[0]["last_checked_at"] is not None

    history = client.get(
        f"/api/v1/cases/{case['id']}/complaints/{complaint['id']}/history",
        headers=account["headers"],
    ).json()
    assert len(history) == 1
    assert history[0]["observed_status"] == "acknowledged"


def test_duplicate_status_observation_is_rejected(
    client: TestClient, account, case
) -> None:
    complaint = client.post(
        f"/api/v1/cases/{case['id']}/complaints",
        headers=account["headers"],
        json={"channel": "bank"},
    ).json()
    checked_at = "2026-11-24T09:00:00Z"
    payload = {"observed_status": "pending", "checked_at": checked_at}

    first = client.post(
        f"/api/v1/cases/{case['id']}/complaints/{complaint['id']}/history",
        headers=account["headers"],
        json=payload,
    )
    assert first.status_code == 201

    duplicate = client.post(
        f"/api/v1/cases/{case['id']}/complaints/{complaint['id']}/history",
        headers=account["headers"],
        json=payload,
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "duplicate_observation"


def test_unknown_complaint_channel_is_rejected(client: TestClient, account, case) -> None:
    response = client.post(
        f"/api/v1/cases/{case['id']}/complaints",
        headers=account["headers"],
        json={"channel": "telepathy"},
    )
    assert response.status_code == 400


def test_roadmap_is_urgent_for_a_fresh_incident(client: TestClient, account) -> None:
    recent = (datetime.now(UTC) - timedelta(hours=3)).isoformat()
    case = client.post(
        "/api/v1/cases",
        headers=account["headers"],
        json={"title": "Money still moving", "incident_occurred_at": recent},
    ).json()

    roadmap = client.get(
        f"/api/v1/cases/{case['id']}/roadmap", headers=account["headers"]
    )
    assert roadmap.status_code == 200
    body = roadmap.json()
    assert body["urgent"] is True
    assert "1930" in body["headline"]
    action_types = {action["action_type"] for action in body["actions"]}
    assert {"call_helpline", "report_cybercrime", "contact_bank"} <= action_types
    assert any(action["priority"] == "critical" for action in body["actions"])


def test_roadmap_generation_is_idempotent(client: TestClient, account, case) -> None:
    first = client.get(f"/api/v1/cases/{case['id']}/roadmap", headers=account["headers"]).json()
    second = client.get(f"/api/v1/cases/{case['id']}/roadmap", headers=account["headers"]).json()

    assert len(first["actions"]) == len(second["actions"])


def test_completing_an_action_records_completion(client: TestClient, account, case) -> None:
    roadmap = client.get(
        f"/api/v1/cases/{case['id']}/roadmap", headers=account["headers"]
    ).json()
    action = roadmap["actions"][0]

    response = client.patch(
        f"/api/v1/cases/{case['id']}/actions/{action['id']}",
        headers=account["headers"],
        json={"status": "completed", "outcome_status": "pending", "outcome_notes": "Called 1930."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["completed_at"] is not None

    refreshed = client.get(
        f"/api/v1/cases/{case['id']}/roadmap", headers=account["headers"]
    ).json()
    assert refreshed["progress"]["completed"] == 1


def test_duplicate_complaint_reference_is_rejected(client: TestClient, account, case) -> None:
    first = client.post(
        f"/api/v1/cases/{case['id']}/complaints",
        headers=account["headers"],
        json={"channel": "bank", "reference_number": "BNK-DUP-1", "submission_status": "submitted"},
    )
    assert first.status_code == 201

    duplicate = client.post(
        f"/api/v1/cases/{case['id']}/complaints",
        headers=account["headers"],
        json={"channel": "bank", "reference_number": "BNK-DUP-1", "submission_status": "submitted"},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "duplicate_complaint_reference"


def test_no_loss_phishing_roadmap_adds_credential_hardening(client: TestClient, account) -> None:
    case = client.post(
        "/api/v1/cases",
        headers=account["headers"],
        json={
            "title": "Fake KYC phishing link",
            "description": "Clicked a fake KYC link via SMS before any debit occurred.",
            "incident_type": "otp_phishing",
            "fraud_channel": "sms",
            "estimated_loss_amount": "0.00",
        },
    ).json()
    roadmap = client.get(f"/api/v1/cases/{case['id']}/roadmap", headers=account["headers"]).json()
    action_types = {a["action_type"] for a in roadmap["actions"]}
    assert "secure_credentials" in action_types
    assert "prepare_complaint" not in action_types
