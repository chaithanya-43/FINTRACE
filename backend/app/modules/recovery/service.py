"""Recovery action persistence and roadmap assembly."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import Conflict, InvalidRequest, NotFound
from app.models import Case, Evidence, RecoveryAction, Transaction, User
from app.modules.audit import service as audit
from app.modules.recovery import planner
from app.utils.enums import (
    AuditAction,
    RecoveryOutcome,
    RecoveryPriority,
    RecoveryStatus,
)


def list_actions(db: Session, case_id: uuid.UUID) -> list[RecoveryAction]:
    statement = (
        select(RecoveryAction)
        .where(RecoveryAction.case_id == case_id)
        .order_by(RecoveryAction.priority, RecoveryAction.created_at)
    )
    return list(db.scalars(statement))


def ensure_roadmap(db: Session, *, case: Case, user: User) -> list[RecoveryAction]:
    """Create any recommended action that is missing, then return the roadmap.

    Existing actions are never duplicated, overwritten or re-prioritised, so a
    user's own edits survive later calls.
    """
    transactions = list(
        db.scalars(select(Transaction).where(Transaction.case_id == case.id))
    )
    evidence_count = int(
        db.scalar(
            select(func.count())
            .select_from(Evidence)
            .where(Evidence.case_id == case.id)
        )
        or 0
    )
    existing = {action.action_type for action in list_actions(db, case.id)}
    created: list[RecoveryAction] = []

    for recommendation in planner.recommend(case, transactions, evidence_count):
        if recommendation["action_type"] in existing:
            continue
        action = RecoveryAction(
            case_id=case.id,
            action_type=recommendation["action_type"],
            title=recommendation["title"],
            description=recommendation["description"],
            instructions=recommendation["instructions"],
            priority=recommendation["priority"],
            due_at=recommendation["due_at"],
            status=RecoveryStatus.PENDING.value,
            source="system",
            created_by_user_id=user.id,
        )
        db.add(action)
        created.append(action)

    if created:
        db.flush()
        for action in created:
            audit.record(
                db,
                action=AuditAction.RECOVERY_ACTION_CREATED,
                actor=user,
                case_id=case.id,
                entity_type="recovery_action",
                entity_id=action.id,
                after=audit.snapshot(action),
            )
        db.commit()
    return list_actions(db, case.id)


def build_roadmap(db: Session, *, case: Case, user: User) -> dict:
    actions = ensure_roadmap(db, case=case, user=user)
    total = len(actions)
    completed = sum(1 for action in actions if action.status == RecoveryStatus.COMPLETED.value)
    overdue_cutoff = datetime.now(UTC)
    overdue = sum(
        1
        for action in actions
        if action.status in planner.OPEN_STATUSES
        and action.due_at is not None
        and action.due_at < overdue_cutoff
    )
    return {
        "case_id": case.id,
        "urgent": planner.is_case_urgent(case),
        "headline": planner.headline(case),
        "emergency_guidance": planner.EMERGENCY_GUIDANCE,
        "actions": actions,
        "progress": {
            "total": total,
            "completed": completed,
            "open": total - completed,
            "overdue": overdue,
        },
    }


def create_action(db: Session, *, case: Case, user: User, data: dict) -> RecoveryAction:
    if case.is_archived:
        raise Conflict("Archived cases are read-only.")
    priority = data.get("priority") or RecoveryPriority.MEDIUM.value
    if priority not in {item.value for item in RecoveryPriority}:
        raise InvalidRequest(f"Unknown priority '{priority}'.")

    action = RecoveryAction(
        case_id=case.id,
        action_type=data["action_type"],
        title=data["title"],
        description=data.get("description"),
        instructions=data.get("instructions"),
        priority=priority,
        due_at=data.get("due_at"),
        assigned_to_user_id=data.get("assigned_to_user_id"),
        status=RecoveryStatus.PENDING.value,
        source="user",
        created_by_user_id=user.id,
    )
    db.add(action)
    db.flush()
    audit.record(
        db,
        action=AuditAction.RECOVERY_ACTION_CREATED,
        actor=user,
        case_id=case.id,
        entity_type="recovery_action",
        entity_id=action.id,
        after=audit.snapshot(action),
    )
    db.commit()
    db.refresh(action)
    return action


_UPDATABLE = {
    "title",
    "description",
    "priority",
    "status",
    "due_at",
    "scheduled_at",
    "outcome_status",
    "outcome_notes",
    "recovered_amount",
    "assigned_to_user_id",
}


def update_action(
    db: Session, *, case: Case, action_id: uuid.UUID, user: User, data: dict
) -> RecoveryAction:
    action = db.get(RecoveryAction, action_id)
    if action is None or action.case_id != case.id:
        raise NotFound("Recovery action not found in this case.")
    if case.is_archived:
        raise Conflict("Archived cases are read-only.")

    changes = {key: value for key, value in data.items() if value is not None}
    if not changes:
        return action

    if "status" in changes and changes["status"] not in {item.value for item in RecoveryStatus}:
        raise InvalidRequest(f"Unknown status '{changes['status']}'.")
    if (
        "priority" in changes
        and changes["priority"] not in {item.value for item in RecoveryPriority}
    ):
        raise InvalidRequest(f"Unknown priority '{changes['priority']}'.")
    if (
        "outcome_status" in changes
        and changes["outcome_status"] not in {item.value for item in RecoveryOutcome}
    ):
        raise InvalidRequest(f"Unknown outcome '{changes['outcome_status']}'.")

    before = audit.snapshot(action)
    for field, value in changes.items():
        if field not in _UPDATABLE:
            raise InvalidRequest(f"Field '{field}' cannot be edited.")
        setattr(action, field, value)

    if changes.get("status") == RecoveryStatus.COMPLETED.value and action.completed_at is None:
        action.completed_at = changes.get("completed_at") or datetime.now(UTC)
    if changes.get("status") and changes["status"] != RecoveryStatus.COMPLETED.value:
        action.completed_at = None
    if action.status == RecoveryStatus.COMPLETED.value and action.outcome_status == "unknown":
        action.outcome_status = "pending"
    action.updated_at = datetime.now(UTC)

    audit.record(
        db,
        action=AuditAction.RECOVERY_ACTION_UPDATED,
        actor=user,
        case_id=case.id,
        entity_type="recovery_action",
        entity_id=action.id,
        before=before,
        after=audit.snapshot(action),
    )
    db.commit()
    db.refresh(action)
    return action
