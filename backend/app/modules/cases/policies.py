"""Case lifecycle and completeness policies (pure functions)."""

from decimal import Decimal

from app.models import Case, Transaction
from app.utils.enums import CaseStatus, CompletenessStatus, FRAUD_CATEGORIES, FRAUD_CHANNELS

# Forward transitions are allowed; closing is reachable from any active state.
_TRANSITIONS: dict[str, set[str]] = {
    CaseStatus.INTAKE: {CaseStatus.COLLECTING_EVIDENCE, CaseStatus.CLOSED},
    CaseStatus.COLLECTING_EVIDENCE: {CaseStatus.ASSESSMENT, CaseStatus.CLOSED},
    CaseStatus.ASSESSMENT: {CaseStatus.RECOVERY, CaseStatus.COLLECTING_EVIDENCE, CaseStatus.CLOSED},
    CaseStatus.RECOVERY: {CaseStatus.CLOSED, CaseStatus.ASSESSMENT},
    CaseStatus.CLOSED: set(),
}


class InvalidTransition(ValueError):
    pass


def assert_transition_allowed(current: str, target: str) -> None:
    if target not in _TRANSITIONS.get(current, set()):
        allowed = ", ".join(sorted(_TRANSITIONS.get(current, set()))) or "none"
        raise InvalidTransition(
            f"Cannot move a case from '{current}' to '{target}'. Allowed: {allowed}."
        )


def normalise_incident_type(value: str) -> str:
    value = value.strip().lower()
    return value if value in FRAUD_CATEGORIES else "unknown"


def normalise_fraud_channel(value: str) -> str:
    value = value.strip().lower()
    return value if value in FRAUD_CHANNELS else "unknown"


def compute_completeness(case: Case, transactions: list[Transaction]) -> str:
    """Derive completeness from what is actually recorded.

    Never used to produce a regulatory result; it only tells the user (and the
    investigator queue) how much of the intake is filled in.
    """
    signals = [
        bool(case.description and len(case.description.strip()) >= 20),
        case.incident_type != "unknown",
        case.fraud_channel != "unknown",
        case.incident_occurred_at is not None,
        case.estimated_loss_amount is not None and case.estimated_loss_amount > 0,
        len(transactions) > 0,
    ]
    if all(signals):
        return CompletenessStatus.COMPLETE.value
    if any(signals):
        return CompletenessStatus.PARTIAL.value
    return CompletenessStatus.INCOMPLETE.value


def derive_estimated_loss(transactions: list[Transaction]) -> Decimal | None:
    amounts = [t.amount for t in transactions if t.direction == "debit"]
    if not amounts:
        return None
    return sum(amounts, Decimal("0"))
