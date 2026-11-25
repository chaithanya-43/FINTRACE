"""Document & Complaint Assistant orchestration."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import Conflict, InvalidRequest, NotFound
from app.models import Case, Complaint, DocumentDraft, Evidence, Transaction, User
from app.modules.audit import service as audit
from app.modules.documents import pdf, templates
from app.utils.enums import DOCUMENT_TYPES, AuditAction, DocumentDraftStatus
from app.utils.sensitive import assert_no_authentication_secrets


def _assert_document_type(document_type: str) -> str:
    value = (document_type or "").strip().lower()
    if value not in DOCUMENT_TYPES:
        raise InvalidRequest(
            f"Unknown document type '{document_type}'. Allowed: {', '.join(DOCUMENT_TYPES)}."
        )
    return value


def _load_case_context(db: Session, case: Case) -> tuple[list[Transaction], list[Evidence], list[Complaint]]:
    transactions = list(
        db.scalars(
            select(Transaction)
            .where(Transaction.case_id == case.id)
            .order_by(Transaction.transaction_at.desc().nulls_last(), Transaction.created_at.desc())
        )
    )
    evidence_items = list(
        db.scalars(
            select(Evidence)
            .where(Evidence.case_id == case.id)
            .order_by(Evidence.created_at.desc())
        )
    )
    complaints = list(
        db.scalars(
            select(Complaint)
            .where(Complaint.case_id == case.id)
            .order_by(Complaint.created_at.desc())
        )
    )
    return transactions, evidence_items, complaints


def catalog() -> list[dict]:
    return [dict(item) for item in templates.DOCUMENT_CATALOG]


def prefill(db: Session, *, case: Case, user: User, document_type: str) -> dict:
    doc_type = _assert_document_type(document_type)
    transactions, evidence_items, complaints = _load_case_context(db, case)
    return templates.build_prefill(
        document_type=doc_type,
        user=user,
        case=case,
        transactions=transactions,
        evidence_items=evidence_items,
        complaints=complaints,
    )


def list_drafts(db: Session, case_id: uuid.UUID) -> list[DocumentDraft]:
    statement = (
        select(DocumentDraft)
        .where(DocumentDraft.case_id == case_id)
        .order_by(DocumentDraft.updated_at.desc())
    )
    return list(db.scalars(statement))


def get_draft(db: Session, *, case: Case, draft_id: uuid.UUID) -> DocumentDraft:
    draft = db.get(DocumentDraft, draft_id)
    if draft is None or draft.case_id != case.id:
        raise NotFound("Document draft not found in this case.")
    return draft


def generate_draft(
    db: Session,
    *,
    case: Case,
    user: User,
    document_type: str,
    intake_answers: dict | None = None,
) -> DocumentDraft:
    if case.is_archived:
        raise Conflict("Archived cases are read-only.")
    doc_type = _assert_document_type(document_type)

    cleaned_answers: dict[str, str] = {}
    if intake_answers:
        for key, value in intake_answers.items():
            text = "" if value is None else str(value)
            assert_no_authentication_secrets(text)
            cleaned_answers[str(key)] = text

    transactions, evidence_items, complaints = _load_case_context(db, case)
    rendered = templates.render_document(
        document_type=doc_type,
        user=user,
        case=case,
        transactions=transactions,
        evidence_items=evidence_items,
        complaints=complaints,
        answers=cleaned_answers,
    )

    draft = DocumentDraft(
        case_id=case.id,
        created_by_user_id=user.id,
        document_type=doc_type,
        title=rendered["title"][:200],
        recipient=rendered["recipient"][:240],
        subject=rendered["subject"][:300],
        content=rendered["content"],
        intake_answers=cleaned_answers,
        attachments_checklist=rendered["attachments_checklist"],
        draft_status=DocumentDraftStatus.DRAFT.value,
    )
    db.add(draft)
    db.flush()

    audit.record(
        db,
        action=AuditAction.DOCUMENT_DRAFT_CREATED,
        actor=user,
        case_id=case.id,
        entity_type="document_draft",
        entity_id=draft.id,
        after={
            "document_type": draft.document_type,
            "title": draft.title,
            "draft_status": draft.draft_status,
        },
    )
    db.commit()
    db.refresh(draft)
    return draft


def update_draft(
    db: Session,
    *,
    case: Case,
    draft: DocumentDraft,
    user: User,
    data: dict,
) -> DocumentDraft:
    if case.is_archived:
        raise Conflict("Archived cases are read-only.")

    changes = {key: value for key, value in data.items() if value is not None}
    if not changes:
        return draft

    assert_no_authentication_secrets(
        changes.get("title"),
        changes.get("recipient"),
        changes.get("subject"),
        changes.get("content"),
    )
    if "intake_answers" in changes and isinstance(changes["intake_answers"], dict):
        for val in changes["intake_answers"].values():
            if val is not None:
                assert_no_authentication_secrets(str(val))

    if "draft_status" in changes:
        valid = {item.value for item in DocumentDraftStatus}
        if changes["draft_status"] not in valid:
            raise InvalidRequest(f"Unknown draft status '{changes['draft_status']}'.")

    before = {
        "title": draft.title,
        "draft_status": draft.draft_status,
        "subject": draft.subject,
    }
    for field, value in changes.items():
        setattr(draft, field, value)
    draft.updated_at = datetime.now(UTC)

    audit.record(
        db,
        action=AuditAction.DOCUMENT_DRAFT_UPDATED,
        actor=user,
        case_id=case.id,
        entity_type="document_draft",
        entity_id=draft.id,
        before=before,
        after={
            "title": draft.title,
            "draft_status": draft.draft_status,
            "subject": draft.subject,
        },
    )
    db.commit()
    db.refresh(draft)
    return draft


def render_pdf(db: Session, *, case: Case, draft: DocumentDraft, user: User) -> bytes:
    pdf_bytes = pdf.render_draft_pdf(
        case_reference=case.public_reference,
        title=draft.title,
        recipient=draft.recipient,
        subject=draft.subject,
        content=draft.content,
        attachments=draft.attachments_checklist or [],
    )
    if not case.is_archived and draft.draft_status == DocumentDraftStatus.DRAFT.value:
        draft.draft_status = DocumentDraftStatus.EXPORTED.value
        draft.updated_at = datetime.now(UTC)
        audit.record(
            db,
            action=AuditAction.DOCUMENT_DRAFT_UPDATED,
            actor=user,
            case_id=case.id,
            entity_type="document_draft",
            entity_id=draft.id,
            after={"draft_status": draft.draft_status, "exported": True},
        )
        db.commit()
    return pdf_bytes
