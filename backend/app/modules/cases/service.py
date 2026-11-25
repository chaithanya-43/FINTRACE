"""Case lifecycle service."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import Conflict, InvalidRequest, NotFound
from app.models import Case, Complaint, Evidence, RecoveryAction, RegulatoryAssessment, Transaction, User
from app.modules.audit import service as audit
from app.modules.cases import policies, reference
from app.utils.enums import AuditAction, CaseStatus
from app.utils.sensitive import assert_no_authentication_secrets


def create_case(db: Session, *, user: User, data: dict) -> Case:
    assert_no_authentication_secrets(data.get("description"), data.get("reporting_details"))

    payload = dict(data)
    payload["incident_type"] = policies.normalise_incident_type(
        payload.get("incident_type") or "unknown"
    )
    payload["fraud_channel"] = policies.normalise_fraud_channel(
        payload.get("fraud_channel") or "unknown"
    )
    if payload.get("currency"):
        payload["currency"] = payload["currency"].upper()

    case = Case(
        **payload,
        created_by_user_id=user.id,
        public_reference=reference.generate_public_reference(),
        internal_status=CaseStatus.INTAKE.value,
        completeness_status="incomplete",
    )

    for attempt in range(5):
        db.add(case)
        try:
            db.flush()
            break
        except IntegrityError as exc:
            db.rollback()
            if "public_reference" not in str(exc.orig):
                raise
            case.public_reference = reference.generate_public_reference()
    else:  # pragma: no cover - collision five times is effectively impossible
        raise Conflict("Could not allocate a unique case reference.")

    db.refresh(case)
    case.completeness_status = policies.compute_completeness(case, [])
    audit.record(
        db,
        action=AuditAction.CASE_CREATED,
        actor=user,
        case_id=case.id,
        entity_type="case",
        entity_id=case.id,
        after=audit.snapshot(case),
    )
    db.commit()
    db.refresh(case)
    return case


def get_case(db: Session, case_id: uuid.UUID) -> Case:
    case = db.get(Case, case_id)
    if case is None:
        raise NotFound("Case not found.")
    return case


_EDITABLE_FIELDS = {
    "title",
    "description",
    "incident_type",
    "fraud_channel",
    "incident_occurred_at",
    "estimated_loss_amount",
    "currency",
    "reporting_details",
    "is_disputed",
}


def update_case(db: Session, *, case: Case, user: User, data: dict) -> Case:
    if case.is_archived:
        raise Conflict("Archived cases are read-only. Restore is not supported in this prototype.")

    changes = {key: value for key, value in data.items() if value is not None}
    if not changes:
        return case

    assert_no_authentication_secrets(changes.get("description"), changes.get("reporting_details"))

    target_status = changes.pop("internal_status", None)
    before = audit.snapshot(case)

    for field, value in changes.items():
        if field not in _EDITABLE_FIELDS:
            raise InvalidRequest(f"Field '{field}' cannot be edited.")
        if field == "incident_type":
            value = policies.normalise_incident_type(value)
        if field == "fraud_channel":
            value = policies.normalise_fraud_channel(value)
        if field == "currency":
            value = value.upper()
        setattr(case, field, value)

    if target_status is not None:
        _apply_status(db, case, user, target_status)

    transactions = list(db.scalars(select(Transaction).where(Transaction.case_id == case.id)))
    case.completeness_status = policies.compute_completeness(case, transactions)
    case.updated_at = datetime.now(UTC)

    audit.record(
        db,
        action=AuditAction.CASE_UPDATED,
        actor=user,
        case_id=case.id,
        entity_type="case",
        entity_id=case.id,
        before=before,
        after=audit.snapshot(case),
    )
    db.commit()
    db.refresh(case)
    return case


def change_status(db: Session, *, case: Case, user: User, target_status: str) -> Case:
    if case.is_archived:
        raise Conflict("Archived cases are read-only.")
    before = audit.snapshot(case, exclude=("updated_at",))
    _apply_status(db, case, user, target_status)
    audit.record(
        db,
        action=AuditAction.CASE_STATUS_CHANGED,
        actor=user,
        case_id=case.id,
        entity_type="case",
        entity_id=case.id,
        before=before,
        after=audit.snapshot(case, exclude=("updated_at",)),
    )
    db.commit()
    db.refresh(case)
    return case


def _apply_status(db: Session, case: Case, user: User, target_status: str) -> None:
    valid = {status.value for status in CaseStatus}
    if target_status not in valid:
        raise InvalidRequest(f"Unknown case status '{target_status}'.")
    if target_status == case.internal_status:
        return
    try:
        policies.assert_transition_allowed(case.internal_status, target_status)
    except policies.InvalidTransition as exc:
        raise Conflict(str(exc), code="invalid_transition") from exc
    case.internal_status = target_status
    case.updated_at = datetime.now(UTC)


def archive_case(db: Session, *, case: Case, user: User) -> Case:
    if case.is_archived:
        return case
    before = audit.snapshot(case)
    case.is_archived = True
    case.archived_at = datetime.now(UTC)
    case.updated_at = datetime.now(UTC)
    audit.record(
        db,
        action=AuditAction.CASE_ARCHIVED,
        actor=user,
        case_id=case.id,
        entity_type="case",
        entity_id=case.id,
        before=before,
        after=audit.snapshot(case),
    )
    db.commit()
    db.refresh(case)
    return case


def case_summary(db: Session, case_id: uuid.UUID) -> dict:
    def count(model, column) -> int:  # noqa: ANN001
        return int(
            db.scalar(select(func.count()).select_from(model).where(column == case_id)) or 0
        )

    open_actions = int(
        db.scalar(
            select(func.count())
            .select_from(RecoveryAction)
            .where(
                RecoveryAction.case_id == case_id,
                RecoveryAction.status.in_(("pending", "in_progress", "blocked")),
            )
        )
        or 0
    )
    total = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.case_id == case_id, Transaction.direction == "debit"
        )
    )
    return {
        "case_id": case_id,
        "transaction_count": count(Transaction, Transaction.case_id),
        "evidence_count": count(Evidence, Evidence.case_id),
        "assessment_count": count(RegulatoryAssessment, RegulatoryAssessment.case_id),
        "complaint_count": count(Complaint, Complaint.case_id),
        "recovery_action_count": count(RecoveryAction, RecoveryAction.case_id),
        "open_recovery_actions": open_actions,
        "total_transaction_amount": total or 0,
    }
