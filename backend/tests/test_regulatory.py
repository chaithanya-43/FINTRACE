from datetime import date

from fastapi.testclient import TestClient

from app.models import RegulatoryRule

RULE_PAYLOAD = {
    "logic": "all",
    "conditions": [
        {"fact": "transaction_count", "operator": "gte", "value": 1},
        {"fact": "authorization_types", "operator": "contains_any", "value": ["unauthorized"]},
    ],
}


def seed_rule(db, *, code: str = "TEST-RULE", version: int = 1) -> RegulatoryRule:
    rule = RegulatoryRule(
        rule_code=code,
        version=version,
        title="Unverified example rule",
        jurisdiction="IN",
        authority="Unverified example - not a legal provision",
        source_reference="Configuration example seeded for the prototype.",
        source_url="https://cybercrime.gov.in",
        effective_from=date(2020, 1, 1),
        rule_payload=RULE_PAYLOAD,
        status="active",
        verification_status="unverified",
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def test_assessment_without_rules_reports_unavailable(
    client: TestClient, account, case
) -> None:
    response = client.post(
        f"/api/v1/cases/{case['id']}/assessments",
        headers=account["headers"],
        json={},
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "no_active_rules"


def test_assessment_persists_rule_and_input_snapshots(
    client: TestClient, account, case, db
) -> None:
    client.post(
        f"/api/v1/cases/{case['id']}/transactions",
        headers=account["headers"],
        json={
            "amount": "15000.00",
            "authorization_type": "unauthorized",
            "transaction_at": "2026-11-20T10:35:00Z",
        },
    )
    seed_rule(db)

    response = client.post(
        f"/api/v1/cases/{case['id']}/assessments",
        headers=account["headers"],
        json={},
    )
    assert response.status_code == 201, response.text
    assessment = response.json()[0]

    assert assessment["result_status"] == "applies"
    assert assessment["rule_code"] == "TEST-RULE"
    assert assessment["rule_version"] == 1
    assert assessment["rule_verification_status"] == "unverified"
    assert len(assessment["input_snapshot_hash"]) == 64
    assert assessment["input_snapshot"]["case"]["incident_type"] == "upi_fraud"
    assert "not a legal" in assessment["explanation"]


def test_repeating_identical_assessment_does_not_duplicate(
    client: TestClient, account, case, db
) -> None:
    seed_rule(db)
    first = client.post(
        f"/api/v1/cases/{case['id']}/assessments", headers=account["headers"], json={}
    ).json()[0]
    second = client.post(
        f"/api/v1/cases/{case['id']}/assessments", headers=account["headers"], json={}
    ).json()[0]

    assert first["id"] == second["id"]

    history = client.get(
        f"/api/v1/cases/{case['id']}/assessments", headers=account["headers"]
    ).json()
    assert len(history["assessments"]) == 1
    assert "not legal advice" in history["disclaimer"]


def test_changed_facts_create_a_superseding_assessment(
    client: TestClient, account, case, db
) -> None:
    seed_rule(db)
    original = client.post(
        f"/api/v1/cases/{case['id']}/assessments", headers=account["headers"], json={}
    ).json()[0]
    # The seeded rule needs a transaction; adding one changes the input snapshot.
    client.post(
        f"/api/v1/cases/{case['id']}/transactions",
        headers=account["headers"],
        json={"amount": "7500.00", "authorization_type": "unauthorized"},
    )
    follow_up = client.post(
        f"/api/v1/cases/{case['id']}/assessments", headers=account["headers"], json={}
    ).json()[0]

    assert follow_up["id"] != original["id"]
    assert follow_up["supersedes_assessment_id"] == original["id"]

    history = client.get(
        f"/api/v1/cases/{case['id']}/assessments", headers=account["headers"]
    ).json()
    assert len(history["assessments"]) == 2


def test_review_updates_only_review_columns(client: TestClient, account, case, db) -> None:
    seed_rule(db)
    assessment = client.post(
        f"/api/v1/cases/{case['id']}/assessments", headers=account["headers"], json={}
    ).json()[0]

    response = client.patch(
        f"/api/v1/assessments/{assessment['id']}/review",
        headers=account["headers"],
        json={"review_status": "confirmed", "review_note": "Checked against the record."},
    )
    assert response.status_code == 200
    assert response.json()["review_status"] == "confirmed"
    assert response.json()["result_status"] == assessment["result_status"]
