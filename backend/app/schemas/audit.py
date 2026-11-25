import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: uuid.UUID | None
    actor_user_id: uuid.UUID | None
    actor_role: str | None
    action: str
    entity_type: str | None
    entity_id: str | None
    before_state: dict | None
    after_state: dict | None
    created_at: datetime


class AnalysisResponse(BaseModel):
    case_id: uuid.UUID
    engine: str
    provider_configured: bool
    summary: str
    suggested_incident_type: str
    suggested_fraud_channel: str
    confidence_note: str
    extracted_facts: list[dict]
    missing_information: list[str]
    suggested_next_steps: list[str]
    fact_provenance: dict


class DashboardSummary(BaseModel):
    total_cases: int
    active_cases: int
    cases_requiring_action: int
    open_recovery_actions: int
    total_estimated_loss: float
    recent_cases: list[dict]
