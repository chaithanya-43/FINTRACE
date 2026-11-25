import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class RuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rule_code: str
    version: int
    title: str
    jurisdiction: str
    authority: str
    source_reference: str
    source_url: str | None
    effective_from: date
    effective_to: date | None
    status: str
    verification_status: str
    notes: str | None


class AssessmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    rule_id: uuid.UUID
    rule_code: str
    rule_version: int
    rule_title: str
    rule_authority: str
    rule_source_reference: str
    rule_source_url: str | None
    rule_verification_status: str
    result_status: str
    explanation: str
    matched_conditions: list | None
    unmatched_conditions: list | None
    missing_facts: list | None
    input_snapshot: dict
    input_snapshot_hash: str
    applicable_on_date: date
    engine_version: str
    schema_version: str
    assessed_at: datetime
    review_status: str
    reviewed_at: datetime | None
    review_note: str | None
    supersedes_assessment_id: uuid.UUID | None


class AssessmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_code: str | None = None
    applicable_on_date: date | None = None


class AssessmentReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_status: str
    review_note: str | None = None


class RuleEvaluationRead(BaseModel):
    rule: RuleRead
    result_status: str
    explanation: str
    matched_conditions: list
    unmatched_conditions: list
    missing_facts: list


class AssessmentListResponse(BaseModel):
    assessments: list[AssessmentRead]
    disclaimer: str
