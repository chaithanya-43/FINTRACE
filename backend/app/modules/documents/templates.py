"""Deterministic complaint and dispute document templates.

FINTRACE assists users in preparing draft letters from facts they recorded.
Templates never fabricate statutory sections, circular numbers, transaction
references, or recovery guarantees, and clearly label unknown details as
"Not provided".
"""

from datetime import UTC, datetime
from decimal import Decimal

from app.models import Case, Complaint, Evidence, Transaction, User

DOCUMENT_CATALOG: tuple[dict, ...] = (
    {
        "document_type": "cybercrime_complaint",
        "code": "A",
        "title": "Cybercrime Complaint",
        "short_description": (
            "Report suspected financial cyber fraud through the National Cyber Crime "
            "Reporting Portal or Cyber Crime Cell."
        ),
        "default_recipient": (
            "The Nodal Officer / Cyber Crime Cell,\n"
            "National Cyber Crime Reporting Portal (https://cybercrime.gov.in)\n"
            "Helpline: 1930"
        ),
        "required_information": [
            "Complainant name & contact",
            "Incident date, time & description",
            "Transaction reference(s) & amount",
            "Prior 1930 / bank actions & evidence",
        ],
        "extra_fields": [
            {"key": "full_name", "label": "Full name", "section": "Personal information", "type": "text"},
            {"key": "phone", "label": "Contact number", "section": "Personal information", "type": "text"},
            {"key": "email", "label": "Email address", "section": "Personal information", "type": "text"},
            {"key": "address", "label": "Postal address (optional)", "section": "Personal information", "type": "textarea"},
            {"key": "is_ongoing", "label": "Is the fraud still ongoing?", "section": "Incident information", "type": "select", "options": ["No", "Yes", "Not sure"]},
            {"key": "bank_name", "label": "Your bank name", "section": "Transaction & bank", "type": "text"},
            {"key": "bank_contacted", "label": "Bank already contacted?", "section": "Prior reporting", "type": "select", "options": ["Not sure", "Yes", "No"]},
            {"key": "helpline_1930_contacted", "label": "1930 helpline contacted?", "section": "Prior reporting", "type": "select", "options": ["Not sure", "Yes", "No"]},
            {"key": "existing_complaint_ref", "label": "Existing acknowledgement / reference number (if any)", "section": "Prior reporting", "type": "text"},
        ],
        "attachments": [
            "Bank SMS / email debit alerts",
            "Account statement highlighting the suspected transaction(s)",
            "Screenshots of calls, messages, UPI collect requests, or phishing links",
            "Copy of government-issued photo ID (when required by portal/authority)",
        ],
    },
    {
        "document_type": "bank_fraud_complaint",
        "code": "B",
        "title": "Bank Fraud Complaint",
        "short_description": (
            "Notify your bank about a suspected fraudulent transaction and request "
            "investigation, account protection, and a written ticket reference."
        ),
        "default_recipient": (
            "The Branch Manager / Fraud Risk & Dispute Desk,\n"
            "{bank_name_or_placeholder}\n"
            "{branch_or_placeholder}"
        ),
        "required_information": [
            "Account holder name & contact",
            "Bank & branch details (if available)",
            "Disputed transaction(s) & amount",
            "Prior communication details",
        ],
        "extra_fields": [
            {"key": "full_name", "label": "Account holder full name", "section": "Personal information", "type": "text"},
            {"key": "phone", "label": "Contact number", "section": "Personal information", "type": "text"},
            {"key": "email", "label": "Email address", "section": "Personal information", "type": "text"},
            {"key": "bank_name", "label": "Bank name", "section": "Bank details", "type": "text"},
            {"key": "branch_name", "label": "Branch name / city (if known)", "section": "Bank details", "type": "text"},
            {"key": "account_last4", "label": "Account / card masked reference (last 4 digits only, optional)", "section": "Bank details", "type": "text"},
            {"key": "bank_contacted", "label": "Have you already contacted the bank?", "section": "Prior communication", "type": "select", "options": ["Not sure", "Yes", "No"]},
            {"key": "existing_complaint_ref", "label": "Existing bank ticket / 1930 / NCRP reference (if any)", "section": "Prior communication", "type": "text"},
        ],
        "attachments": [
            "Copy of bank SMS / email transaction alert",
            "Relevant bank statement extract showing transaction ID / UTR",
            "Acknowledgement from 1930 / cybercrime.gov.in (if already filed)",
            "Supporting chat or call-log screenshots",
        ],
    },
    {
        "document_type": "transaction_dispute_letter",
        "code": "C",
        "title": "Transaction Dispute Letter",
        "short_description": (
            "Formally dispute one or more reported transactions and request a written "
            "investigation and status update."
        ),
        "default_recipient": (
            "The Dispute Resolution / Chargeback Desk,\n"
            "{bank_name_or_placeholder}"
        ),
        "required_information": [
            "Account holder details",
            "Transaction reference(s), date & amount",
            "Authorisation status (unauthorised vs deceived)",
            "Supporting alerts / receipts",
        ],
        "extra_fields": [
            {"key": "full_name", "label": "Account holder full name", "section": "Personal information", "type": "text"},
            {"key": "phone", "label": "Contact number", "section": "Personal information", "type": "text"},
            {"key": "email", "label": "Email address", "section": "Personal information", "type": "text"},
            {"key": "bank_name", "label": "Issuing / payer bank name", "section": "Bank details", "type": "text"},
            {"key": "account_last4", "label": "Masked account or card reference (last 4 digits only, optional)", "section": "Bank details", "type": "text"},
            {"key": "existing_complaint_ref", "label": "Prior bank / 1930 reference (if any)", "section": "Prior reporting", "type": "text"},
        ],
        "attachments": [
            "Transaction receipt or debit SMS/email alert",
            "Account or card statement showing disputed entry",
            "Any merchant or caller correspondence",
            "Cybercrime complaint acknowledgement (if available)",
        ],
    },
    {
        "document_type": "upi_fraud_complaint",
        "code": "D",
        "title": "UPI Fraud Complaint",
        "short_description": (
            "Prepare a targeted complaint for suspected fraudulent UPI transactions "
            "with UTRs, timestamps, payer bank, and beneficiary details."
        ),
        "default_recipient": (
            "The Nodal / UPI Dispute Officer,\n"
            "{bank_name_or_placeholder}\n"
            "(Copy to Payment Service Provider App Support, if applicable)"
        ),
        "required_information": [
            "UPI UTR / transaction reference",
            "Timestamp & disputed amount",
            "UPI app & payer bank name",
            "Beneficiary VPA / name (if known)",
        ],
        "extra_fields": [
            {"key": "full_name", "label": "Complainant full name", "section": "Personal information", "type": "text"},
            {"key": "phone", "label": "Contact number", "section": "Personal information", "type": "text"},
            {"key": "email", "label": "Email address", "section": "Personal information", "type": "text"},
            {"key": "bank_name", "label": "Payer bank name", "section": "UPI details", "type": "text"},
            {"key": "upi_app_name", "label": "UPI application used (e.g. BHIM, GPay, PhonePe, Paytm)", "section": "UPI details", "type": "text"},
            {"key": "payer_vpa", "label": "Your UPI ID / VPA (optional)", "section": "UPI details", "type": "text"},
            {"key": "existing_complaint_ref", "label": "1930 / NCRP / UPI app reference (if any)", "section": "Prior reporting", "type": "text"},
        ],
        "attachments": [
            "UPI transaction detail screenshot showing 12-digit / bank UTR",
            "Payer bank debit SMS / statement entry",
            "Screenshot of deceptive collect request, QR code, or chat",
            "1930 helpline / cybercrime.gov.in reference (if available)",
        ],
    },
    {
        "document_type": "police_complaint",
        "code": "E",
        "title": "Police Complaint",
        "short_description": (
            "Prepare a formal written incident complaint for your local police station "
            "or district cyber cell."
        ),
        "default_recipient": (
            "The Station House Officer (SHO) / Officer-in-Charge,\n"
            "{police_station_or_placeholder}"
        ),
        "required_information": [
            "Complainant name, contact & address",
            "Chronological incident description",
            "Transaction & loss summary",
            "1930 / cybercrime portal reference (if filed)",
        ],
        "extra_fields": [
            {"key": "full_name", "label": "Complainant full name", "section": "Personal information", "type": "text"},
            {"key": "phone", "label": "Contact number", "section": "Personal information", "type": "text"},
            {"key": "email", "label": "Email address", "section": "Personal information", "type": "text"},
            {"key": "address", "label": "Residential address", "section": "Personal information", "type": "textarea"},
            {"key": "police_station", "label": "Police station / district cyber cell name", "section": "Authority details", "type": "text"},
            {"key": "bank_name", "label": "Bank name", "section": "Transaction & bank", "type": "text"},
            {"key": "existing_complaint_ref", "label": "1930 / cybercrime.gov.in acknowledgement number (if any)", "section": "Prior reporting", "type": "text"},
        ],
        "attachments": [
            "Printed copy of cybercrime.gov.in acknowledgement (if filed)",
            "Bank statement / transaction alerts signed or stamped where available",
            "Screenshots of chats, phone numbers, URLs, and call logs",
            "Copy of identity & address proof",
        ],
    },
    {
        "document_type": "follow_up_letter",
        "code": "F",
        "title": "Follow-Up Letter",
        "short_description": (
            "Request a formal status update on an already submitted bank, cybercrime, "
            "or police complaint."
        ),
        "default_recipient": (
            "The Grievance / Dispute Officer,\n"
            "{target_institution_or_placeholder}"
        ),
        "required_information": [
            "Original complaint reference & date",
            "Institution or authority contacted",
            "Previous responses / current status",
            "Requested status update",
        ],
        "extra_fields": [
            {"key": "full_name", "label": "Complainant full name", "section": "Personal information", "type": "text"},
            {"key": "phone", "label": "Contact number", "section": "Personal information", "type": "text"},
            {"key": "email", "label": "Email address", "section": "Personal information", "type": "text"},
            {"key": "target_institution", "label": "Institution or authority name", "section": "Original complaint", "type": "text"},
            {"key": "original_complaint_ref", "label": "Original complaint reference number", "section": "Original complaint", "type": "text"},
            {"key": "original_complaint_date", "label": "Original complaint filing date", "section": "Original complaint", "type": "text"},
            {"key": "previous_communication", "label": "Summary of previous communication / responses", "section": "Status & issue", "type": "textarea"},
            {"key": "unresolved_issue", "label": "Current unresolved issue", "section": "Status & issue", "type": "textarea"},
        ],
        "attachments": [
            "Copy of original complaint and acknowledgement receipt",
            "Copies of prior email/ticket replies received",
            "Updated bank statement if requested by the institution",
        ],
    },
    {
        "document_type": "escalation_letter",
        "code": "G",
        "title": "Escalation Letter",
        "short_description": (
            "Escalate an unresolved bank complaint to the bank's Nodal / Grievance "
            "Redressal Officer (or applicable escalation channel)."
        ),
        "default_recipient": (
            "The Principal Nodal Officer / Grievance Redressal Officer,\n"
            "{bank_name_or_placeholder}"
        ),
        "required_information": [
            "Original bank complaint reference & date",
            "Summary of prior responses",
            "Reason for escalation & timeline",
            "Requested resolution",
        ],
        "extra_fields": [
            {"key": "full_name", "label": "Complainant full name", "section": "Personal information", "type": "text"},
            {"key": "phone", "label": "Contact number", "section": "Personal information", "type": "text"},
            {"key": "email", "label": "Email address", "section": "Personal information", "type": "text"},
            {"key": "bank_name", "label": "Bank / institution name", "section": "Original bank complaint", "type": "text"},
            {"key": "original_complaint_ref", "label": "Original bank complaint reference", "section": "Original bank complaint", "type": "text"},
            {"key": "original_complaint_date", "label": "Original bank complaint date", "section": "Original bank complaint", "type": "text"},
            {"key": "previous_communication", "label": "Previous bank responses / ticket history", "section": "Escalation grounds", "type": "textarea"},
            {"key": "escalation_reason", "label": "Reason for escalation", "section": "Escalation grounds", "type": "textarea"},
        ],
        "attachments": [
            "Original bank complaint copy and acknowledgement number",
            "All prior bank correspondence / closure or interim replies",
            "Transaction statements and 1930 / NCRP acknowledgement",
        ],
    },
)

