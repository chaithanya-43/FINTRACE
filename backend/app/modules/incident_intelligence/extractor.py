"""Deterministic extraction of facts from a case narrative.

Extraction output is always marked as unconfirmed. Anything taken from free
text must be confirmed by the user before it is treated as recorded fact.
"""

import re

from app.models import Case, Transaction

_AMOUNT_PATTERN = re.compile(
    r"(?:rs\.?|inr|₹)\s?([0-9][0-9,]*(?:\.[0-9]{1,2})?)", re.I
)
_UTR_PATTERN = re.compile(r"\b(\d{12})\b")
_UPI_PATTERN = re.compile(r"\b([a-zA-Z0-9._-]{2,}@[a-zA-Z]{2,})\b")
_PHONE_PATTERN = re.compile(r"(?:\+91[\s-]?)?\b([6-9]\d{9})\b")
_URL_PATTERN = re.compile(r"https?://[^\s<>\"']+", re.I)
_DATE_HINT = re.compile(
    r"\b(yesterday|today|this morning|last night|last week|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
    re.I,
)


def extract(description: str) -> dict:
    text = description or ""
    amounts = []
    for raw in _AMOUNT_PATTERN.findall(text):
        try:
            amounts.append(float(raw.replace(",", "")))
        except ValueError:
            continue

    facts = {
        "amounts_mentioned": amounts,
        "utr_references": sorted(set(_UTR_PATTERN.findall(text))),
        "upi_ids": sorted(set(_UPI_PATTERN.findall(text))),
        "phone_numbers": sorted(set(_PHONE_PATTERN.findall(text))),
        "links": sorted(set(_URL_PATTERN.findall(text))),
        "date_hints": sorted({item for item in _DATE_HINT.findall(text)}),
    }
    return facts


def missing_information(
    case: Case, transactions: list[Transaction], evidence_count: int, extracted: dict
) -> list[str]:
    missing: list[str] = []
    if not case.description or len((case.description or "").strip()) < 20:
        missing.append("A description of what happened (at least a couple of sentences).")
    if case.incident_type == "unknown":
        missing.append("The type of fraud, if you can tell.")
    if case.fraud_channel == "unknown":
        missing.append("How you were contacted (call, UPI, WhatsApp, card, app).")
    if case.incident_occurred_at is None:
        missing.append("When the incident happened (date and approximate time).")
    if case.estimated_loss_amount is None and not transactions:
        missing.append("The amount lost, or at least one transaction.")
    if not transactions:
        missing.append("Transaction details: amount, date, and UTR or reference if available.")
    if evidence_count == 0:
        missing.append("Evidence: bank alerts, screenshots or a statement.")
    if not extracted["utr_references"] and transactions:
        missing.append("UTR or reference numbers for the transactions, if your bank shows them.")
    return missing


def suggested_next_steps(case: Case, evidence_count: int) -> list[str]:
    steps = [
        "If money is still moving, call the 1930 cybercrime helpline now.",
        "Report the incident at https://cybercrime.gov.in and keep the acknowledgement number.",
        "Contact your bank's fraud desk using the number on your card or in the app.",
    ]
    if evidence_count == 0:
        steps.append("Upload the bank alerts and screenshots as evidence before editing them.")
    if case.internal_status in ("intake", "collecting_evidence"):
        steps.append("Fill in the missing information so a regulatory assessment can be run.")
    steps.append("Record what each organisation tells you as a status observation.")
    return steps
