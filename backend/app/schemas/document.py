import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentFieldSpec(BaseModel):
    key: str
    label: str
    section: str
    type: str
    options: list[str] | None = None


class DocumentCatalogItem(BaseModel):
    document_type: str
    code: str
    title: str
    short_description: str
    default_recipient: str
    required_information: list[str]
    extra_fields: list[DocumentFieldSpec]
    attachments: list[str]


class DocumentMissingItem(BaseModel):
    key: str
    label: str
    severity: str


class AttachmentChecklistItem(BaseModel):
    label: str
    available: bool
    note: str | None = None


class DocumentPrefillResponse(BaseModel):
    document_type: str
    spec: DocumentCatalogItem
    case_summary: dict
    prefilled_answers: dict[str, str]
    missing_information: list[DocumentMissingItem]
    attachments_checklist: list[AttachmentChecklistItem]


class DocumentGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_type: str
    intake_answers: dict[str, str] | None = None


class DocumentDraftUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=3, max_length=200)
    recipient: str | None = Field(default=None, min_length=2, max_length=240)
    subject: str | None = Field(default=None, min_length=2, max_length=300)
    content: str | None = Field(default=None, min_length=10, max_length=40000)
    draft_status: str | None = None
    intake_answers: dict[str, str] | None = None
    attachments_checklist: list[dict] | None = None


class DocumentDraftRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    created_by_user_id: uuid.UUID
    document_type: str
    title: str
    recipient: str
    subject: str
    content: str
    intake_answers: dict | None
    attachments_checklist: list | None
    draft_status: str
    created_at: datetime
    updated_at: datetime
