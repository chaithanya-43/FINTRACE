import hashlib

from fastapi.testclient import TestClient

CONTENT = b"Transaction alert: INR 15000 debited on 20-11-2026. UTR 424242424242."


def _upload(client: TestClient, headers: dict, case_id: str, *, content: bytes = CONTENT):
    return client.post(
        f"/api/v1/cases/{case_id}/evidence",
        headers=headers,
        files={"file": ("alert.txt", content, "text/plain")},
        data={"evidence_type": "bank_alert", "description": "Bank SMS"},
    )


def test_upload_records_sha256_of_stored_bytes(client: TestClient, account, case) -> None:
    response = _upload(client, account["headers"], case["id"])
    assert response.status_code == 201, response.text

    body = response.json()
    assert body["sha256_hash"] == hashlib.sha256(CONTENT).hexdigest()
    assert body["byte_size"] == len(CONTENT)
    assert body["verification_status"] == "unverified"
    assert body["chain_of_custody"][0]["event"] == "uploaded"


def test_duplicate_bytes_are_allowed(client: TestClient, account, case) -> None:
    first = _upload(client, account["headers"], case["id"])
    second = _upload(client, account["headers"], case["id"])

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["sha256_hash"] == second.json()["sha256_hash"]

    listing = client.get(
        f"/api/v1/cases/{case['id']}/evidence", headers=account["headers"]
    )
    assert len(listing.json()) == 2


def test_verification_recomputes_and_matches(client: TestClient, account, case) -> None:
    evidence = _upload(client, account["headers"], case["id"]).json()

    response = client.post(
        f"/api/v1/cases/{case['id']}/evidence/{evidence['id']}/verify",
        headers=account["headers"],
    )
    assert response.status_code == 200
    body = response.json()
    assert body["hash_matches"] is True
    assert body["recomputed_hash"] == body["stored_hash"]
    assert body["verification_status"] == "verified"
    assert body["signature_status"] == "not_signed"


def test_download_returns_original_bytes(client: TestClient, account, case) -> None:
    evidence = _upload(client, account["headers"], case["id"]).json()

    response = client.get(
        f"/api/v1/cases/{case['id']}/evidence/{evidence['id']}/download",
        headers=account["headers"],
    )
    assert response.status_code == 200
    assert response.content == CONTENT
    assert response.headers["x-evidence-sha256"] == evidence["sha256_hash"]


def test_unsupported_content_type_is_rejected(client: TestClient, account, case) -> None:
    response = client.post(
        f"/api/v1/cases/{case['id']}/evidence",
        headers=account["headers"],
        files={"file": ("payload.exe", b"MZ", "application/x-msdownload")},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "unsupported_file_type"


def test_evidence_of_another_user_is_not_accessible(
    client: TestClient, account, other_account, case
) -> None:
    evidence = _upload(client, account["headers"], case["id"]).json()

    response = client.get(
        f"/api/v1/cases/{case['id']}/evidence/{evidence['id']}/download",
        headers=other_account["headers"],
    )
    assert response.status_code == 404


def test_signing_reports_unavailable_without_a_key(client: TestClient, account, case) -> None:
    evidence = _upload(client, account["headers"], case["id"]).json()
    client.post(
        f"/api/v1/cases/{case['id']}/evidence/{evidence['id']}/verify",
        headers=account["headers"],
    )

    response = client.post(
        f"/api/v1/cases/{case['id']}/evidence/{evidence['id']}/sign",
        headers=account["headers"],
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "signing_unavailable"
