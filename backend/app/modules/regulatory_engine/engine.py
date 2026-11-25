"""Assessment orchestration.

Every assessment stores the exact rule version and a hash of the exact input
used. Historical rows are never overwritten; re-evaluating the same rule for
changed facts creates a new assessment that supersedes the previous one.
"""

import hashlib
import json
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import Conflict, InvalidRequest, Unavailable
from app.models import Case, Evidence, RegulatoryAssessment, RegulatoryRule, Transaction, User
from app.modules.audit import service as audit
from app.modules.regulatory_engine import evaluator, loader
from app.utils.enums import AuditAction

DISCLAIMER = (
    "Assessments are deterministic evaluations of recorded facts against stored, "
    "source-referenced rules. They are not legal advice and do not replace a "
    "decision by a bank, regulator or court. Rules whose source has not been "
    "verified are marked as unverified."
)


def _json_safe(value):  # noqa: ANN001
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    return value


def build_input_snapshot(
    case: Case, transactions: list[Transaction], evidence_count: int
) -> dict:
    return {
        "case": {
            "id": str(case.id),
            "public_reference": case.public_reference,
            "incident_type": case.incident_type,
            "fraud_channel": case.fraud_channel,
            "incident_occurred_at": _json_safe(case.incident_occurred_at),
            "estimated_loss_amount": _json_safe(case.estimated_loss_amount),
            "currency": case.currency,
            "is_disputed": case.is_disputed,
            "completeness_status": case.completeness_status,
        },
        "transactions": [
            {
                "id": str(item.id),
                "amount": _json_safe(item.amount),
                "currency": item.currency,
                "direction": item.direction,
                "authorization_type": item.authorization_type,
                "channel": item.channel,
                "transaction_at": _json_safe(item.transaction_at),
            }
            for item in sorted(transactions, key=lambda row: str(row.id))
        ],
        "evidence_count": evidence_count,
    }


def snapshot_hash(snapshot: dict) -> str:
    canonical = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def case_facts(db: Session, case: Case) -> tuple[dict, dict, list[Transaction], int]:
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
    snapshot = build_input_snapshot(case, transactions, evidence_count)
    facts = evaluator.build_facts(case, transactions, evidence_count)
    return facts, snapshot, transactions, evidence_count


def assess(
    db: Session,
    *,
    case: Case,
    rule: RegulatoryRule,
    user: User,
    applicable_on_date: date | None = None,
) -> RegulatoryAssessment:
    on_date = applicable_on_date or datetime.now(UTC).date()
    if rule.status != "active":
        raise InvalidRequest(
            f"Rule {rule.rule_code} v{rule.version} is '{rule.status}' and cannot be applied."
        )
    if rule.effective_from > on_date or (rule.effective_to and rule.effective_to < on_date):
        raise Conflict(
            f"Rule {rule.rule_code} v{rule.version} is not in force on {on_date.isoformat()}."
        )

    facts, snapshot, _, _ = case_facts(db, case)
    try:
        evaluation = evaluator.evaluate(rule.rule_payload, facts, on_date=on_date)
    except evaluator.RulePayloadError as exc:
        raise Conflict(f"Rule payload is invalid: {exc}", code="invalid_rule_payload") from exc

    digest = snapshot_hash(snapshot)
    previous = db.scalar(
        select(RegulatoryAssessment)
        .where(
            RegulatoryAssessment.case_id == case.id,
            RegulatoryAssessment.rule_code == rule.rule_code,
        )
        .order_by(RegulatoryAssessment.assessed_at.desc())
        .limit(1)
    )
    if (
        previous is not None
        and previous.rule_id == rule.id
        and previous.input_snapshot_hash == digest
        and previous.applicable_on_date == on_date
    ):
        # No new facts and no rule change: the stored assessment already answers this.
        return previous

    assessment = RegulatoryAssessment(
        case_id=case.id,
        rule_id=rule.id,
        rule_code=rule.rule_code,
        rule_version=rule.version,
        rule_title=rule.title,
        rule_authority=rule.authority,
        rule_source_reference=rule.source_reference,
        rule_source_url=rule.source_url,
        rule_verification_status=rule.verification_status,
        result_status=evaluation.result_status,
        explanation=evaluation.explanation,
        matched_conditions=evaluation.matched,
        unmatched_conditions=evaluation.unmatched,
        missing_facts=evaluation.missing,
        input_snapshot=snapshot,
        input_snapshot_hash=digest,
        incident_occurred_at_snapshot=case.incident_occurred_at,
        applicable_on_date=on_date,
        engine_version=settings.regulatory_engine_version,
        schema_version=settings.regulatory_schema_version,
        assessed_at=datetime.now(UTC),
        assessed_by_user_id=user.id,
        supersedes_assessment_id=previous.id if previous else None,
    )
    db.add(assessment)
    db.flush()

    audit.record(
        db,
        action=AuditAction.ASSESSMENT_CREATED,
        actor=user,
        case_id=case.id,
        entity_type="regulatory_assessment",
        entity_id=assessment.id,
        after={
            "rule_code": rule.rule_code,
            "rule_version": rule.version,
            "result_status": assessment.result_status,
            "input_snapshot_hash": digest,
            "supersedes": str(previous.id) if previous else None,
        },
    )
    db.commit()
    db.refresh(assessment)
    return assessment


def assess_case(
    db: Session,
    *,
    case: Case,
    user: User,
    rule_code: str | None = None,
    applicable_on_date: date | None = None,
) -> list[RegulatoryAssessment]:
    on_date = applicable_on_date or datetime.now(UTC).date()
    rules = loader.active_rules(db, on_date=on_date, rule_code=rule_code)
    if not rules:
        raise Unavailable(
            "No active regulatory rules are available for that date. Rules must be "
            "seeded and verified before an assessment can be produced.",
            code="no_active_rules",
        )
    return [
        assess(db, case=case, rule=rule, user=user, applicable_on_date=on_date)
        for rule in rules
    ]


def assessments_for_case(db: Session, case_id: uuid.UUID) -> list[RegulatoryAssessment]:
    statement = (
        select(RegulatoryAssessment)
        .where(RegulatoryAssessment.case_id == case_id)
        .order_by(RegulatoryAssessment.assessed_at.desc(), RegulatoryAssessment.rule_code)
    )
    return list(db.scalars(statement))


def review_assessment(
    db: Session,
    *,
    assessment: RegulatoryAssessment,
    user: User,
    review_status: str,
    review_note: str | None,
) -> RegulatoryAssessment:
    valid = {"unreviewed", "confirmed", "rejected", "disputed"}
    if review_status not in valid:
        raise InvalidRequest(f"Unknown review status '{review_status}'.")
    before = {
        "review_status": assessment.review_status,
        "review_note": assessment.review_note,
    }
    assessment.review_status = review_status
    assessment.reviewed_by_user_id = user.id
    assessment.reviewed_at = datetime.now(UTC)
    assessment.review_note = review_note

    audit.record(
        db,
        action=AuditAction.ASSESSMENT_REVIEWED,
        actor=user,
        case_id=assessment.case_id,
        entity_type="regulatory_assessment",
        entity_id=assessment.id,
        before=before,
        after={"review_status": review_status, "review_note": review_note},
    )
    db.commit()
    db.refresh(assessment)
    return assessment


def get_assessment(db: Session, assessment_id: uuid.UUID) -> RegulatoryAssessment | None:
    return db.get(RegulatoryAssessment, assessment_id)
