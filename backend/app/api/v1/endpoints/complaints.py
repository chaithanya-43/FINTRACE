import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, load_authorized_case
from app.database.connection import get_db
from app.models import User
from app.modules.cases import complaints as service
from app.schemas.complaint import (
    ComplaintCreate,
    ComplaintRead,
    ComplaintUpdate,
    StatusEventCreate,
    StatusEventRead,
)

router = APIRouter(tags=["complaints"])


@router.get("/cases/{case_id}/complaints", response_model=list[ComplaintRead])
def list_complaints(
    case_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ComplaintRead]:
    load_authorized_case(case_id, user, db)
    return [ComplaintRead.model_validate(item) for item in service.list_complaints(db, case_id)]


@router.post(
    "/cases/{case_id}/complaints",
    response_model=ComplaintRead,
    status_code=status.HTTP_201_CREATED,
)
def create_complaint(
    case_id: uuid.UUID,
    payload: ComplaintCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ComplaintRead:
    case = load_authorized_case(case_id, user, db)
    complaint = service.create_complaint(
        db, case=case, user=user, data=payload.model_dump(exclude_unset=True)
    )
    return ComplaintRead.model_validate(complaint)


@router.patch("/cases/{case_id}/complaints/{complaint_id}", response_model=ComplaintRead)
def update_complaint(
    case_id: uuid.UUID,
    complaint_id: uuid.UUID,
    payload: ComplaintUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ComplaintRead:
    case = load_authorized_case(case_id, user, db)
    complaint = service.get_complaint(db, case=case, complaint_id=complaint_id)
    complaint = service.update_complaint(
        db, case=case, complaint=complaint, user=user, data=payload.model_dump(exclude_unset=True)
    )
    return ComplaintRead.model_validate(complaint)


@router.get(
    "/cases/{case_id}/complaints/{complaint_id}/history",
    response_model=list[StatusEventRead],
)
def complaint_history(
    case_id: uuid.UUID,
    complaint_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[StatusEventRead]:
    case = load_authorized_case(case_id, user, db)
    complaint = service.get_complaint(db, case=case, complaint_id=complaint_id)
    return [StatusEventRead.model_validate(item) for item in service.status_history(db, complaint)]


@router.post(
    "/cases/{case_id}/complaints/{complaint_id}/history",
    response_model=StatusEventRead,
    status_code=status.HTTP_201_CREATED,
)
def record_status_observation(
    case_id: uuid.UUID,
    complaint_id: uuid.UUID,
    payload: StatusEventCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StatusEventRead:
    case = load_authorized_case(case_id, user, db)
    complaint = service.get_complaint(db, case=case, complaint_id=complaint_id)
    event = service.add_status_event(
        db, case=case, complaint=complaint, user=user, data=payload.model_dump(exclude_unset=True)
    )
    return StatusEventRead.model_validate(event)
