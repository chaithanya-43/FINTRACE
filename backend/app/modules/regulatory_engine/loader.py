"""Rule loading. Only active, in-force rules are ever evaluated."""

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import RegulatoryRule
from app.utils.enums import RuleStatus


def active_rules(
    db: Session,
    *,
    on_date: date | None = None,
    rule_code: str | None = None,
) -> list[RegulatoryRule]:
    effective_on = on_date or datetime.now().date()
    statement = select(RegulatoryRule).where(
        RegulatoryRule.status == RuleStatus.ACTIVE.value,
        RegulatoryRule.effective_from <= effective_on,
    )
    if rule_code:
        statement = statement.where(RegulatoryRule.rule_code == rule_code)
    rules = list(db.scalars(statement.order_by(RegulatoryRule.rule_code)))

    return [
        rule
        for rule in rules
        if rule.effective_to is None or rule.effective_to >= effective_on
    ]


def all_rules(db: Session) -> list[RegulatoryRule]:
    statement = select(RegulatoryRule).order_by(
        RegulatoryRule.rule_code, RegulatoryRule.version.desc()
    )
    return list(db.scalars(statement))
