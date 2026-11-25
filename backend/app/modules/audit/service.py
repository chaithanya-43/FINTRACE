"""Audit trail writer.

Every state change records an append-only event. Callers pass JSON-safe
snapshots; this module never stores evidence contents or request bodies.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditEvent, User
from app.utils.enums import AuditAction

_SENSITIVE_FIELDS = {
    "password",
    "password_hash",
    "otp",
    "pin",
    "cvv",
    "token",
    "access_token",
}


def json_safe(value: Any) -> Any:  # noqa: ANN401
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


def snapshot(model: Any, *, exclude: tuple[str, ...] = ()) -> dict:  # noqa: ANN401
    """Column-level snapshot of an ORM row, minus sensitive columns."""
    data: dict[str, Any] = {}
    for column in model.__table__.columns:
        if column.name in exclude or column.name in _SENSITIVE_FIELDS:
            continue
        data[column.name] = json_safe(getattr(model, column.name, None))
    return data


def record(
    db: Session,
    *,
    action: AuditAction | str,
    actor: User | None = None,
    case_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    entity_id: str | uuid.UUID | None = None,
    before: dict | None = None,
    after: dict | None = None,
    actor_role: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditEvent:
    event = AuditEvent(
        case_id=case_id,
        actor_user_id=actor.id if actor else None,
        actor_role=actor_role or (actor.role if actor else None),
        action=str(action),
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        before_state=json_safe(before) if before else None,
        after_state=json_safe(after) if after else None,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(event)
    db.flush()
    return event


def list_for_case(db: Session, case_id: uuid.UUID, limit: int = 200) -> list[AuditEvent]:
    statement = (
        select(AuditEvent)
        .where(AuditEvent.case_id == case_id)
        .order_by(AuditEvent.id.desc())
        .limit(limit)
    )
    return list(db.scalars(statement))