CATALOG_BY_TYPE: dict[str, dict] = {item["document_type"]: item for item in DOCUMENT_CATALOG}


def _val(value: object, fallback: str = "Not provided") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def _fmt_dt(dt: datetime | None) -> str:
    if dt is None:
        return "Not provided"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).strftime("%d %b %Y, %H:%M UTC")


def _fmt_money(amount: Decimal | float | None, currency: str = "INR") -> str:
    if amount is None:
        return "Not provided"
    return f"{currency} {Decimal(str(amount)):,.2f}"


def _auth_label(auth_type: str) -> str:
    return {
        "unauthorized": "Reported as unauthorised (victim states they did not approve it)",
        "authorized_deceived": "Reported as authorised under deception (victim approved after deception)",
        "unknown": "Authorisation status uncertain / not yet determined",
    }.get(auth_type, auth_type)


def _format_transactions_block(transactions: list[Transaction]) -> str:
    if not transactions:
        return "No individual financial transactions have been recorded in this case yet."
    lines: list[str] = []
    for idx, tx in enumerate(transactions, start=1):
        prov = "User-confirmed entry" if tx.verification_status == "user_confirmed" else f"Recorded ({tx.verification_status.replace('_', ' ')})"
        lines.extend(
            [
                f"  Transaction #{idx}:",
                f"    - Transaction ID / UTR : {_val(tx.utr_reference)}",
                f"    - Date & Time          : {_fmt_dt(tx.transaction_at)}",
                f"    - Amount & Direction   : {_fmt_money(tx.amount, tx.currency)} ({tx.direction})",
                f"    - Payment Channel      : {_val(tx.channel)}",
                f"    - Counterparty / Payee : {_val(tx.counterparty_name)}",
                f"    - Masked Account/VPA   : {_val(tx.counterparty_account_masked)}",
                f"    - Reported Status      : {tx.status}",
                f"    - Authorisation Claim  : {_auth_label(tx.authorization_type)}",
                f"    - Provenance           : {prov} (user-reported; not bank-verified)",
            ]
        )
    return "\n".join(lines)


