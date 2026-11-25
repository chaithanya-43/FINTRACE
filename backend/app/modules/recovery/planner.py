"""Deterministic recovery roadmap planning.

Recommendations are rules of thumb for the user's own actions. They are not
legal advice and FINTRACE performs none of them on the user's behalf.
"""

from datetime import UTC, datetime, timedelta

from app.models import Case, Transaction
from app.utils.enums import RecoveryPriority, RecoveryStatus

EMERGENCY_GUIDANCE = [
    "If money is still moving or your account is compromised, call the national "
    "cybercrime helpline 1930 now.",
    "Report the incident at https://cybercrime.gov.in as soon as possible and keep "
    "the acknowledgement number.",
    "Contact your bank's fraud desk to flag the transaction and ask about a freeze "
    "or hold. FINTRACE does not contact your bank.",
    "Never share an OTP, UPI PIN, card CVV or banking password with anyone, including "
    "anyone claiming to help with recovery.",
]

_URGENT_WINDOW_HOURS = 72


def _hours_since_incident(case: Case) -> float | None:
    if case.incident_occurred_at is None:
        return None
    occurred = case.incident_occurred_at
    if occurred.tzinfo is None:
        occurred = occurred.replace(tzinfo=UTC)
    return (datetime.now(UTC) - occurred).total_seconds() / 3600


def recommend(
    case: Case,
    transactions: list[Transaction],
    evidence_count: int,
    now: datetime | None = None,
) -> list[dict]:
    moment = now or datetime.now(UTC)
    hours = _hours_since_incident(case)
    urgent = hours is None or hours <= _URGENT_WINDOW_HOURS
    unauthorized = any(item.authorization_type == "unauthorized" for item in transactions)
    card_channel = case.fraud_channel == "card" or any(
        item.channel == "card" for item in transactions
    )

    actions: list[dict] = [
        {
            "action_type": "call_helpline",
            "title": "Call the 1930 cybercrime helpline",
            "description": "Report the fraud on the national helpline and note the reference given.",
            "instructions": "Dial 1930. Have transaction dates, amounts and UTR references ready.",
            "priority": RecoveryPriority.CRITICAL.value if urgent else RecoveryPriority.HIGH.value,
            "due_at": moment + timedelta(hours=6),
        },
        {
            "action_type": "report_cybercrime",
            "title": "File the report on cybercrime.gov.in",
            "description": "Submit the incident on the national cybercrime reporting portal yourself.",
            "instructions": (
                "FINTRACE cannot submit this for you. Attach the evidence you uploaded "
                "and copy the acknowledgement number back into the complaint record."
            ),
            "priority": RecoveryPriority.CRITICAL.value if urgent else RecoveryPriority.HIGH.value,
            "due_at": moment + timedelta(hours=24),
        },
        {
            "action_type": "contact_bank",
            "title": "Notify your bank's fraud desk",
            "description": "Ask the bank to flag the transaction and explain the dispute process.",
            "instructions": (
                "Use the number printed on your card or in the bank app, not a number "
                "from the suspect conversation."
            ),
            "priority": RecoveryPriority.HIGH.value,
            "due_at": moment + timedelta(hours=12 if urgent else 48),
        },
    ]

    if unauthorized:
        actions.append(
            {
                "action_type": "freeze_account",
                "title": "Ask for the account to be frozen or blocked",
                "description": "Unauthorised debits were recorded, so request a block on further debits.",
                "instructions": "Ask the bank in writing and keep the ticket number.",
                "priority": RecoveryPriority.CRITICAL.value,
                "due_at": moment + timedelta(hours=6),
            }
        )

    if card_channel:
        actions.append(
            {
                "action_type": "chargeback_request",
                "title": "Raise a chargeback or dispute with the card issuer",
                "description": "Card transactions may be eligible for a dispute or chargeback.",
                "instructions": "Ask the issuer for the dispute form and the deadline to file it.",
                "priority": RecoveryPriority.MEDIUM.value,
                "due_at": moment + timedelta(days=7),
            }
        )

    if evidence_count == 0:
        actions.append(
            {
                "action_type": "preserve_evidence",
                "title": "Upload the transaction alerts, screenshots and messages",
                "description": "Evidence is currently missing from this case.",
                "instructions": (
                    "Upload bank SMS or email alerts, chat screenshots and the transaction "
                    "statement. Do not edit the files before uploading."
                ),
                "priority": RecoveryPriority.HIGH.value,
                "due_at": moment + timedelta(days=2),
            }
        )

    actions.extend(
        [
            {
                "action_type": "prepare_complaint",
                "title": "Prepare the written complaint",
                "description": "Assemble the case facts and reference numbers for the bank or police.",
                "instructions": (
                    "Copy the prepared complaint information from the complaint section "
                    "and submit it through the organisation's own channel."
                ),
                "priority": RecoveryPriority.MEDIUM.value,
                "due_at": moment + timedelta(days=3),
            },
            {
                "action_type": "follow_up",
                "title": "Follow up and record the official status",
                "description": "Re-check each complaint and record what the organisation says.",
                "instructions": (
                    "Add a status observation rather than editing older ones, so the "
                    "history of what you were told stays intact."
                ),
                "priority": RecoveryPriority.MEDIUM.value,
                "due_at": moment + timedelta(days=7),
            },
        ]
    )

    return actions


def is_case_urgent(case: Case) -> bool:
    hours = _hours_since_incident(case)
    return case.internal_status != "closed" and (hours is None or hours <= _URGENT_WINDOW_HOURS)


def headline(case: Case) -> str:
    if case.internal_status == "closed":
        return "This case is closed. Keep the reference and evidence for any later follow-up."
    if is_case_urgent(case):
        return (
            "Active fraud guidance: call 1930 and report on cybercrime.gov.in now, "
            "before working through the rest of the roadmap."
        )
    return "Work through the open actions below and record each official response as it arrives."


OPEN_STATUSES = (
    RecoveryStatus.PENDING.value,
    RecoveryStatus.IN_PROGRESS.value,
    RecoveryStatus.BLOCKED.value,
)
