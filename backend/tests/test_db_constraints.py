"""Database-level integrity tests.

These assert guarantees that live in PostgreSQL, not in Python: the composite
same-case foreign key, append-only history, the write-once assessment guard and
the immutable-active-rule guard.
"""

import uuid
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.models import (
    Case,
    Complaint,
    Evidence,
    RegulatoryAssessment,
    RegulatoryRule,
    Transaction,
    User,
)
from app.utils.enums import Role


def make_user(db, email: str = "db@example.com") -> User:
    from app.core.security import hash_password

    user = User(
        email=email,
        full_name="DB Test",
        password_hash=hash_password("correct-horse-battery"),
        role=Role.CITIZEN.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_case(db, user: User) -> Case:
    case = Case(
        public_reference=f"FT-TEST-{uuid.uuid4().hex[:6].upper()}",
        created_by_user_id=user.id,
        title="Constraint case",
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def test_evidence_cannot_reference_a_transaction_from_another_case(db) -> None:
    user = make_user(db)
    case_a = make_case(db, user)
    case_b = make_case(db, user)

    transaction = Transaction(
        case_id=case_a.id, amount=100, currency="INR", direction="debit"
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    # case_id points at case B while the transaction belongs to case A: the
    # composite foreign key must reject this.
    evidence = Evidence(
        case_id=case_b.id,
        transaction_id=transaction.id,
        uploaded_by_user_id=user.id,
        original_filename="alert.txt",
        stored_path="cases/x/aa/hash.txt",
        content_type="text/plain",
        byte_size=10,
        sha256_hash="a" * 64,
    )
    db.add(evidence)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_duplicate_evidence_hashes_are_allowed(db) -> None:
    user = make_user(db)
    case = make_case(db, user)
    for index in range(2):
        db.add(
            Evidence(
                case_id=case.id,
                uploaded_by_user_id=user.id,
                original_filename=f"alert-{index}.txt",
                stored_path=f"cases/x/aa/hash-{index}.txt",
                content_type="text/plain",
                byte_size=10,
                sha256_hash="b" * 64,
            )
        )
    db.commit()

    count = db.execute(
        text("select count(*) from evidence where sha256_hash = :h"), {"h": "b" * 64}
    ).scalar_one()
    assert count == 2


def test_audit_events_cannot_be_updated_or_deleted(db) -> None:
    user = make_user(db)
    db.execute(
        text(
            "insert into audit_events (action, entity_type, entity_id) "
            "values ('test.event', 'test', '1')"
        )
    )
    db.commit()

    with pytest.raises(DBAPIError):
        db.execute(text("update audit_events set action = 'tampered'"))
        db.commit()
    db.rollback()

    with pytest.raises(DBAPIError):
        db.execute(text("delete from audit_events"))
        db.commit()
    db.rollback()


def test_complaint_status_events_are_append_only(db) -> None:
    user = make_user(db)
    case = make_case(db, user)
    complaint = Complaint(
        case_id=case.id,
        channel="bank",
        submission_status="draft",
        created_by_user_id=user.id,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    db.execute(
        text(
            "insert into complaint_status_events "
            "(complaint_id, observed_status, checked_at, recorded_by_user_id) "
            "values (:c, 'pending', now(), :u)"
        ),
        {"c": complaint.id, "u": user.id},
    )
    db.commit()

    with pytest.raises(DBAPIError):
        db.execute(text("update complaint_status_events set observed_status = 'closed'"))
        db.commit()
    db.rollback()


def _seed_assessment(db, case: Case, user: User) -> RegulatoryAssessment:
    rule = RegulatoryRule(
        rule_code="DB-RULE",
        version=1,
        title="Guard test rule",
        jurisdiction="IN",
        authority="Unverified example",
        source_reference="Guard test",
        effective_from=date(2020, 1, 1),
        rule_payload={"logic": "all", "conditions": []},
        status="active",
        verification_status="unverified",
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    assessment = RegulatoryAssessment(
        case_id=case.id,
        rule_id=rule.id,
        rule_code=rule.rule_code,
        rule_version=rule.version,
        rule_title=rule.title,
        rule_authority=rule.authority,
        rule_source_reference=rule.source_reference,
        rule_verification_status=rule.verification_status,
        result_status="inconclusive",
        explanation="Guard test.",
        input_snapshot={"case": {"id": str(case.id)}},
        input_snapshot_hash="c" * 64,
        applicable_on_date=date(2026, 11, 24),
        engine_version="1.0.0",
        schema_version="1.0",
        assessed_at=datetime.now(UTC),
        assessed_by_user_id=user.id,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


def test_assessment_result_columns_are_write_once(db) -> None:
    user = make_user(db)
    case = make_case(db, user)
    assessment = _seed_assessment(db, case, user)

    with pytest.raises(DBAPIError):
        db.execute(
            text("update regulatory_assessments set result_status = 'applies' where id = :i"),
            {"i": assessment.id},
        )
        db.commit()
    db.rollback()

    # Review fields remain mutable.
    db.execute(
        text(
            "update regulatory_assessments set review_status = 'confirmed', "
            "reviewed_by_user_id = :u, reviewed_at = now() where id = :i"
        ),
        {"i": assessment.id, "u": user.id},
    )
    db.commit()

    db.refresh(assessment)
    assert assessment.review_status == "confirmed"


def test_active_rule_payload_is_immutable(db) -> None:
    user = make_user(db)
    case = make_case(db, user)
    _seed_assessment(db, case, user)

    with pytest.raises(DBAPIError):
        db.execute(text("update regulatory_rules set rule_payload = '{}'::jsonb"))
        db.commit()
    db.rollback()


def test_cases_reject_invalid_currency_length(db) -> None:
    user = make_user(db)
    case = Case(
        public_reference="FT-TEST-CURR1",
        created_by_user_id=user.id,
        title="Currency case",
        currency="RUPEES",
    )
    db.add(case)
    # The column is varchar(3), so PostgreSQL rejects the value rather than
    # storing a silently truncated currency code.
    with pytest.raises(DBAPIError):
        db.commit()
    db.rollback()
