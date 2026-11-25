"""Evidence orchestration: upload, verify, sign, read."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError, Conflict, InvalidRequest, NotFound, Unavailable
from app.models import Case, Evidence, EvidenceSignature, Transaction, User
from app.modules.audit import service as audit
from app.modules.evidence import hashing, signing, storage
from app.utils.enums import (
    AuditAction,
    EvidenceVerificationStatus,
)
from app.utils.sensitive import assert_no_authentication_secrets

HASH_DISCLAIMER = (
    "The SHA-256 hash proves the stored file matches the bytes recorded at upload. "
    "It does not prove the file came from the claimed source or existed at a "
    "particular time; chain-of-custody context is recorded separately."
)


def list_evidence(db: Session, case_id: uuid.UUID) -> list[Evidence]:
    statement = (
        select(Evidence)
        .where(Evidence.case_id == case_id)
        .order_by(Evidence.created_at.desc())
    )
    return list(db.scalars(statement))


def get_evidence(db: Session, *, case: Case, evidence_id: uuid.UUID) -> Evidence:
    evidence = db.get(Evidence, evidence_id)
    if evidence is None or evidence.case_id != case.id:
        raise NotFound("Evidence not found in this case.")
    return evidence


def upload_evidence(
    db: Session,
    *,
    case: Case,
    user: User,
    upload,
    evidence_type: str = "other",
    description: str | None = None,
    transaction_id: uuid.UUID | None = None,
    collected_at: datetime | None = None,
) -> Evidence:
    if case.is_archived:
        raise Conflict("Archived cases are read-only.")
    assert_no_authentication_secrets(description, upload.filename)

    content_type = (upload.content_type or "application/octet-stream").lower()
    if content_type not in settings.allowed_evidence_type_list:
        raise InvalidRequest(
            f"Unsupported file type '{content_type}'. Allowed: "
            f"{', '.join(settings.allowed_evidence_type_list)}.",
            code="unsupported_file_type",
        )

    if transaction_id is not None:
        transaction = db.get(Transaction, transaction_id)
        if transaction is None or transaction.case_id != case.id:
            raise NotFound("Transaction not found in this case.")

    try:
        relative_path, sha256_hash, byte_size = storage.save_stream(
            case.id, upload.file, max_bytes=settings.max_upload_bytes
        )
    except storage.StorageError as exc:
        message = str(exc)
        if "maximum upload size" in message:
            raise AppError(413, "file_too_large", message) from exc
        raise InvalidRequest(message, code="invalid_upload") from exc

    ownership = [
        {
            "event": "uploaded",
            "at": datetime.now(UTC).isoformat(),
            "actor_user_id": str(user.id),
            "sha256": sha256_hash,
            "byte_size": byte_size,
            "note": "Recorded by FINTRACE at upload time; not an independent attestation.",
        }
    ]

    evidence = Evidence(
        case_id=case.id,
        transaction_id=transaction_id,
        uploaded_by_user_id=user.id,
        original_filename=(upload.filename or "unnamed")[:255],
        stored_path=relative_path,
        content_type=content_type,
        byte_size=byte_size,
        sha256_hash=sha256_hash,
        evidence_type=(evidence_type or "other")[:48],
        description=description,
        collected_at=collected_at,
        chain_of_custody=ownership,
        verification_status=EvidenceVerificationStatus.UNVERIFIED.value,
    )
    db.add(evidence)
    db.flush()

    audit.record(
        db,
        action=AuditAction.EVIDENCE_UPLOADED,
        actor=user,
        case_id=case.id,
        entity_type="evidence",
        entity_id=evidence.id,
        after={
            "sha256_hash": sha256_hash,
            "byte_size": byte_size,
            "content_type": content_type,
            "original_filename": evidence.original_filename,
        },
    )
    db.commit()
    db.refresh(evidence)
    return evidence


def read_stream(evidence: Evidence):
    try:
        return storage.open_stream(evidence.stored_path)
    except storage.StorageError as exc:
        raise NotFound(str(exc)) from exc


def verify_evidence(
    db: Session, *, case: Case, evidence: Evidence, user: User
) -> dict:
    try:
        recomputed = hashing.sha256_file(storage.absolute_path(evidence.stored_path))
    except storage.StorageError as exc:
        recomputed = ""
        note = str(exc)
    else:
        note = HASH_DISCLAIMER

    hash_matches = bool(recomputed) and recomputed == evidence.sha256_hash
    notes = [note]

    signatures = list(
        db.scalars(
            select(EvidenceSignature).where(EvidenceSignature.evidence_id == evidence.id)
        )
    )
    signature_status = "not_signed"
    if signatures:
        public_key = signing.public_key_b64() if signing.is_configured() else None
        results = []
        for signature in signatures:
            if public_key is None:
                results.append("unavailable")
                continue
            valid = signing.verify_signature(
                signature.signature_b64, evidence.sha256_hash, public_key
            )
            results.append("valid" if valid else "invalid")
        if "invalid" in results:
            signature_status = "invalid"
        elif "unavailable" in results:
            signature_status = "unavailable"
        else:
            signature_status = "valid"
        if signature_status == "unavailable":
            notes.append(
                "Signatures exist but no public key is configured, so they could not be checked."
            )
        if signature_status == "invalid":
            notes.append("At least one stored signature does not verify against the hash.")

    previous = evidence.verification_status
    evidence.verification_status = (
        EvidenceVerificationStatus.VERIFIED.value
        if hash_matches
        else EvidenceVerificationStatus.FAILED.value
    )
    evidence.verified_at = datetime.now(UTC)
    evidence.updated_at = datetime.now(UTC)

    audit.record(
        db,
        action=AuditAction.EVIDENCE_VERIFIED
        if hash_matches
        else AuditAction.EVIDENCE_VERIFICATION_FAILED,
        actor=user,
        case_id=case.id,
        entity_type="evidence",
        entity_id=evidence.id,
        before={"verification_status": previous},
        after={
            "verification_status": evidence.verification_status,
            "recomputed_hash": recomputed,
            "stored_hash": evidence.sha256_hash,
            "signature_status": signature_status,
        },
    )
    db.commit()
    db.refresh(evidence)

    return {
        "evidence_id": evidence.id,
        "stored_hash": evidence.sha256_hash,
        "recomputed_hash": recomputed,
        "hash_matches": hash_matches,
        "verification_status": evidence.verification_status,
        "signature_status": signature_status,
        "signed": bool(signatures),
        "notes": notes,
    }


def sign_evidence(db: Session, *, case: Case, evidence: Evidence, user: User) -> EvidenceSignature:
    if not signing.is_configured():
        raise Unavailable(
            "Evidence signing is not configured on this deployment. Set "
            "ED25519_KEY_ID and ED25519_PRIVATE_KEY_B64 to enable it.",
            code="signing_unavailable",
        )
    try:
        signature_b64 = signing.sign_hash(evidence.sha256_hash)
    except signing.SigningUnavailable as exc:
        raise Unavailable(str(exc), code="signing_unavailable") from exc
    except signing.SigningError as exc:
        raise InvalidRequest(str(exc), code="signing_error") from exc

    key = signing.ensure_registered_key(db)
    signature = EvidenceSignature(
        evidence_id=evidence.id,
        signing_key_id=key.id if key else None,
        key_id_snapshot=signing.key_id(),
        algorithm="Ed25519",
        signature_b64=signature_b64,
        signed_at=datetime.now(UTC),
        verification_result="valid"
        if signing.verify_signature(signature_b64, evidence.sha256_hash, signing.public_key_b64())
        else "unverified",
    )
    db.add(signature)
    db.flush()

    custody = list(evidence.chain_of_custody or [])
    custody.append(
        {
            "event": "signed",
            "at": datetime.now(UTC).isoformat(),
            "actor_user_id": str(user.id),
            "key_id": signing.key_id(),
        }
    )
    evidence.chain_of_custody = custody
    evidence.updated_at = datetime.now(UTC)

    audit.record(
        db,
        action=AuditAction.EVIDENCE_VERIFIED,
        actor=user,
        case_id=case.id,
        entity_type="evidence_signature",
        entity_id=signature.id,
        after={"key_id": signing.key_id(), "evidence_id": str(evidence.id)},
    )
    db.commit()
    db.refresh(signature)
    return signature


def list_signatures(db: Session, evidence: Evidence) -> list[EvidenceSignature]:
    return list(
        db.scalars(
            select(EvidenceSignature)
            .where(EvidenceSignature.evidence_id == evidence.id)
            .order_by(EvidenceSignature.signed_at.desc())
        )
    )
