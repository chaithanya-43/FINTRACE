"""Complaint records and externally observed status history.

FINTRACE records complaints the user filed themselves. It has no integration
that submits anything to an official portal, and nothing here claims otherwise.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import Conflict, InvalidRequest, NotFound
from app.models import Case, Complaint, ComplaintStatusEvent, Transaction, User
from app.modules.audit import service as audit
from app.utils.enums import (
    COMPLAINT_CHANNELS,
    AuditAction,
    SubmissionStatus,
)
from app.utils.sensitive import assert_no_authentication_secrets

_OPEN_STATUSES = {
    SubmissionStatus.DRAFT.value,
    SubmissionStatus.READY.value,
    SubmissionStatus.SUBMITTED.value,
    SubmissionStatus.ACKNOWLEDGED.value,
}


def _assert_channel(channel: str) -> str:
    channel = channel.strip().lower()
    if channel not in COMPLAINT_CHANNELS:
        raise InvalidRequest(
            f"Unknown complaint channel '{channel}'. Allowed: {', '.join(COMPLAINT_CHANNELS)}."
        )
    return channel


def list_complaints(db: Session, case_id: uuid.UUID) -> list[Complaint]:
    statement = (
        select(Complaint)
        .where(Complaint.case_id == case_id)
        .order_by(Complaint.created_at.desc())
    )
    return list(db.scalars(statement))


def create_complaint(db: Session, *, case: Case, user: User, data: dict) -> Complaint:
    if case.is_archived:
        raise Conflict("Archived cases are read-only.")
    assert_no_authentication_secrets(
        data.get("notes"),
        data.get("organisation_name"),
        data.get("reference_number"),
    )

    channel = _assert_channel(data["channel"])
    status = data.get("submission_status") or SubmissionStatus.DRAFT.value
    valid_statuses = {item.value for item in SubmissionStatus}
    if status not in valid_statuses:
        raise InvalidRequest(f"Unknown submission status '{status}'.")

    filed_at = data.get("filed_at")
    if status in ("submitted", "acknowledged") and filed_at is None:
        filed_at = datetime.now(UTC)

    complaint = Complaint(
        case_id=case.id,
        channel=channel,
        organisation_name=data.get("organisation_name"),
        reference_number=(data.get("reference_number") or "").strip() or None,
        submission_status=status,
        filed_at=filed_at,
        created_by_user_id=user.id,
        prepared_payload=_prepare_payload(case, channel),
    )
    if status == SubmissionStatus.ACKNOWLEDGED.value:
        complaint.acknowledged_at = datetime.now(UTC)

    db.add(complaint)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        if "uq_complaints_case_channel_reference" in str(exc.orig):
            raise Conflict(
                "A complaint with this channel and reference number already exists in this case.",
                code="duplicate_complaint_reference",
            ) from exc
        raise
    audit.record(
        db,
        action=AuditAction.COMPLAINT_CREATED,
        actor=user,
        case_id=case.id,
        entity_type="complaint",
        entity_id=complaint.id,
        after=audit.snapshot(complaint),
    )
    db.commit()
    db.refresh(complaint)
    return complaint


def _prepare_payload(case: Case, channel: str) -> dict:
    """Reference information the user can copy into the organisation's form."""
    return {
        "case_reference": case.public_reference,
        "channel": channel,
        "incident_type": case.incident_type,
        "fraud_channel": case.fraud_channel,
        "incident_occurred_at": case.incident_occurred_at.isoformat()
        if case.incident_occurred_at
        else None,
        "estimated_loss_amount": float(case.estimated_loss_amount)
        if case.estimated_loss_amount is not None
        else None,
        "currency": case.currency,
        "note": "Prepared by FINTRACE for the user to submit. FINTRACE does not submit complaints.",
    }


def get_complaint(db: Session, *, case: Case, complaint_id: uuid.UUID) -> Complaint:
    complaint = db.get(Complaint, complaint_id)
    if complaint is None or complaint.case_id != case.id:
        raise NotFound("Complaint not found in this case.")
    return complaint


