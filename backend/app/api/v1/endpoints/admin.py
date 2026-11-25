from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.core.exceptions import NotFound
from app.database.connection import get_db
from app.models import User
from app.modules.accounts import service
from app.schemas.auth import UserRead
from app.utils.enums import Role

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserRead])
def list_users(
    _: User = Depends(require_roles(Role.ADMINISTRATOR.value)),
    db: Session = Depends(get_db),
) -> list[UserRead]:
    return [UserRead.model_validate(user) for user in service.list_users(db)]


@router.patch("/users/{user_id}/role", response_model=UserRead)
def change_role(
    user_id: str,
    payload: dict,
    actor: User = Depends(require_roles(Role.ADMINISTRATOR.value)),
    db: Session = Depends(get_db),
) -> UserRead:
    import uuid as _uuid

    user = db.get(User, _uuid.UUID(user_id))
    if user is None:
        raise NotFound("User not found.")
    updated = service.change_role(db, actor=actor, user=user, role=str(payload.get("role", "")))
    return UserRead.model_validate(updated)


@router.patch("/users/{user_id}/status", response_model=UserRead)
def change_status(
    user_id: str,
    payload: dict,
    actor: User = Depends(require_roles(Role.ADMINISTRATOR.value)),
    db: Session = Depends(get_db),
) -> UserRead:
    import uuid as _uuid

    user = db.get(User, _uuid.UUID(user_id))
    if user is None:
        raise NotFound("User not found.")
    updated = service.change_account_status(
        db, actor=actor, user=user, status=str(payload.get("account_status", ""))
    )
    return UserRead.model_validate(updated)
