from fastapi.testclient import TestClient


def test_create_case_assigns_reference_and_intake_status(client: TestClient, account, case) -> None:
    assert case["public_reference"].startswith("FT-")
    assert case["internal_status"] == "intake"
    assert case["completeness_status"] in {"partial", "complete"}


def test_citizen_cannot_read_another_users_case(
    client: TestClient, account, other_account, case
) -> None:
    response = client.get(f"/api/v1/cases/{case['id']}", headers=other_account["headers"])
    assert response.status_code == 404


def test_case_list_is_scoped_to_owner(client: TestClient, account, other_account, case) -> None:
    owner_list = client.get("/api/v1/cases", headers=account["headers"])
    assert owner_list.status_code == 200
    assert len(owner_list.json()) == 1

    other_list = client.get("/api/v1/cases", headers=other_account["headers"])
    assert other_list.status_code == 200
    assert other_list.json() == []


def test_update_case_fields(client: TestClient, account, case) -> None:
    response = client.patch(
        f"/api/v1/cases/{case['id']}",
        headers=account["headers"],
        json={"title": "Updated title", "fraud_channel": "card"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated title"
    assert response.json()["fraud_channel"] == "card"


def test_status_transition_rules(client: TestClient, account, case) -> None:
    skip = client.post(
        f"/api/v1/cases/{case['id']}/status",
        headers=account["headers"],
        json={"internal_status": "recovery"},
    )
    assert skip.status_code == 409
    assert skip.json()["error"]["code"] == "invalid_transition"

    allowed = client.post(
        f"/api/v1/cases/{case['id']}/status",
        headers=account["headers"],
        json={"internal_status": "collecting_evidence"},
    )
    assert allowed.status_code == 200
    assert allowed.json()["internal_status"] == "collecting_evidence"


def test_archive_case_is_read_only_afterwards(client: TestClient, account, case) -> None:
    archived = client.post(f"/api/v1/cases/{case['id']}/archive", headers=account["headers"])
    assert archived.status_code == 200

    update = client.patch(
        f"/api/v1/cases/{case['id']}",
        headers=account["headers"],
        json={"title": "Should fail"},
    )
    assert update.status_code == 409


def test_audit_trail_records_case_events(client: TestClient, account, case) -> None:
    response = client.get(f"/api/v1/cases/{case['id']}/audit", headers=account["headers"])
    assert response.status_code == 200
    actions = [event["action"] for event in response.json()]
    assert "case.created" in actions


def test_dashboard_summary_uses_real_data(client: TestClient, account, case) -> None:
    response = client.get("/api/v1/dashboard/summary", headers=account["headers"])
    assert response.status_code == 200
    body = response.json()
    assert body["total_cases"] == 1
    assert body["active_cases"] == 1
    assert body["recent_cases"][0]["public_reference"] == case["public_reference"]


def test_analysis_is_deterministic_and_labels_itself(client: TestClient, account, case) -> None:
    response = client.post(
        f"/api/v1/cases/{case['id']}/analyze", headers=account["headers"]
    )
    assert response.status_code == 200
    body = response.json()
    assert body["engine"] == "deterministic-keyword-v1"
    assert body["provider_configured"] is False
    assert body["suggested_incident_type"] == "upi_fraud"
    assert body["suggested_fraud_channel"] == "upi"
    assert body["missing_information"]
    assert any(fact["provenance"] == "user_provided" for fact in body["extracted_facts"])
