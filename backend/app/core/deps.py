"""Authentication and authorization dependencies."""

import uuid
from collections.abc import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import Forbidden, NotFound, Unauthorized
from app.core.security import TokenError, decode_access_token
from app.database.connection import get_db
from app.models import Case, User
from app.utils.enums import AccountStatus, Role

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise Unauthorized()
    try:
        payload = decode_access_token(credentials.credentials)
    except TokenError as exc:
        raise Unauthorized(str(exc)) from exc

    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise Unauthorized("Access token subject is not a valid user id.") from exc

    user = db.get(User, user_id)
    if user is None:
        raise Unauthorized("The account for this token no longer exists.")
    if user.account_status != AccountStatus.ACTIVE:
        raise Forbidden("This account is not active.")
    return user


def require_roles(*roles: str) -> Callable[..., User]:
    allowed = set(roles)

    def _dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise Forbidden(
                f"This action requires one of the roles: {', '.join(sorted(allowed))}."
            )
        return user

    return _dependency


def can_access_case(user: User, case: Case) -> bool:
    """Citizens see their own cases; investigators their assigned ones.

    Administrators may access any case for support and review purposes.
    """
    if user.role == Role.ADMINISTRATOR:
        return True
    if case.created_by_user_id == user.id:
        return True
    if user.role == Role.INVESTIGATOR and case.assigned_to_user_id == user.id:
        return True
    return False


def load_authorized_case(
    case_id: uuid.UUID,
    user: User,
    db: Session,
    *,
    allow_archived: bool = True,
) -> Case:
    case = db.get(Case, case_id)
    if case is None:
        raise NotFound("Case not found.")
    if not can_access_case(user, case):
        # Deliberately the same response as a missing case: existence of other
        # people's cases is not disclosed.
        raise NotFound("Case not found.")
    if case.is_archived and not allow_archived:
        raise Forbidden("This case is archived and read-only.")
    return case


def get_case_dependency(case_id: uuid.UUID) -> Callable[..., Case]:
    def _dependency(
        user: User = Depends(get_current_user), db: Session = Depends(get_db)
    ) -> Case:
        return load_authorized_case(case_id, user, db)

    return _dependency


def visible_case_query(user: User):
    statement = select(Case)
    if user.role == Role.ADMINISTRATOR:
        return statement
    if user.role == Role.INVESTIGATOR:
        return statement.where(
            (Case.created_by_user_id == user.id) | (Case.assigned_to_user_id == user.id)
        )
    return statement.where(Case.created_by_user_id == user.id)