def _format_evidence_block(evidence_items: list[Evidence]) -> str:
    if not evidence_items:
        return "No supporting files have been uploaded to the FINTRACE case yet."
    lines: list[str] = []
    for idx, ev in enumerate(evidence_items, start=1):
        lines.append(
            f"  {idx}. {ev.original_filename} [{ev.evidence_type.replace('_', ' ')}] "
            f"— SHA-256: {ev.sha256_hash[:16]}… ({ev.verification_status})"
            + (f" — {ev.description}" if ev.description else "")
        )
    return "\n".join(lines)


def _format_complaints_block(complaints: list[Complaint]) -> str:
    if not complaints:
        return "No formal complaints have been logged in the FINTRACE Complaint Tracker yet."
    lines: list[str] = []
    for idx, comp in enumerate(complaints, start=1):
        lines.append(
            f"  {idx}. {comp.channel.replace('_', ' ').title()} "
            f"({_val(comp.organisation_name, 'Organisation not specified')}) — "
            f"Ref: {_val(comp.reference_number)} · "
            f"Submission status: {comp.submission_status} · "
            f"Filed: {_fmt_dt(comp.filed_at)} · "
            f"Latest observed status: {_val(comp.official_status, 'Not yet observed')}"
        )
    return "\n".join(lines)


