"""Transaction management (case sub-module)."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import Conflict, InvalidRequest, NotFound
from app.models import Case, Transaction, User
from app.modules.audit import service as audit
from app.modules.cases import policies
from app.utils.enums import AuditAction
from app.utils.sensitive import assert_no_authentication_secrets

_EDITABLE_FIELDS = {
    "amount",
    "currency",
    "transaction_at",
    "direction",
    "authorization_type",
    "channel",
    "counterparty_name",
    "counterparty_account_masked",
    "utr_reference",
    "status",
    "verification_status",
    "notes",
}


def list_transactions(db: Session, case_id: uuid.UUID) -> list[Transaction]:
    statement = (
        select(Transaction)
        .where(Transaction.case_id == case_id)
        .order_by(Transaction.transaction_at.desc().nullslast(), Transaction.created_at.desc())
    )
    return list(db.scalars(statement))


def create_transaction(
    db: Session, *, case: Case, user: User, data: dict
) -> Transaction:
    if case.is_archived:
        raise Conflict("Archived cases are read-only.")
    assert_no_authentication_secrets(data.get("notes"))

    payload = dict(data)
    payload["currency"] = (payload.get("currency") or "INR").upper()
    payload.setdefault("source", "user")
    payload.setdefault("recorded_by_user_id", user.id)

    transaction = Transaction(case_id=case.id, **payload)
    db.add(transaction)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        if "uq_transactions_case_utr" in str(exc.orig):
            raise Conflict(
                "A transaction with this UTR reference already exists in this case.",
                code="duplicate_utr",
            ) from exc
        raise

    _refresh_case_totals(db, case)
    audit.record(
        db,
        action=AuditAction.TRANSACTION_CREATED,
        actor=user,
        case_id=case.id,
        entity_type="transaction",
        entity_id=transaction.id,
        after=audit.snapshot(transaction),
    )
    db.commit()
    db.refresh(transaction)
    return transaction


def update_transaction(
    db: Session, *, case: Case, transaction_id: uuid.UUID, user: User, data: dict
) -> Transaction:
    transaction = db.get(Transaction, transaction_id)
    if transaction is None or transaction.case_id != case.id:
        raise NotFound("Transaction not found in this case.")
    if case.is_archived:
        raise Conflict("Archived cases are read-only.")

    changes = {key: value for key, value in data.items() if value is not None}
    if not changes:
        return transaction
    assert_no_authentication_secrets(changes.get("notes"))

    before = audit.snapshot(transaction)
    for field, value in changes.items():
        if field not in _EDITABLE_FIELDS:
            raise InvalidRequest(f"Field '{field}' cannot be edited.")
        if field == "currency":
            value = value.upper()
        setattr(transaction, field, value)
    transaction.updated_at = datetime.now(UTC)

    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        if "uq_transactions_case_utr" in str(exc.orig):
            raise Conflict(
                "A transaction with this UTR reference already exists in this case.",
                code="duplicate_utr",
            ) from exc
        raise

    _refresh_case_totals(db, case)
    audit.record(
        db,
        action=AuditAction.TRANSACTION_UPDATED,
        actor=user,
        case_id=case.id,
        entity_type="transaction",
        entity_id=transaction.id,
        before=before,
        after=audit.snapshot(transaction),
    )
    db.commit()
    db.refresh(transaction)
    return transaction


def _refresh_case_totals(db: Session, case: Case) -> None:
    """Derive the case loss estimate from recorded debits when none was entered."""
    transactions = list(
        db.scalars(select(Transaction).where(Transaction.case_id == case.id))
    )
    if case.estimated_loss_amount is None:
        derived = policies.derive_estimated_loss(transactions)
        if derived is not None:
            case.estimated_loss_amount = derived
    case.completeness_status = policies.compute_completeness(case, transactions)
    case.updated_at = datetime.now(UTC)