def update_complaint(
    db: Session, *, case: Case, complaint: Complaint, user: User, data: dict
) -> Complaint:
    if case.is_archived:
        raise Conflict("Archived cases are read-only.")

    changes = {key: value for key, value in data.items() if value is not None}
    if not changes:
        return complaint
    assert_no_authentication_secrets(
        changes.get("organisation_name"), changes.get("reference_number")
    )
    if "channel" in changes:
        changes["channel"] = _assert_channel(changes["channel"])
    if "reference_number" in changes:
        changes["reference_number"] = changes["reference_number"].strip() or None

    status = changes.get("submission_status")
    if status is not None:
        valid_statuses = {item.value for item in SubmissionStatus}
        if status not in valid_statuses:
            raise InvalidRequest(f"Unknown submission status '{status}'.")
        if status in ("submitted", "acknowledged") and not (
            changes.get("filed_at") or complaint.filed_at
        ):
            changes["filed_at"] = datetime.now(UTC)
        if status == "acknowledged" and not (
            changes.get("acknowledged_at") or complaint.acknowledged_at
        ):
            changes["acknowledged_at"] = datetime.now(UTC)

    before = audit.snapshot(complaint)
    for field, value in changes.items():
        setattr(complaint, field, value)
    complaint.updated_at = datetime.now(UTC)

    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        if "uq_complaints_case_channel_reference" in str(exc.orig):
            raise Conflict(
                "A complaint with this channel and reference number already exists in this case.",
                code="duplicate_complaint_reference",
            ) from exc
        raise

    audit.record(
        db,
        action=AuditAction.COMPLAINT_UPDATED,
        actor=user,
        case_id=case.id,
        entity_type="complaint",
        entity_id=complaint.id,
        before=before,
        after=audit.snapshot(complaint),
    )
    db.commit()
    db.refresh(complaint)
    return complaint


def add_status_event(
    db: Session, *, case: Case, complaint: Complaint, user: User, data: dict
) -> ComplaintStatusEvent:
    """Append an observation and refresh the cached official status."""
    if case.is_archived:
        raise Conflict("Archived cases are read-only.")
    assert_no_authentication_secrets(data.get("observed_status"), data.get("status_detail"))

    checked_at = data.get("checked_at") or datetime.now(UTC)
    event = ComplaintStatusEvent(
        complaint_id=complaint.id,
        observed_status=data["observed_status"].strip(),
        status_detail=data.get("status_detail"),
        source_url=data.get("source_url"),
        checked_at=checked_at,
        recorded_by_user_id=user.id,
    )
    db.add(event)
    try:
        db.flush()
    except Exception as exc:  # noqa: BLE001 - unique violation maps to a clean 409
        db.rollback()
        if "uq_complaint_status_events_observation" in str(exc):
            raise Conflict(
                "This status observation was already recorded.",
                code="duplicate_observation",
            ) from exc
        raise

    # The cache always mirrors the newest observation; history remains authority.
    complaint.official_status = event.observed_status
    complaint.official_status_detail = event.status_detail
    complaint.official_status_source_url = event.source_url
    complaint.last_checked_at = checked_at
    complaint.updated_at = datetime.now(UTC)

    audit.record(
        db,
        action=AuditAction.COMPLAINT_STATUS_OBSERVED,
        actor=user,
        case_id=case.id,
        entity_type="complaint_status_event",
        entity_id=event.id,
        after={
            "complaint_id": str(complaint.id),
            "observed_status": event.observed_status,
            "checked_at": checked_at,
        },
    )
    db.commit()
    db.refresh(event)
    return event


def status_history(db: Session, complaint: Complaint) -> list[ComplaintStatusEvent]:
    statement = (
        select(ComplaintStatusEvent)
        .where(ComplaintStatusEvent.complaint_id == complaint.id)
        .order_by(ComplaintStatusEvent.checked_at.asc(), ComplaintStatusEvent.created_at.asc())
    )
    return list(db.scalars(statement))


def case_transactions(db: Session, case_id: uuid.UUID) -> list[Transaction]:
    return list(db.scalars(select(Transaction).where(Transaction.case_id == case_id)))
