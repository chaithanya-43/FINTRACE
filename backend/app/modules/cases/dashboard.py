"""Dashboard aggregates computed from real case data."""

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import visible_case_query
from app.models import Case, RecoveryAction, User
from app.modules.recovery import planner
from app.utils.enums import CaseStatus


def summary(db: Session, *, user: User) -> dict:
    visible = visible_case_query(user)
    total = int(db.scalar(select(func.count()).select_from(visible.subquery())) or 0)

    cases = list(
        db.scalars(
            visible.where(Case.is_archived.is_(False)).order_by(Case.created_at.desc()).limit(200)
        )
    )
    active = sum(1 for case in cases if case.internal_status != CaseStatus.CLOSED.value)

    case_ids = [case.id for case in cases]
    open_actions = 0
    if case_ids:
        open_actions = int(
            db.scalar(
                select(func.count())
                .select_from(RecoveryAction)
                .where(
                    RecoveryAction.case_id.in_(case_ids),
                    RecoveryAction.status.in_(planner.OPEN_STATUSES),
                )
            )
            or 0
        )

    requiring_action = 0
    for case in cases:
        if case.internal_status == CaseStatus.CLOSED.value:
            continue
        if planner.is_case_urgent(case) or case.completeness_status != "complete":
            requiring_action += 1

    loss_total = Decimal("0")
    for case in cases:
        if case.estimated_loss_amount is not None:
            loss_total += case.estimated_loss_amount

    recent = [
        {
            "id": str(case.id),
            "public_reference": case.public_reference,
            "title": case.title,
            "incident_type": case.incident_type,
            "internal_status": case.internal_status,
            "completeness_status": case.completeness_status,
            "created_at": case.created_at.isoformat(),
            "estimated_loss_amount": float(case.estimated_loss_amount)
            if case.estimated_loss_amount is not None
            else None,
        }
        for case in cases[:8]
    ]

    return {
        "total_cases": total,
        "active_cases": active,
        "cases_requiring_action": requiring_action,
        "open_recovery_actions": open_actions,
        "total_estimated_loss": float(loss_total),
        "recent_cases": recent,
    }
