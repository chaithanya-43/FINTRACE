import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    transaction_id: uuid.UUID | None
    original_filename: str
    content_type: str
    byte_size: int
    sha256_hash: str
    evidence_type: str
    description: str | None
    verification_status: str
    verified_at: datetime | None
    chain_of_custody: list | dict | None
    created_at: datetime


class SignatureRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    key_id_snapshot: str
    algorithm: str
    signature_b64: str
    signed_at: datetime
    verified_at: datetime | None
    verification_result: str


class EvidenceVerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Optional: verify a specific signature together with the stored bytes.
    signature_id: uuid.UUID | None = None


class EvidenceVerifyResponse(BaseModel):
    evidence_id: uuid.UUID
    stored_hash: str
    recomputed_hash: str
    hash_matches: bool
    verification_status: str
    signature_status: str
    signed: bool
    notes: list[str]


class SignEvidenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key_id: str | None = None
