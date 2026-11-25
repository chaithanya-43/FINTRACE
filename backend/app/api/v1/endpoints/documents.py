import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, load_authorized_case
from app.database.connection import get_db
from app.models import User
from app.modules.documents import service
from app.schemas.document import (
    DocumentCatalogItem,
    DocumentDraftRead,
    DocumentDraftUpdate,
    DocumentGenerateRequest,
    DocumentPrefillResponse,
)

router = APIRouter(tags=["documents"])


@router.get("/documents/catalog", response_model=list[DocumentCatalogItem])
def list_document_catalog(
    _: User = Depends(get_current_user),
) -> list[DocumentCatalogItem]:
    return [DocumentCatalogItem(**item) for item in service.catalog()]


@router.get("/cases/{case_id}/documents/prefill", response_model=DocumentPrefillResponse)
def prefill_document(
    case_id: uuid.UUID,
    document_type: str = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentPrefillResponse:
    case = load_authorized_case(case_id, user, db)
    data = service.prefill(db, case=case, user=user, document_type=document_type)
    return DocumentPrefillResponse(**data)


@router.get("/cases/{case_id}/documents", response_model=list[DocumentDraftRead])
def list_case_documents(
    case_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DocumentDraftRead]:
    load_authorized_case(case_id, user, db)
    return [DocumentDraftRead.model_validate(item) for item in service.list_drafts(db, case_id)]


@router.post(
    "/cases/{case_id}/documents/generate",
    response_model=DocumentDraftRead,
    status_code=status.HTTP_201_CREATED,
)
def generate_case_document(
    case_id: uuid.UUID,
    payload: DocumentGenerateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentDraftRead:
    case = load_authorized_case(case_id, user, db)
    draft = service.generate_draft(
        db,
        case=case,
        user=user,
        document_type=payload.document_type,
        intake_answers=payload.intake_answers,
    )
    return DocumentDraftRead.model_validate(draft)


@router.get("/cases/{case_id}/documents/{draft_id}", response_model=DocumentDraftRead)
def read_case_document(
    case_id: uuid.UUID,
    draft_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentDraftRead:
    case = load_authorized_case(case_id, user, db)
    draft = service.get_draft(db, case=case, draft_id=draft_id)
    return DocumentDraftRead.model_validate(draft)


@router.patch("/cases/{case_id}/documents/{draft_id}", response_model=DocumentDraftRead)
def update_case_document(
    case_id: uuid.UUID,
    draft_id: uuid.UUID,
    payload: DocumentDraftUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentDraftRead:
    case = load_authorized_case(case_id, user, db)
    draft = service.get_draft(db, case=case, draft_id=draft_id)
    updated = service.update_draft(
        db,
        case=case,
        draft=draft,
        user=user,
        data=payload.model_dump(exclude_unset=True),
    )
    return DocumentDraftRead.model_validate(updated)


@router.get("/cases/{case_id}/documents/{draft_id}/pdf")
def export_case_document_pdf(
    case_id: uuid.UUID,
    draft_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    case = load_authorized_case(case_id, user, db)
    draft = service.get_draft(db, case=case, draft_id=draft_id)
    pdf_bytes = service.render_pdf(db, case=case, draft=draft, user=user)
    safe_name = f"{case.public_reference}_{draft.document_type}_draft.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_name}"',
            "Cache-Control": "no-store",
        },
    )
