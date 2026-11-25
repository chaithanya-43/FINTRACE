# API contracts

FastAPI generates OpenAPI documentation automatically.

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

All routes are versioned under `/api/v1`. Endpoints are implemented in
`backend/app/api/v1/endpoints/` and delegate business logic to `backend/app/modules/`.

## Authentication

Every route except `POST /auth/register`, `POST /auth/login` and `/health` requires an
`Authorization: Bearer <token>` header.

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/register` | Create a citizen account and return a token |
| POST | `/auth/login` | Exchange email/password for a token |
| GET | `/auth/me` | Current user profile |

Passwords are hashed with Argon2id. Tokens are HS256 JWTs carrying the user id and a role
snapshot; the role is re-read from the database on every request, so a change takes effect
immediately.

`role` is never accepted from a client: registration always creates a `citizen`.

## Cases

| Method | Path | Purpose |
|---|---|---|
| GET | `/dashboard/summary` | Counts and recent cases computed from stored data |
| POST | `/cases` | Create a case |
| GET | `/cases` | List visible cases (`include_archived`, `limit`, `offset`) |
| GET | `/cases/{case_id}` | Read one case |
| GET | `/cases/{case_id}/summary` | Counts for one case |
| PATCH | `/cases/{case_id}` | Update editable fields or the internal status |
| POST | `/cases/{case_id}/status` | Transition the internal status |
| POST | `/cases/{case_id}/archive` | Archive (records are retained, further edits rejected) |
| GET | `/cases/{case_id}/progress` | Status, completeness and step list |
| POST | `/cases/{case_id}/analyze` | Deterministic incident analysis |
| GET | `/cases/{case_id}/audit` | Append-only audit trail |

Visibility: a citizen sees only cases they created; an investigator sees cases they created
or were assigned; an administrator sees all. Accessing another user's case returns `404`,
not `403`, so existence is not disclosed.

## Transactions

| Method | Path | Purpose |
|---|---|---|
| GET | `/cases/{case_id}/transactions` | List transactions |
| POST | `/cases/{case_id}/transactions` | Add a transaction |
| PATCH | `/cases/{case_id}/transactions/{transaction_id}` | Update a transaction |

`amount` must be greater than zero, `currency` is a three-letter code (INR by default), and
a UTR reference may not repeat inside one case (`409 duplicate_utr`). Free text containing
an OTP, PIN, CVV or password is rejected (`400 sensitive_data_rejected`).

## Regulatory intelligence

| Method | Path | Purpose |
|---|---|---|
| GET | `/regulatory-rules` | All stored rules, newest version first |
| GET | `/cases/{case_id}/regulations` | Rules in force for the case date |
| POST | `/cases/{case_id}/assessments` | Run assessments (`rule_code` optional) |
| GET | `/cases/{case_id}/assessments` | Assessment history plus disclaimer |
| PATCH | `/assessments/{assessment_id}/review` | Human review (only mutable columns) |

An assessment stores the rule version, rule payload snapshot, input snapshot and its
SHA-256 hash, the applicable date and the engine version. Re-running with identical facts
and the same rule returns the stored assessment instead of duplicating it; changed facts
create a new row that sets `supersedes_assessment_id`. If no active rule exists the API
returns `503 no_active_rules`.

## Evidence

| Method | Path | Purpose |
|---|---|---|
| GET | `/cases/{case_id}/evidence` | List evidence metadata |
| POST | `/cases/{case_id}/evidence` | Multipart upload (`file`, `evidence_type`, `description`, `transaction_id`, `collected_at`) |
| GET | `/cases/{case_id}/evidence/{evidence_id}` | Read metadata |
| GET | `/cases/{case_id}/evidence/{evidence_id}/download` | Authorised stream (`X-Evidence-SHA256` header) |
| POST | `/cases/{case_id}/evidence/{evidence_id}/verify` | Recompute the hash and check signatures |
| POST | `/cases/{case_id}/evidence/{evidence_id}/sign` | Ed25519 sign (requires configuration) |
| GET | `/cases/{case_id}/evidence/{evidence_id}/signatures` | Signature records |

Uploads are rejected above `MAX_UPLOAD_BYTES` (`413 file_too_large`) or for disallowed
content types (`400 unsupported_file_type`). Files are written outside any served directory
under a content-derived path, and are only reachable through the authorised download route.

Evidence with an identical hash may be uploaded again: duplicate bytes are a provenance
signal, not an error.

Signing returns `503 signing_unavailable` when no key is configured. It never reports a
signature it did not produce.

## Recovery

| Method | Path | Purpose |
|---|---|---|
| GET | `/cases/{case_id}/roadmap` | Roadmap (creates missing recommended actions) |
| GET | `/cases/{case_id}/actions` | List actions |
| POST | `/cases/{case_id}/actions` | Record a user action |
| PATCH | `/cases/{case_id}/actions/{action_id}` | Update status, priority, outcome |

The roadmap is idempotent: an action type is only created once per case, so a user's own
edits are never overwritten.

## Complaints

| Method | Path | Purpose |
|---|---|---|
| GET | `/cases/{case_id}/complaints` | List complaints |
| POST | `/cases/{case_id}/complaints` | Record a complaint the user filed |
| PATCH | `/cases/{case_id}/complaints/{complaint_id}` | Update submission status or reference |
| GET | `/cases/{case_id}/complaints/{complaint_id}/history` | Status observations, oldest first |
| POST | `/cases/{case_id}/complaints/{complaint_id}/history` | Append an observation |

`official_status` is `null` until an observation exists; a missing value is information, not
a default. Observations are append-only and an identical `(complaint, checked_at, status)`
is rejected with `409 duplicate_observation`.

FINTRACE has no integration that submits a complaint anywhere.

## Administration

| Method | Path | Purpose |
|---|---|---|
| GET | `/admin/users` | List users (administrator only) |
| PATCH | `/admin/users/{user_id}/role` | Change a role |
| PATCH | `/admin/users/{user_id}/status` | Lock, suspend or deactivate |

## Errors

Every failure uses one envelope:

```json
{
  "error": {
    "code": "duplicate_utr",
    "message": "A transaction with this UTR reference already exists in this case.",
    "details": null
  }
}
```

Validation errors return `422` with `details` as a list of `{field, message}`.

Status codes in use: `400` invalid input or rejected sensitive text, `401` missing/expired
token, `403` role or account-state refusal, `404` missing or not visible, `409` conflict or
invalid transition, `413` upload too large, `422` schema validation, `503` unavailable
feature or no active rules.

## Contract conventions

- Keep versioned routes under `/api/v1`.
- Use Pydantic schemas for public request and response shapes.
- Return structured validation and error responses.
- Document sensitive fields and retention behavior explicitly.
- Future multilingual fields should use extensible schema design rather than hard-coded
  language variants.
