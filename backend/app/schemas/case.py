import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CaseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=20000)
    incident_type: str = Field(default="unknown", max_length=48)
    fraud_channel: str = Field(default="unknown", max_length=48)
    incident_occurred_at: datetime | None = None
    incident_date: datetime | None = None
    estimated_loss_amount: Decimal | None = Field(default=None, ge=0, le=Decimal("999999999999.99"))
    currency: str = Field(default="INR", min_length=3, max_length=3)
    reporting_details: str | None = Field(default=None, max_length=5000)


class CaseUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=20000)
    incident_type: str | None = Field(default=None, max_length=48)
    fraud_channel: str | None = Field(default=None, max_length=48)
    incident_occurred_at: datetime | None = None
    estimated_loss_amount: Decimal | None = Field(
        default=None, ge=0, le=Decimal("999999999999.99")
    )
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    reporting_details: str | None = Field(default=None, max_length=5000)
    internal_status: str | None = None
    is_disputed: bool | None = None


class CaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    public_reference: str
    title: str
    description: str | None
    incident_type: str
    fraud_channel: str
    incident_occurred_at: datetime | None
    estimated_loss_amount: Decimal | None
    currency: str
    internal_status: str
    completeness_status: str
    is_disputed: bool
    is_archived: bool
    reporting_details: str | None
    created_at: datetime
    updated_at: datetime
    created_by_user_id: uuid.UUID
    assigned_to_user_id: uuid.UUID | None


class CaseSummary(BaseModel):
    case_id: uuid.UUID
    transaction_count: int
    evidence_count: int
    assessment_count: int
    complaint_count: int
    recovery_action_count: int
    open_recovery_actions: int
    total_transaction_amount: Decimal
