import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ComplaintCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel: str
    organisation_name: str | None = Field(default=None, max_length=200)
    reference_number: str | None = Field(default=None, max_length=120)
    submission_status: str = Field(default="draft")
    filed_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=5000)


class ComplaintUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel: str | None = None
    organisation_name: str | None = Field(default=None, max_length=200)
    reference_number: str | None = Field(default=None, max_length=120)
    submission_status: str | None = None
    filed_at: datetime | None = None
    acknowledged_at: datetime | None = None
    closed_at: datetime | None = None
    is_disputed: bool | None = None


class StatusEventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observed_status: str = Field(min_length=1, max_length=48)
    status_detail: str | None = Field(default=None, max_length=5000)
    source_url: str | None = Field(default=None, max_length=2000)
    checked_at: datetime | None = None


class StatusEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    observed_status: str
    status_detail: str | None
    source_url: str | None
    checked_at: datetime
    recorded_by_user_id: uuid.UUID
    created_at: datetime


class ComplaintRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    channel: str
    organisation_name: str | None
    reference_number: str | None
    submission_status: str
    official_status: str | None
    official_status_detail: str | None
    official_status_source_url: str | None
    is_disputed: bool
    filed_at: datetime | None
    acknowledged_at: datetime | None
    closed_at: datetime | None
    last_checked_at: datetime | None
    created_at: datetime
