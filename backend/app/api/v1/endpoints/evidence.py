import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, load_authorized_case
from app.core.exceptions import Conflict
from app.database.connection import get_db
from app.models import Evidence, User
from app.modules.evidence import service
from app.schemas.evidence import (
    EvidenceRead,
    EvidenceVerifyResponse,
    SignatureRead,
)

router = APIRouter(tags=["evidence"])


@router.get("/cases/{case_id}/evidence", response_model=list[EvidenceRead])
def list_evidence(
    case_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[EvidenceRead]:
    load_authorized_case(case_id, user, db)
    return [EvidenceRead.model_validate(item) for item in service.list_evidence(db, case_id)]


@router.post(
    "/cases/{case_id}/evidence",
    response_model=EvidenceRead,
    status_code=status.HTTP_201_CREATED,
)
def upload_evidence(
    case_id: uuid.UUID,
    file: UploadFile = File(...),
    evidence_type: str = Form(default="other"),
    description: str | None = Form(default=None),
    transaction_id: uuid.UUID | None = Form(default=None),
    collected_at: datetime | None = Form(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EvidenceRead:
    case = load_authorized_case(case_id, user, db)
    evidence = service.upload_evidence(
        db,
        case=case,
        user=user,
        upload=file,
        evidence_type=evidence_type,
        description=description,
        transaction_id=transaction_id,
        collected_at=collected_at,
    )
    return EvidenceRead.model_validate(evidence)


@router.get("/cases/{case_id}/evidence/{evidence_id}", response_model=EvidenceRead)
def read_evidence(
    case_id: uuid.UUID,
    evidence_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EvidenceRead:
    case = load_authorized_case(case_id, user, db)
    return EvidenceRead.model_validate(service.get_evidence(db, case=case, evidence_id=evidence_id))


@router.get("/cases/{case_id}/evidence/{evidence_id}/download")
def download_evidence(
    case_id: uuid.UUID,
    evidence_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    case = load_authorized_case(case_id, user, db)
    evidence: Evidence = service.get_evidence(db, case=case, evidence_id=evidence_id)
    stream = service.read_stream(evidence)
    # Evidence is private: it is streamed through this authorized endpoint and
    # never exposed as a public storage URL.
    return StreamingResponse(
        stream,
        media_type=evidence.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{evidence.original_filename}"',
            "X-Evidence-SHA256": evidence.sha256_hash,
            "Cache-Control": "no-store",
        },
    )


@router.post(
    "/cases/{case_id}/evidence/{evidence_id}/verify",
    response_model=EvidenceVerifyResponse,
)
def verify_evidence(
    case_id: uuid.UUID,
    evidence_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EvidenceVerifyResponse:
    case = load_authorized_case(case_id, user, db)
    evidence = service.get_evidence(db, case=case, evidence_id=evidence_id)
    return EvidenceVerifyResponse(**service.verify_evidence(db, case=case, evidence=evidence, user=user))


@router.get(
    "/cases/{case_id}/evidence/{evidence_id}/signatures",
    response_model=list[SignatureRead],
)
def list_signatures(
    case_id: uuid.UUID,
    evidence_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SignatureRead]:
    case = load_authorized_case(case_id, user, db)
    evidence = service.get_evidence(db, case=case, evidence_id=evidence_id)
    return [SignatureRead.model_validate(item) for item in service.list_signatures(db, evidence)]


@router.post(
    "/cases/{case_id}/evidence/{evidence_id}/sign",
    response_model=SignatureRead,
    status_code=status.HTTP_201_CREATED,
)
def sign_evidence(
    case_id: uuid.UUID,
    evidence_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SignatureRead:
    case = load_authorized_case(case_id, user, db)
    evidence = service.get_evidence(db, case=case, evidence_id=evidence_id)
    if evidence.verification_status != "verified":
        raise Conflict(
            "Verify the stored bytes before signing: a signature over an unverified hash "
            "would attest to something that was not checked.",
            code="evidence_not_verified",
        )
    signature = service.sign_evidence(db, case=case, evidence=evidence, user=user)
    return SignatureRead.model_validate(signature)
