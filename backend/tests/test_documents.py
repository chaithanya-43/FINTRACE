from fastapi.testclient import TestClient


def _full_case(client: TestClient, headers: dict[str, str], *, with_tx: bool = True) -> dict:
    case = client.post(
        "/api/v1/cases",
        headers=headers,
        json={
            "title": "Unauthorized UPI debit after KYC call",
            "description": (
                "A caller pretending to be a bank representative said my KYC would be "
                "suspended. Shortly afterward, INR 25,000 was debited via UPI without "
                "my authorization."
            ),
            "incident_type": "otp_phishing",
            "fraud_channel": "phone_call",
            "incident_occurred_at": "2026-11-25T09:15:00Z",
            "estimated_loss_amount": "25000.00",
            "reporting_details": "Called 1930 and awaiting bank ticket.",
        },
    ).json()

    if with_tx:
        client.post(
            f"/api/v1/cases/{case['id']}/transactions",
            headers=headers,
            json={
                "amount": "25000.00",
                "transaction_at": "2026-11-25T09:18:00Z",
                "authorization_type": "unauthorized",
                "channel": "upi",
                "counterparty_name": "Unknown KYC Caller",
                "utr_reference": "UPI202611250001",
            },
        )
    return case


def test_catalog_lists_all_seven_document_types(client: TestClient, account) -> None:
    resp = client.get("/api/v1/documents/catalog", headers=account["headers"])
    assert resp.status_code == 200
    types = {item["document_type"] for item in resp.json()}
    assert types == {
        "cybercrime_complaint",
        "bank_fraud_complaint",
        "transaction_dispute_letter",
        "upi_fraud_complaint",
        "police_complaint",
        "follow_up_letter",
        "escalation_letter",
    }


def test_tc001_to_tc006_generate_all_document_types_edit_and_pdf(
    client: TestClient, account
) -> None:
    case = _full_case(client, account["headers"])
    client.post(
        f"/api/v1/cases/{case['id']}/complaints",
        headers=account["headers"],
        json={
            "channel": "bank",
            "organisation_name": "State Bank Demo",
            "reference_number": "BNK-2026-771",
            "submission_status": "submitted",
        },
    )

    # Prefill check
    prefill = client.get(
        f"/api/v1/cases/{case['id']}/documents/prefill",
        headers=account["headers"],
        params={"document_type": "cybercrime_complaint"},
    )
    assert prefill.status_code == 200
    assert prefill.json()["prefilled_answers"]["full_name"] == "Test Victim"

    doc_types = [
        "cybercrime_complaint",
        "bank_fraud_complaint",
        "transaction_dispute_letter",
        "upi_fraud_complaint",
        "police_complaint",
        "follow_up_letter",
        "escalation_letter",
    ]
    draft_ids = []
    for doc_type in doc_types:
        gen = client.post(
            f"/api/v1/cases/{case['id']}/documents/generate",
            headers=account["headers"],
            json={
                "document_type": doc_type,
                "intake_answers": {
                    "bank_name": "State Bank Demo",
                    "upi_app_name": "BHIM",
                    "police_station": "Koramangala Cyber PS",
                },
            },
        )
        assert gen.status_code == 201, f"{doc_type} failed: {gen.text}"
        draft = gen.json()
        draft_ids.append(draft["id"])
        assert "DRAFT" in draft["content"]
        assert "UPI202611250001" in draft["content"]
        assert "25,000.00" in draft["content"]
        assert len(draft["attachments_checklist"]) >= 3

    # Edit first draft and verify persistence
    updated = client.patch(
        f"/api/v1/cases/{case['id']}/documents/{draft_ids[0]}",
        headers=account["headers"],
        json={
            "content": "DRAFT — Edited content for review.\n\nUpdated paragraph with verified bank ticket.",
            "draft_status": "reviewed",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["draft_status"] == "reviewed"
    assert "Updated paragraph" in updated.json()["content"]

    # Export A4 PDF
    pdf_resp = client.get(
        f"/api/v1/cases/{case['id']}/documents/{draft_ids[0]}/pdf",
        headers=account["headers"],
    )
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert pdf_resp.content.startswith(b"%PDF-")

    # Audit events recorded
    audit = client.get(f"/api/v1/cases/{case['id']}/audit", headers=account["headers"]).json()
    actions = {ev["action"] for ev in audit}
    assert "document_draft.created" in actions
    assert "document_draft.updated" in actions


def test_tc007_incomplete_personal_info_marks_not_provided(client: TestClient, account) -> None:
    case = _full_case(client, account["headers"], with_tx=False)
    gen = client.post(
        f"/api/v1/cases/{case['id']}/documents/generate",
        headers=account["headers"],
        json={"document_type": "cybercrime_complaint", "intake_answers": {"phone": "", "address": ""}},
    )
    assert gen.status_code == 201
    content = gen.json()["content"]
    assert "Not provided" in content
    assert "No individual financial transactions have been recorded" in content


def test_tc008_multiple_transactions_and_security(
    client: TestClient, account, other_account
) -> None:
    case = _full_case(client, account["headers"], with_tx=True)
    client.post(
        f"/api/v1/cases/{case['id']}/transactions",
        headers=account["headers"],
        json={
            "amount": "15000.00",
            "transaction_at": "2026-11-25T09:22:00Z",
            "authorization_type": "unauthorized",
            "channel": "upi",
            "utr_reference": "UPI202611250002",
        },
    )

    gen = client.post(
        f"/api/v1/cases/{case['id']}/documents/generate",
        headers=account["headers"],
        json={"document_type": "upi_fraud_complaint"},
    )
    assert gen.status_code == 201
    content = gen.json()["content"]
    assert "Transaction #1:" in content
    assert "Transaction #2:" in content
    assert "UPI202611250001" in content
    assert "UPI202611250002" in content

    # Sensitive secret rejected
    bad = client.post(
        f"/api/v1/cases/{case['id']}/documents/generate",
        headers=account["headers"],
        json={
            "document_type": "bank_fraud_complaint",
            "intake_answers": {"bank_name": "OTP is 482910"},
        },
    )
    assert bad.status_code == 400
    assert bad.json()["error"]["code"] == "sensitive_data_rejected"

    # Cross-user isolation
    hidden = client.get(
        f"/api/v1/cases/{case['id']}/documents", headers=other_account["headers"]
    )
    assert hidden.status_code == 404
