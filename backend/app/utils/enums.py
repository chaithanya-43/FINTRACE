"""Vocabulary shared by models, schemas and services.

Fixed, security-relevant vocabularies are mirrored by database CHECK
constraints. The values here are the single Python source of truth.
"""

from enum import StrEnum


class Role(StrEnum):
    CITIZEN = "citizen"
    INVESTIGATOR = "investigator"
    ADMINISTRATOR = "administrator"


class AccountStatus(StrEnum):
    ACTIVE = "active"
    LOCKED = "locked"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


class CaseStatus(StrEnum):
    INTAKE = "intake"
    COLLECTING_EVIDENCE = "collecting_evidence"
    ASSESSMENT = "assessment"
    RECOVERY = "recovery"
    CLOSED = "closed"


class CompletenessStatus(StrEnum):
    INCOMPLETE = "incomplete"
    PARTIAL = "partial"
    COMPLETE = "complete"


class Direction(StrEnum):
    DEBIT = "debit"
    CREDIT = "credit"


class AuthorizationType(StrEnum):
    UNAUTHORIZED = "unauthorized"
    AUTHORIZED_DECEIVED = "authorized_deceived"
    UNKNOWN = "unknown"


class TransactionStatus(StrEnum):
    REPORTED = "reported"
    DISPUTED = "disputed"
    REVERSED = "reversed"
    CHARGEBACK = "chargeback"
    UNRESOLVED = "unresolved"


class RecordSource(StrEnum):
    USER = "user"
    EVIDENCE = "evidence"
    EXTRACTED = "extracted"


class VerificationStatus(StrEnum):
    UNVERIFIED = "unverified"
    USER_CONFIRMED = "user_confirmed"
    DISPUTED = "disputed"


class EvidenceVerificationStatus(StrEnum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    FAILED = "failed"


class ResultStatus(StrEnum):
    APPLIES = "applies"
    MAY_APPLY = "may_apply"
    DOES_NOT_APPLY = "does_not_apply"
    INCONCLUSIVE = "inconclusive"
    DISPUTED = "disputed"


class ReviewStatus(StrEnum):
    UNREVIEWED = "unreviewed"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    DISPUTED = "disputed"


class RuleStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"


class RuleVerificationStatus(StrEnum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"


class SubmissionStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class RecoveryPriority(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecoveryStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


class RecoveryOutcome(StrEnum):
    UNKNOWN = "unknown"
    PENDING = "pending"
    RECOVERED = "recovered"
    PARTIALLY_RECOVERED = "partially_recovered"
    NOT_RECOVERED = "not_recovered"


class KeyStatus(StrEnum):
    ACTIVE = "active"
    RETIRED = "retired"
    REVOKED = "revoked"


class AuditAction(StrEnum):
    USER_REGISTERED = "user.registered"
    USER_LOGGED_IN = "user.logged_in"
    USER_LOGIN_FAILED = "user.login_failed"
    USER_ROLE_CHANGED = "user.role_changed"
    CASE_CREATED = "case.created"
    CASE_UPDATED = "case.updated"
    CASE_ARCHIVED = "case.archived"
    CASE_STATUS_CHANGED = "case.status_changed"
    TRANSACTION_CREATED = "transaction.created"
    TRANSACTION_UPDATED = "transaction.updated"
    EVIDENCE_UPLOADED = "evidence.uploaded"
    EVIDENCE_VERIFIED = "evidence.verified"
    EVIDENCE_VERIFICATION_FAILED = "evidence.verification_failed"
    ASSESSMENT_CREATED = "assessment.created"
    ASSESSMENT_REVIEWED = "assessment.reviewed"
    RECOVERY_ACTION_CREATED = "recovery_action.created"
    RECOVERY_ACTION_UPDATED = "recovery_action.updated"
    COMPLAINT_CREATED = "complaint.created"
    COMPLAINT_UPDATED = "complaint.updated"
    COMPLAINT_STATUS_OBSERVED = "complaint.status_observed"


FRAUD_CATEGORIES: tuple[str, ...] = (
    "upi_fraud",
    "card_fraud",
    "net_banking_fraud",
    "investment_fraud",
    "loan_app_fraud",
    "job_offer_fraud",
    "otp_phishing",
    "sextortion",
    "sim_swap",
    "impersonation",
    "merchant_fraud",
    "unknown",
)

FRAUD_CHANNELS: tuple[str, ...] = (
    "upi",
    "card",
    "net_banking",
    "whatsapp",
    "phone_call",
    "sms",
    "email",
    "social_media",
    "mobile_app",
    "in_person",
    "unknown",
)

COMPLAINT_CHANNELS: tuple[str, ...] = (
    "cybercrime_portal",
    "bank",
    "nodal_officer",
    "police_station",
    "rbi_ombudsman",
    "other",
)

RECOVERY_ACTION_TYPES: tuple[str, ...] = (
    "report_cybercrime",
    "call_helpline",
    "contact_bank",
    "freeze_account",
    "chargeback_request",
    "prepare_complaint",
    "follow_up",
    "preserve_evidence",
)
