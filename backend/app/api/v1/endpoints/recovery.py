import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, load_authorized_case
from app.database.connection import get_db
from app.models import User
from app.modules.recovery import service
from app.schemas.recovery import (
    RecoveryActionCreate,
    RecoveryActionRead,
    RecoveryActionUpdate,
    RoadmapResponse,
)

router = APIRouter(tags=["recovery"])


@router.get("/cases/{case_id}/roadmap", response_model=RoadmapResponse)
def read_roadmap(
    case_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoadmapResponse:
    case = load_authorized_case(case_id, user, db)
    return RoadmapResponse(**service.build_roadmap(db, case=case, user=user))


@router.get("/cases/{case_id}/actions", response_model=list[RecoveryActionRead])
def list_actions(
    case_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[RecoveryActionRead]:
    load_authorized_case(case_id, user, db)
    return [RecoveryActionRead.model_validate(item) for item in service.list_actions(db, case_id)]


@router.post(
    "/cases/{case_id}/actions",
    response_model=RecoveryActionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_action(
    case_id: uuid.UUID,
    payload: RecoveryActionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecoveryActionRead:
    case = load_authorized_case(case_id, user, db)
    action = service.create_action(
        db, case=case, user=user, data=payload.model_dump(exclude_unset=True)
    )
    return RecoveryActionRead.model_validate(action)


@router.patch(
    "/cases/{case_id}/actions/{action_id}", response_model=RecoveryActionRead
)
def update_action(
    case_id: uuid.UUID,
    action_id: uuid.UUID,
    payload: RecoveryActionUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecoveryActionRead:
    case = load_authorized_case(case_id, user, db)
    action = service.update_action(
        db, case=case, action_id=action_id, user=user, data=payload.model_dump(exclude_unset=True)
    )
    return RecoveryActionRead.model_validate(action)
