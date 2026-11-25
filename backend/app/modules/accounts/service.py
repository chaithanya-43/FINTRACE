"""Account lifecycle: registration, authentication and role administration."""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import Conflict, Forbidden, InvalidRequest, Unauthorized
from app.core.security import (
    create_access_token,
    hash_password,
    password_hash_needs_rehash,
    verify_password,
)
from app.models import User
from app.modules.audit import service as audit
from app.utils.enums import AccountStatus, AuditAction, Role

# Compared against when the email is unknown, so a missing account does not
# respond measurably faster than a wrong password.
_DUMMY_HASH = hash_password("fintrace-dummy-password-value")


def register(db: Session, *, email: str, password: str, full_name: str, phone: str | None) -> User:
    normalised_email = email.strip().lower()
    existing = db.scalar(
        select(User).where(func.lower(User.email) == normalised_email)
    )
    if existing is not None:
        raise Conflict("An account with this email already exists.", code="email_taken")

    user = User(
        email=normalised_email,
        full_name=full_name.strip(),
        phone_e164=phone,
        password_hash=hash_password(password),
        # Self-registration can only ever create a citizen account.
        role=Role.CITIZEN.value,
        account_status=AccountStatus.ACTIVE.value,
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise Conflict("An account with this email already exists.", code="email_taken") from exc

    audit.record(
        db,
        action=AuditAction.USER_REGISTERED,
        actor=user,
        entity_type="user",
        entity_id=user.id,
        after={"email": user.email, "role": user.role},
    )
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, *, email: str, password: str) -> tuple[User, str, int]:
    normalised_email = email.strip().lower()
    user = db.scalar(select(User).where(func.lower(User.email) == normalised_email))

    if user is None:
        verify_password(_DUMMY_HASH, password)
        raise Unauthorized("Email or password is incorrect.")

    if not verify_password(user.password_hash, password):
        audit.record(
            db,
            action=AuditAction.USER_LOGIN_FAILED,
            actor=user,
            entity_type="user",
            entity_id=user.id,
        )
        db.commit()
        raise Unauthorized("Email or password is incorrect.")

    if user.account_status != AccountStatus.ACTIVE:
        raise Forbidden("This account is not active.")

    if password_hash_needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)

    user.last_login_at = datetime.now(UTC)
    token, expires_in = create_access_token(str(user.id), user.role)
    audit.record(
        db,
        action=AuditAction.USER_LOGGED_IN,
        actor=user,
        entity_type="user",
        entity_id=user.id,
    )
    db.commit()
    db.refresh(user)
    return user, token, expires_in


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at.desc())))


def change_role(db: Session, *, actor: User, user: User, role: str) -> User:
    if role not in {item.value for item in Role}:
        raise InvalidRequest(f"Unknown role '{role}'.")
    if user.id == actor.id and role != Role.ADMINISTRATOR.value:
        raise InvalidRequest("Administrators cannot remove their own administrator role.")

    before = {"role": user.role}
    user.role = role
    user.updated_at = datetime.now(UTC)
    audit.record(
        db,
        action=AuditAction.USER_ROLE_CHANGED,
        actor=actor,
        entity_type="user",
        entity_id=user.id,
        before=before,
        after={"role": role},
    )
    db.commit()
    db.refresh(user)
    return user


def change_account_status(db: Session, *, actor: User, user: User, status: str) -> User:
    if status not in {item.value for item in AccountStatus}:
        raise InvalidRequest(f"Unknown account status '{status}'.")
    before = {"account_status": user.account_status}
    user.account_status = status
    user.updated_at = datetime.now(UTC)
    audit.record(
        db,
        action="user.account_status_changed",
        actor=actor,
        entity_type="user",
        entity_id=user.id,
        before=before,
        after={"account_status": status},
    )
    db.commit()
    db.refresh(user)
    return user
