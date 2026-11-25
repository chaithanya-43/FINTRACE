"""End-to-end smoke test against a running FINTRACE API.

Exercises the whole prototype the way the frontend does: register, create a
case, record a transaction, upload and verify evidence, run the analysis, run a
regulatory assessment, generate the roadmap, file a complaint and observe its
status, then read the audit trail.

Usage (with the API running, e.g. on port 8000):

    python scripts/smoke_test.py [base_url]

Exits non-zero on the first failed assertion.
"""

import hashlib
import sys
import uuid

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000/api/v1"

EVIDENCE_BYTES = (
    b"Bank alert: INR 15,000 debited on 20-11-2026 to VPA refund-desk@upi. "
    b"UTR 424242424242."
)


def check(label: str, condition: bool, detail: object = "") -> None:
    if not condition:
        raise SystemExit(f"FAILED: {label} {detail}")
    print(f"  ok  {label}")


def main() -> None:
    client = httpx.Client(base_url=BASE, timeout=30)

    health = client.get("/health")
    check("health", health.status_code == 200 and health.json() == {"status": "ok"})

    email = f"smoke-{uuid.uuid4().hex[:10]}@example.com"
    registration = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "smoke-test-password",
            "full_name": "Smoke Test",
        },
    )
    check("register", registration.status_code == 201, registration.text[:200])
    token = registration.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"

    me = client.get("/auth/me")
    check("current user", me.json()["email"] == email)

    case = client.post(
        "/cases",
        json={
            "title": "Unauthorised UPI debit",
            "description": (
                "A caller pretending to be from my bank sent a collect request for a "
                "refund. I approved it and INR 15,000 left my account. The caller then "
                "stopped answering and the number is now unreachable."
            ),
            "incident_type": "upi_fraud",
            "fraud_channel": "upi",
            "incident_occurred_at": "2026-11-20T10:30:00Z",
            "estimated_loss_amount": "15000.00",
        },
    )
    check("create case", case.status_code == 201, case.text[:200])
    case_id = case.json()["id"]

    transaction = client.post(
        f"/cases/{case_id}/transactions",
        json={
            "amount": "15000.00",
            "transaction_at": "2026-11-20T10:35:00Z",
            "authorization_type": "authorized_deceived",
            "channel": "upi",
            "utr_reference": "424242424242",
        },
    )
    check("add transaction", transaction.status_code == 201, transaction.text[:200])

    duplicate = client.post(
        f"/cases/{case_id}/transactions",
        json={"amount": "1.00", "utr_reference": "424242424242"},
    )
    check("duplicate UTR rejected", duplicate.status_code == 409)

    upload = client.post(
        f"/cases/{case_id}/evidence",
        files={"file": ("alert.txt", EVIDENCE_BYTES, "text/plain")},
        data={"evidence_type": "bank_alert", "description": "Bank SMS alert"},
    )
    check("upload evidence", upload.status_code == 201, upload.text[:200])
    evidence = upload.json()
    check(
        "sha256 matches uploaded bytes",
        evidence["sha256_hash"] == hashlib.sha256(EVIDENCE_BYTES).hexdigest(),
    )

    duplicate_upload = client.post(
        f"/cases/{case_id}/evidence",
        files={"file": ("alert-copy.txt", EVIDENCE_BYTES, "text/plain")},
        data={"evidence_type": "bank_alert"},
    )
    check("duplicate evidence allowed", duplicate_upload.status_code == 201)

    verify = client.post(f"/cases/{case_id}/evidence/{evidence['id']}/verify")
    check("verify evidence", verify.status_code == 200 and verify.json()["hash_matches"])

    download = client.get(f"/cases/{case_id}/evidence/{evidence['id']}/download")
    check("download evidence", download.content == EVIDENCE_BYTES)

    analysis = client.post(f"/cases/{case_id}/analyze")
    check("analysis engine", analysis.json()["engine"] == "deterministic-keyword-v1")

    assessment = client.post(f"/cases/{case_id}/assessments", json={})
    if assessment.status_code == 503:
        print("  --  no active rules seeded; skipping assessments")
    else:
        check("run assessment", assessment.status_code == 201, assessment.text[:200])
        first = assessment.json()[0]
        check("assessment has rule snapshot", bool(first["rule_code"] and first["input_snapshot_hash"]))
        again = client.post(f"/cases/{case_id}/assessments", json={})
        check("identical assessment is not duplicated", again.json()[0]["id"] == first["id"])

    roadmap = client.get(f"/cases/{case_id}/roadmap")
    check("roadmap", roadmap.status_code == 200 and len(roadmap.json()["actions"]) > 0)
    action = roadmap.json()["actions"][0]
    updated = client.patch(
        f"/cases/{case_id}/actions/{action['id']}",
        json={"status": "completed", "outcome_status": "pending"},
    )
    check("complete action", updated.status_code == 200 and updated.json()["completed_at"])

    complaint = client.post(
        f"/cases/{case_id}/complaints",
        json={
            "channel": "cybercrime_portal",
            "organisation_name": "National Cyber Crime Reporting Portal",
            "submission_status": "submitted",
        },
    )
    check("create complaint", complaint.status_code == 201, complaint.text[:200])
    complaint_id = complaint.json()["id"]

    observation = client.post(
        f"/cases/{case_id}/complaints/{complaint_id}/history",
        json={"observed_status": "acknowledged", "status_detail": "Shown as under review."},
    )
    check("record status observation", observation.status_code == 201, observation.text[:200])

    history = client.get(f"/cases/{case_id}/complaints/{complaint_id}/history")
    check("status history", len(history.json()) == 1)

    audit = client.get(f"/cases/{case_id}/audit")
    actions = [event["action"] for event in audit.json()]
    check("audit trail", "case.created" in actions and "evidence.uploaded" in actions)

    dashboard = client.get("/dashboard/summary")
    check("dashboard totals", dashboard.json()["total_cases"] >= 1)

    stranger = httpx.Client(base_url=BASE, timeout=30)
    other = stranger.post(
        "/auth/register",
        json={
            "email": f"smoke-other-{uuid.uuid4().hex[:8]}@example.com",
            "password": "smoke-test-password",
            "full_name": "Other Person",
        },
    )
    stranger.headers["Authorization"] = f"Bearer {other.json()['access_token']}"
    hidden = stranger.get(f"/cases/{case_id}")
    check("cross-account case hidden", hidden.status_code == 404)

    print("\nAll smoke checks passed.")


if __name__ == "__main__":
    main()
