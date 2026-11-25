import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class RecoveryActionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_type: str
    title: str = Field(min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    instructions: str | None = Field(default=None, max_length=5000)
    priority: str = Field(default="medium")
    due_at: datetime | None = None
    assigned_to_user_id: uuid.UUID | None = None


class RecoveryActionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    priority: str | None = None
    status: str | None = None
    due_at: datetime | None = None
    scheduled_at: datetime | None = None
    completed_at: datetime | None = None
    outcome_status: str | None = None
    outcome_notes: str | None = Field(default=None, max_length=5000)
    recovered_amount: Decimal | None = Field(default=None, ge=0)
    assigned_to_user_id: uuid.UUID | None = None


class RecoveryActionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    action_type: str
    title: str
    description: str | None
    instructions: str | None
    priority: str
    status: str
    source: str
    due_at: datetime | None
    scheduled_at: datetime | None
    completed_at: datetime | None
    outcome_status: str
    outcome_notes: str | None
    recovered_amount: Decimal | None
    assigned_to_user_id: uuid.UUID | None
    created_at: datetime


class RoadmapResponse(BaseModel):
    case_id: uuid.UUID
    urgent: bool
    headline: str
    emergency_guidance: list[str]
    actions: list[RecoveryActionRead]
    progress: dict
