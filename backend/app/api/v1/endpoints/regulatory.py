import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, load_authorized_case, require_roles
from app.core.exceptions import NotFound
from app.database.connection import get_db
from app.models import User
from app.modules.regulatory_engine import engine, loader
from app.schemas.regulatory import (
    AssessmentRead,
    AssessmentRequest,
    AssessmentReviewRequest,
    AssessmentListResponse,
    RuleRead,
)
from app.utils.enums import Role

router = APIRouter(tags=["regulatory"])


@router.get("/regulatory-rules", response_model=list[RuleRead])
def list_rules(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[RuleRead]:
    return [RuleRead.model_validate(rule) for rule in loader.all_rules(db)]


@router.get("/cases/{case_id}/regulations", response_model=list[RuleRead])
def active_regulations(
    case_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[RuleRead]:
    """Rules in force for this case, whether or not an assessment was run."""
    case = load_authorized_case(case_id, user, db)
    on_date = case.incident_occurred_at.date() if case.incident_occurred_at else None
    rules = loader.active_rules(db, on_date=on_date)
    if not rules:
        return []
    return [RuleRead.model_validate(rule) for rule in rules]


@router.post(
    "/cases/{case_id}/assessments",
    response_model=list[AssessmentRead],
    status_code=status.HTTP_201_CREATED,
)
def create_assessment(
    case_id: uuid.UUID,
    payload: AssessmentRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AssessmentRead]:
    case = load_authorized_case(case_id, user, db)
    produced = engine.assess_case(
        db,
        case=case,
        user=user,
        rule_code=payload.rule_code,
        applicable_on_date=payload.applicable_on_date,
    )
    return [AssessmentRead.model_validate(item) for item in produced]


@router.get(
    "/cases/{case_id}/assessments", response_model=AssessmentListResponse
)
def list_assessments(
    case_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssessmentListResponse:
    load_authorized_case(case_id, user, db)
    assessments = engine.assessments_for_case(db, case_id)
    return AssessmentListResponse(
        assessments=[AssessmentRead.model_validate(item) for item in assessments],
        disclaimer=engine.DISCLAIMER,
    )


@router.patch("/assessments/{assessment_id}/review", response_model=AssessmentRead)
def review_assessment(
    assessment_id: uuid.UUID,
    payload: AssessmentReviewRequest,
    user: User = Depends(require_roles(Role.INVESTIGATOR.value, Role.ADMINISTRATOR.value)),
    db: Session = Depends(get_db),
) -> AssessmentRead:
    assessment = engine.get_assessment(db, assessment_id)
    if assessment is None:
        raise NotFound("Assessment not found.")
    load_authorized_case(assessment.case_id, user, db)
    assessment = engine.review_assessment(
        db,
        assessment=assessment,
        user=user,
        review_status=payload.review_status,
        review_note=payload.review_note,
    )
    return AssessmentRead.model_validate(assessment)