def build_prefill(
    *,
    document_type: str,
    user: User,
    case: Case,
    transactions: list[Transaction],
    evidence_items: list[Evidence],
    complaints: list[Complaint],
) -> dict:
    spec = CATALOG_BY_TYPE[document_type]

    latest_complaint = complaints[0] if complaints else None
    bank_complaint = next((c for c in complaints if c.channel in ("bank", "nodal_officer")), None)
    preferred_complaint = (
        bank_complaint
        if document_type in ("escalation_letter", "bank_fraud_complaint") and bank_complaint
        else latest_complaint
    )

    prefilled_answers: dict[str, str] = {
        "full_name": user.full_name or "",
        "phone": user.phone_e164 or "",
        "email": user.email or "",
        "address": "",
        "is_ongoing": "No",
        "bank_name": (bank_complaint.organisation_name if bank_complaint and bank_complaint.organisation_name else ""),
        "branch_name": "",
        "account_last4": "",
        "upi_app_name": "",
        "payer_vpa": "",
        "police_station": "",
        "bank_contacted": "Yes" if bank_complaint else "Not sure",
        "helpline_1930_contacted": "Not sure",
        "existing_complaint_ref": (preferred_complaint.reference_number if preferred_complaint and preferred_complaint.reference_number else ""),
        "target_institution": (preferred_complaint.organisation_name if preferred_complaint and preferred_complaint.organisation_name else ""),
        "original_complaint_ref": (preferred_complaint.reference_number if preferred_complaint and preferred_complaint.reference_number else ""),
        "original_complaint_date": (_fmt_dt(preferred_complaint.filed_at) if preferred_complaint and preferred_complaint.filed_at else ""),
        "previous_communication": (
            f"Latest recorded status: {preferred_complaint.official_status}"
            + (f" ({preferred_complaint.official_status_detail})" if preferred_complaint.official_status_detail else "")
            if preferred_complaint and preferred_complaint.official_status
            else ""
        ),
        "unresolved_issue": "",
        "escalation_reason": "",
    }

    missing_items: list[dict] = []
    if not (user.phone_e164 or "").strip():
        missing_items.append({"key": "phone", "label": "Contact phone number", "severity": "recommended"})
    if not transactions:
        missing_items.append({"key": "transactions", "label": "At least one transaction record (UTR, timestamp, amount)", "severity": "recommended"})
    elif not any((t.utr_reference or "").strip() for t in transactions):
        missing_items.append({"key": "utr_reference", "label": "Transaction UTR / reference number", "severity": "recommended"})
    if not evidence_items:
        missing_items.append({"key": "evidence", "label": "Supporting evidence (alerts, screenshots, statements)", "severity": "recommended"})
    if document_type in ("bank_fraud_complaint", "transaction_dispute_letter", "upi_fraud_complaint", "escalation_letter"):
        if not prefilled_answers["bank_name"]:
            missing_items.append({"key": "bank_name", "label": "Bank name", "severity": "recommended"})
    if document_type in ("follow_up_letter", "escalation_letter"):
        if not prefilled_answers["original_complaint_ref"]:
            missing_items.append({"key": "original_complaint_ref", "label": "Original complaint reference number", "severity": "recommended"})
        if not prefilled_answers["original_complaint_date"]:
            missing_items.append({"key": "original_complaint_date", "label": "Original complaint date", "severity": "recommended"})

    attachments_checklist = [
        {
            "label": item,
            "available": len(evidence_items) > 0,
            "note": (
                f"{len(evidence_items)} file(s) recorded in case"
                if evidence_items
                else "Not yet uploaded in Evidence centre"
            ),
        }
        for item in spec["attachments"]
    ]

    return {
        "document_type": document_type,
        "spec": spec,
        "case_summary": {
            "public_reference": case.public_reference,
            "title": case.title,
            "incident_type": case.incident_type,
            "fraud_channel": case.fraud_channel,
            "incident_occurred_at": case.incident_occurred_at.isoformat() if case.incident_occurred_at else None,
            "estimated_loss_amount": str(case.estimated_loss_amount) if case.estimated_loss_amount is not None else None,
            "currency": case.currency,
            "transaction_count": len(transactions),
            "evidence_count": len(evidence_items),
            "complaint_count": len(complaints),
        },
        "prefilled_answers": prefilled_answers,
        "missing_information": missing_items,
        "attachments_checklist": attachments_checklist,
    }


