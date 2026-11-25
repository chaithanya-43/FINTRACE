"""Incident analysis orchestration.

The provider is intentionally deterministic. No external model is configured in
this prototype, and the response says so instead of implying one was used.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Case, Evidence, Transaction, User
from app.modules.incident_intelligence import classifier, extractor


def analyse(db: Session, *, case: Case, user: User) -> dict:  # noqa: ARG001 - user reserved for future per-user redaction
    transactions = list(
        db.scalars(select(Transaction).where(Transaction.case_id == case.id))
    )
    evidence_count = int(
        db.scalar(
            select(func.count())
            .select_from(Evidence)
            .where(Evidence.case_id == case.id)
        )
        or 0
    )

    description = case.description or ""
    classification = classifier.classify(
        description,
        incident_type=case.incident_type,
        fraud_channel=case.fraud_channel,
    )
    extracted = extractor.extract(description)

    facts: list[dict] = []
    for amount in extracted["amounts_mentioned"]:
        facts.append(
            {
                "fact": "amount_mentioned",
                "value": amount,
                "provenance": "extracted_from_description",
                "confirmed": False,
            }
        )
    for utr in extracted["utr_references"]:
        facts.append(
            {
                "fact": "utr_reference",
                "value": utr,
                "provenance": "extracted_from_description",
                "confirmed": any(t.utr_reference == utr for t in transactions),
            }
        )
    for upi_id in extracted["upi_ids"]:
        facts.append(
            {
                "fact": "upi_id",
                "value": upi_id,
                "provenance": "extracted_from_description",
                "confirmed": False,
            }
        )
    for link in extracted["links"]:
        facts.append(
            {
                "fact": "link",
                "value": link,
                "provenance": "extracted_from_description",
                "confirmed": False,
            }
        )

    for transaction in transactions:
        facts.append(
            {
                "fact": "recorded_transaction",
                "value": {
                    "amount": float(transaction.amount),
                    "currency": transaction.currency,
                    "at": transaction.transaction_at.isoformat()
                    if transaction.transaction_at
                    else None,
                },
                "provenance": transaction.source,
                "confirmed": transaction.verification_status == "user_confirmed",
            }
        )

    for field in ("incident_type", "fraud_channel", "estimated_loss_amount", "incident_occurred_at"):
        value = getattr(case, field)
        facts.append(
            {
                "fact": field,
                "value": value.isoformat() if hasattr(value, "isoformat") else value,
                "provenance": "user_provided",
                "confirmed": True,
            }
        )

    summary_bits = [
        f"Case {case.public_reference}",
        f"recorded as {case.incident_type.replace('_', ' ')} via {case.fraud_channel.replace('_', ' ')}",
        f"with {len(transactions)} transaction(s) and {evidence_count} evidence file(s)",
    ]

    return {
        "case_id": case.id,
        "engine": "deterministic-keyword-v1",
        "provider_configured": False,
        "summary": (
            ", ".join(summary_bits)
            + ". Analysis is limited to pattern matching over the recorded text; "
            "no external AI provider is configured in this deployment."
        ),
        "suggested_incident_type": classification["suggested_incident_type"],
        "suggested_fraud_channel": classification["suggested_fraud_channel"],
        "confidence_note": classification["confidence_note"],
        "extracted_facts": facts,
        "missing_information": extractor.missing_information(
            case, transactions, evidence_count, extracted
        ),
        "suggested_next_steps": extractor.suggested_next_steps(case, evidence_count),
        "fact_provenance": {
            "user_provided": "Facts the user entered or confirmed.",
            "extracted_from_description": (
                "Pattern-matched from free text; unconfirmed until the user confirms it."
            ),
            "evidence": "Derived from an uploaded file.",
            "extracted": "Produced by automated extraction.",
        },
    }