def render_document(
    *,
    document_type: str,
    user: User,
    case: Case,
    transactions: list[Transaction],
    evidence_items: list[Evidence],
    complaints: list[Complaint],
    answers: dict | None = None,
) -> dict:
    spec = CATALOG_BY_TYPE[document_type]
    ans = {k: ("" if v is None else str(v).strip()) for k, v in (answers or {}).items()}

    today_str = datetime.now(UTC).strftime("%d %b %Y")
    full_name = _val(ans.get("full_name") or user.full_name)
    phone = _val(ans.get("phone") or user.phone_e164)
    email = _val(ans.get("email") or user.email)
    address = _val(ans.get("address"))
    bank_name = _val(ans.get("bank_name"))
    branch_name = _val(ans.get("branch_name"))
    account_last4 = _val(ans.get("account_last4"))
    is_ongoing = _val(ans.get("is_ongoing"), "Not specified")
    existing_ref = _val(ans.get("existing_complaint_ref"))

    fraud_cat = case.incident_type.replace("_", " ").title()
    channel_label = case.fraud_channel.replace("_", " ").title()
    occurred_str = _fmt_dt(case.incident_occurred_at)
    narrative = _val(case.description, "No written narrative recorded yet.")
    reporting_summary = _val(case.reporting_details, "No prior reporting note recorded.")

    tx_total = sum((t.amount for t in transactions if t.direction == "debit"), Decimal("0"))
    loss_display = (
        _fmt_money(case.estimated_loss_amount, case.currency)
        if case.estimated_loss_amount is not None
        else (_fmt_money(tx_total, case.currency) if transactions else "Not provided / Unknown")
    )

    tx_block = _format_transactions_block(transactions)
    ev_block = _format_evidence_block(evidence_items)
    comp_block = _format_complaints_block(complaints)

    if document_type == "cybercrime_complaint":
        recipient = spec["default_recipient"]
        subject = (
            f"Report of Suspected Financial Cyber Fraud ({fraud_cat}) — "
            f"Reported Loss: {loss_display} [Ref: {case.public_reference}]"
        )
        body = f"""DRAFT — Please review all information before submitting this document to the relevant authority.
(Prepared with FINTRACE assistance. FINTRACE does not submit complaints to 1930 or cybercrime.gov.in on your behalf.)

Date: {today_str}

1. COMPLAINANT DETAILS
   Name    : {full_name}
   Phone   : {phone}
   Email   : {email}
   Address : {address}

2. RECIPIENT AUTHORITY
{recipient}

3. SUBJECT
   {subject}

4. INCIDENT INTRODUCTION
   I am writing to report a suspected financial cyber fraud incident involving {fraud_cat} through {channel_label}, occurring on or around {occurred_str}. The details below reflect the facts as experienced and recorded by me; they are submitted for official verification and investigation.

5. CHRONOLOGICAL INCIDENT DESCRIPTION (USER-REPORTED FACTS)
   {narrative}

   Ongoing fraud status: {is_ongoing}

6. FRAUD CATEGORY & CONTACT CHANNEL
   - Reported Category : {fraud_cat}
   - Contact Channel   : {channel_label}
   - Case Reference    : {case.public_reference}

7. TRANSACTION INFORMATION
   - Payer / Affected Bank : {bank_name}
{tx_block}

8. FINANCIAL LOSS INFORMATION
   - Reported / Estimated Loss : {loss_display}
   - Note: Reported figures are based on complainant records and alerts and remain subject to bank verification.

9. ACTIONS ALREADY TAKEN
   - Bank contacted       : {_val(ans.get("bank_contacted"), "Not specified")}
   - 1930 helpline called : {_val(ans.get("helpline_1930_contacted"), "Not specified")}
   - Existing reference   : {existing_ref}
   - Additional notes     : {reporting_summary}
   - Logged complaints:
{comp_block}

10. EVIDENCE AVAILABLE
{ev_block}

11. REQUESTED ASSISTANCE AND INVESTIGATION
    I respectfully request the authority to:
    a) Register and investigate this suspected financial cyber fraud incident.
    b) Coordinate with the concerned bank(s) and payment intermediaries to trace and freeze any remaining proceeds where technically and legally feasible.
    c) Issue an official complaint acknowledgement / reference number for my bank dispute records.
    (Note: No recovery of funds is guaranteed, and this draft does not assert legal conclusions.)

12. DECLARATION
    I declare that the information stated above is true and accurate to the best of my knowledge and belief.

13. DATE AND SIGNATURE
    Date      : {today_str}
    Signature : ___________________________
    Name      : {full_name}
"""

    elif document_type == "bank_fraud_complaint":
        recipient = (
            "The Branch Manager / Fraud Risk & Dispute Desk,\n"
            f"{bank_name if bank_name != 'Not provided' else '[Bank Name — Not provided]'}\n"
            f"{branch_name if branch_name != 'Not provided' else '[Branch Name — Not provided]'}"
        )
        subject = (
            f"Report of Suspected Fraudulent Transaction(s) and Request for Investigation — "
            f"Disputed Amount: {loss_display}"
        )
        body = f"""DRAFT — Please review all information before submitting this document to your bank.
(Prepared with FINTRACE assistance. FINTRACE does not transmit complaints to any bank.)

Date: {today_str}

1. ACCOUNT HOLDER DETAILS
   Name                  : {full_name}
   Phone                 : {phone}
   Email                 : {email}
   Account/Card (Masked) : {account_last4}

2. BANK AND BRANCH INFORMATION
   Bank Name   : {bank_name}
   Branch Name : {branch_name}

3. SUBJECT
   {subject}

4. DESCRIPTION OF SUSPECTED FRAUD (USER-REPORTED FACTS)
   Incident Category : {fraud_cat} (via {channel_label})
   Occurred At       : {occurred_str}
   Account Holder Statement:
   {narrative}

5. TRANSACTION DETAILS
{tx_block}

6. AMOUNT DISPUTED
   Total Reported Disputed Amount : {loss_display}

7. PREVIOUS COMMUNICATION DETAILS
   - Bank previously contacted : {_val(ans.get("bank_contacted"), "Not specified")}
   - Prior 1930 / NCRP / Bank Ref : {existing_ref}
   - Notes : {reporting_summary}
   - Recorded complaints:
{comp_block}

8. REQUEST TO INVESTIGATE THE TRANSACTION(S)
   I request the bank to formally log this dispute, investigate the suspected fraudulent transaction(s) listed above, and preserve relevant transaction and routing logs.

9. REQUEST FOR APPROPRIATE ACCOUNT PROTECTION & BANKING PROCEDURES
   Please take appropriate protective action on my account/payment credentials as per applicable banking procedures (such as placing a temporary hold, blocking compromised instruments, or initiating beneficiary-bank recall/lien requests where permitted).

10. REQUEST FOR ACKNOWLEDGEMENT AND COMPLAINT REFERENCE
    Kindly provide a written acknowledgement along with the official bank complaint/ticket reference number and expected review timeline. I have also been advised to report this incident to the national cybercrime helpline 1930 and https://cybercrime.gov.in if not already completed.

    Supporting Evidence Available:
{ev_block}

11. DATE AND SIGNATURE
    Date      : {today_str}
    Signature : ___________________________
    Name      : {full_name}
"""

    elif document_type == "transaction_dispute_letter":
        recipient = (
            "The Dispute Resolution / Chargeback Cell,\n"
            f"{bank_name if bank_name != 'Not provided' else '[Bank / Card Issuer Name — Not provided]'}"
        )
        subject = f"Formal Transaction Dispute Request — {loss_display} [Case Ref: {case.public_reference}]"
        body = f"""DRAFT — Please review all information before submitting this dispute letter.

Date: {today_str}

To:
{recipient}

From:
Name                  : {full_name}
Phone                 : {phone}
Email                 : {email}
Account/Card (Masked) : {account_last4}

SUBJECT: {subject}

Dear Sir / Madam,

1. PURPOSE OF DISPUTE
   I am writing to formally dispute the transaction(s) detailed below, which occurred on or around {occurred_str} and are suspected to involve {fraud_cat}.

2. DISPUTED TRANSACTION DETAILS
{tx_block}

   Total Disputed Amount : {loss_display}

3. FACTUAL STATEMENT (USER-REPORTED)
   {narrative}

4. SUPPORTING EVIDENCE AVAILABLE
{ev_block}

5. PRIOR REPORTING
   Existing Reference (1930 / Cybercrime / Bank): {existing_ref}

6. REQUESTED ACTION
   - Please register this formal transaction dispute and initiate investigation/chargeback procedures as applicable.
   - Please provide a written dispute acknowledgement and reference number.
   - Please share any documentation required from me to process the dispute.

Yours faithfully,

___________________________
{full_name}
Date: {today_str}
"""

    elif document_type == "upi_fraud_complaint":
        upi_app = _val(ans.get("upi_app_name"))
        payer_vpa = _val(ans.get("payer_vpa"))
        recipient = (
            "The Nodal Officer / UPI Dispute Resolution Team,\n"
            f"{bank_name if bank_name != 'Not provided' else '[Payer Bank Name — Not provided]'}"
        )
        subject = f"UPI Fraud & Suspected Transaction Complaint — {loss_display} [Ref: {case.public_reference}]"
        body = f"""DRAFT — Please review all information before submitting this UPI complaint.

Date: {today_str}

To:
{recipient}

Complainant:
Name       : {full_name}
Phone      : {phone}
Email      : {email}
Payer Bank : {bank_name}
UPI App    : {upi_app}
Payer VPA  : {payer_vpa}

SUBJECT: {subject}

1. INCIDENT DESCRIPTION
   On or around {occurred_str}, the following suspected fraudulent UPI transaction(s) occurred via {channel_label}:
   {narrative}

2. UPI TRANSACTION DETAILS (INCLUDING UTR, TIMESTAMPS & BENEFICIARY)
{tx_block}

   Total Reported Disputed Amount : {loss_display}

3. PRIOR ACTIONS & REPORTING
   - Existing 1930 / cybercrime.gov.in / App Reference : {existing_ref}
   - Notes : {reporting_summary}

4. SUPPORTING EVIDENCE
{ev_block}

5. REQUESTED INVESTIGATION
   I request the payer bank and concerned UPI payment service provider to:
   a) Investigate the UPI transaction(s) listed above using the UTR reference(s).
   b) Coordinate with the beneficiary bank/PSP regarding the recipient account/VPA under applicable UPI dispute procedures.
   c) Provide a written complaint acknowledgement and tracking reference.

   (Note: I understand that submitting this letter does not guarantee recovery and that national reporting should also be completed at 1930 / https://cybercrime.gov.in.)

Date: {today_str}
Signature: ___________________________
Name: {full_name}
"""

    elif document_type == "police_complaint":
        station = _val(ans.get("police_station"), "[Local Police Station / Cyber Cell — Not provided]")
        recipient = (
            "The Station House Officer (SHO) / Officer-in-Charge,\n"
            f"{station}"
        )
        subject = f"Written Complaint Regarding Suspected Financial Cyber Fraud — {loss_display} [Ref: {case.public_reference}]"
        body = f"""DRAFT — Please review all information before submitting this complaint at the police station.

Date: {today_str}

To:
{recipient}

Complainant Details:
Name    : {full_name}
Phone   : {phone}
Email   : {email}
Address : {address}

SUBJECT: {subject}

Respected Sir / Madam,

1. BRIEF SUMMARY OF INCIDENT
   I wish to lodge a written complaint regarding a suspected financial fraud ({fraud_cat}) committed against me via {channel_label} on or around {occurred_str}, involving a reported loss of {loss_display}.

2. DETAILED FACTS AS REPORTED BY COMPLAINANT
   {narrative}

3. TRANSACTION & BANK DETAILS
   Payer Bank: {bank_name}
{tx_block}

4. PRIOR CYBERCRIME / BANK REPORTING
   - 1930 / NCRP Acknowledgement : {existing_ref}
   - Additional Reporting Notes   : {reporting_summary}
{comp_block}

5. EVIDENCE ENCLOSED / AVAILABLE
{ev_block}

6. REQUEST
   I request you to kindly register my complaint, conduct an investigation in accordance with applicable law, and issue an official acknowledgement / copy of the registered complaint for bank coordination.

   I affirm that the facts stated above are accurate to the best of my knowledge.

Yours faithfully,

___________________________
{full_name}
Date: {today_str}
"""

    elif document_type == "follow_up_letter":
        inst = _val(ans.get("target_institution") or (bank_name if bank_name != "Not provided" else ""), "[Institution / Authority — Not provided]")
        orig_ref = _val(ans.get("original_complaint_ref") or existing_ref)
        orig_date = _val(ans.get("original_complaint_date"))
        prev_comm = _val(ans.get("previous_communication"), "No prior response recorded.")
        unresolved = _val(ans.get("unresolved_issue"), f"Resolution and status update on disputed amount ({loss_display}).")
        recipient = f"The Grievance / Dispute Officer,\n{inst}"
        subject = f"Follow-Up on Pending Fraud Complaint — Ref: {orig_ref} [Case: {case.public_reference}]"
        body = f"""DRAFT — Please review all information before sending this follow-up letter.

Date: {today_str}

To:
{recipient}

From:
Name  : {full_name}
Phone : {phone}
Email : {email}

SUBJECT: {subject}

Dear Sir / Madam,

1. ORIGINAL COMPLAINT REFERENCE
   - Institution / Authority  : {inst}
   - Original Complaint Ref   : {orig_ref}
   - Original Complaint Date  : {orig_date}
   - Disputed Amount          : {loss_display}

2. PREVIOUS COMMUNICATION & OBSERVED STATUS
   {prev_comm}
   Logged Complaints & Observations:
{comp_block}

3. CURRENT UNRESOLVED ISSUE
   {unresolved}

   Associated Transaction(s):
{tx_block}

4. REQUESTED UPDATE
   Kindly provide a written status update on the investigation of the above complaint, including current findings, next steps, and an expected timeframe for response.

Yours faithfully,

___________________________
{full_name}
Date: {today_str}
"""

    else:  # escalation_letter
        orig_ref = _val(ans.get("original_complaint_ref") or existing_ref)
        orig_date = _val(ans.get("original_complaint_date"))
        prev_comm = _val(ans.get("previous_communication"), "No satisfactory resolution received to date.")
        esc_reason = _val(
            ans.get("escalation_reason"),
            "The original bank complaint remains unresolved or lacks a substantive written response.",
        )
        recipient = (
            "The Principal Nodal Officer / Grievance Redressal Officer,\n"
            f"{bank_name if bank_name != 'Not provided' else '[Bank Name — Not provided]'}"
        )
        subject = f"Escalation of Unresolved Bank Fraud Complaint — Ref: {orig_ref} [Case: {case.public_reference}]"
        body = f"""DRAFT — Please review all information before escalating this complaint.
(Verify your bank's published Grievance Redressal escalation matrix before sending.)

Date: {today_str}

To:
{recipient}

From:
Name                  : {full_name}
Phone                 : {phone}
Email                 : {email}
Account/Card (Masked) : {account_last4}

SUBJECT: {subject}

Dear Sir / Madam,

1. ORIGINAL BANK COMPLAINT DETAILS
   - Bank Name               : {bank_name}
   - Original Complaint Ref  : {orig_ref}
   - Original Complaint Date : {orig_date}
   - Incident Occurred Date  : {occurred_str}
   - Disputed Amount         : {loss_display}

2. PREVIOUS RESPONSES & COMMUNICATION HISTORY
   {prev_comm}
{comp_block}

3. REASON FOR ESCALATION
   {esc_reason}

4. SUMMARY OF INCIDENT & TRANSACTIONS
   {narrative}

{tx_block}

5. SUPPORTING EVIDENCE
{ev_block}

6. REQUESTED RESOLUTION
   I request an escalated review of the original complaint by the Grievance Redressal / Nodal Officer and a reasoned written response. Where applicable under your bank's grievance redressal policy and RBI's Integrated Ombudsman escalation eligibility rules, I reserve the right to seek further escalation if the matter remains unresolved.

   (Note: This draft does not assert legal liability or guarantee recovery of funds.)

Yours faithfully,

___________________________
{full_name}
Date: {today_str}
"""

    prefill_info = build_prefill(
        document_type=document_type,
        user=user,
        case=case,
        transactions=transactions,
        evidence_items=evidence_items,
        complaints=complaints,
    )

    return {
        "document_type": document_type,
        "title": f"{spec['title']} — {case.public_reference}",
        "recipient": recipient,
        "subject": subject,
        "content": body.strip() + "\n",
        "attachments_checklist": prefill_info["attachments_checklist"],
    }
