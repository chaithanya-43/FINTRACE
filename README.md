# FINTRACE

FINTRACE is a modular monolith for India's financial fraud intelligence and recovery
ecosystem. It registers incidents and cases, classifies fraud intelligence, applies
source-backed regulatory rules deterministically, preserves evidence integrity, and plans
recovery actions with traceable complaint history.

This repository now contains a **working end-to-end prototype**: FastAPI + PostgreSQL +
Alembic backend, and a React/Vite dashboard that uses the real API.

## Problem

Victims and investigators often work across fragmented complaint channels and evidence
sources. FINTRACE organises incident information, preserves evidence provenance, supports
consistent regulatory workflows, and tracks recovery progress without presenting
AI-generated material as an authoritative legal or regulatory decision.

## What is implemented

| Capability | Status |
|---|---|
| Registration, login, JWT sessions, Argon2id hashing | Implemented |
| Role-based access (citizen, investigator, administrator) | Implemented |
| Case lifecycle with enforced status transitions, archive | Implemented |
| Transaction records with provenance and UTR uniqueness per case | Implemented |
| Incident analysis: classification, extraction, gaps, next steps | Implemented (deterministic, no external model) |
| Versioned regulatory rules, deterministic evaluation, assessment history | Implemented |
| Human review of assessments (review columns only) | Implemented |
| Private evidence storage, SHA-256 hashing, verification, retrieval | Implemented |
| Ed25519 signing and signature checks | Implemented, requires key configuration |
| Recovery roadmap with priorities, due dates and outcomes | Implemented |
| Complaints with append-only status observation history | Implemented |
| Append-only audit trail across the domain | Implemented |
| Dashboard, case workspace, evidence, recovery and complaint screens | Implemented |

## Technology stack

- Frontend: React, Vite, JavaScript
- Backend: Python, FastAPI
- Database: PostgreSQL
- ORM: SQLAlchemy 2.0
- Migrations: Alembic
- API documentation: OpenAPI / Swagger
- Configuration: Pydantic Settings and environment variables
- Testing: Pytest (against PostgreSQL) and Vitest

## Architecture

FINTRACE uses a modular monolith. API routes remain thin, business logic lives in backend
modules, SQLAlchemy models remain separate from Pydantic schemas, and database sessions are
provided through dependency injection.

See [Architecture](docs/architecture.md), [Database design](docs/database-design.md),
[API contracts](docs/api-contracts.md), [Development guide](docs/development-guide.md), and
[Security guidelines](docs/security-guidelines.md).

## Project structure

```text
frontend/   React application
backend/    FastAPI application, models, migrations and tests
docs/       Architecture and operating documentation
scripts/    Rule seeding and end-to-end smoke test
storage/    Private local evidence area (not committed)
```

## Local setup

Prerequisites:

- Docker with Compose (or a local PostgreSQL 16 server)
- Python 3.11+
- Node.js 20+

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Replace the placeholders. `JWT_SECRET` must be a real random value, and `DATABASE_URL` must
point at your PostgreSQL database.

### Database

```bash
docker compose up -d postgres
cd backend && alembic upgrade head
cd .. && python scripts/seed_regulatory_rules.py
```

The seeded rules are example configurations marked **unverified**. Replace them with rules
transcribed from reviewed primary sources before relying on any assessment.

### Backend

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --reload
```

The API is available at `http://localhost:8000`, with Swagger at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend is available at `http://localhost:5173`.

## Testing

```bash
# Backend: requires a disposable PostgreSQL database
export TEST_DATABASE_URL="postgresql+psycopg://fintrace:fintrace@localhost:5432/fintrace_test"
cd backend && pytest

# Frontend
cd frontend && npm test && npm run build

# End to end, with the API running
python scripts/smoke_test.py
```

The backend suite runs against PostgreSQL because the guarantees it checks live there:
CHECK constraints, the composite same-case foreign key, JSONB snapshots and the append-only
triggers. It drops and recreates the test database's schema.

## Security notes

- Passwords are hashed with Argon2id; tokens are signed JWTs.
- `role` is never accepted from a client. Registration always creates a citizen.
- Cases are visible only to their creator, an assigned investigator, or an administrator.
  Another user's case returns `404` so existence is not disclosed.
- Free text containing an OTP, UPI PIN, CVV or password is rejected before persistence.
- Evidence files live outside any served directory and are streamed only through an
  authorised endpoint; no public storage URL exists.
- Audit, complaint-status and signature rows are append-only at the database level.
- Assessment results are write-once; only review columns may change.
- No secret is committed. `.env` files are gitignored.

## Known limitations

- **No external AI provider.** Incident analysis is a deterministic keyword pass. The
  response reports `provider_configured: false` rather than implying a model was used.
- **No official integrations.** FINTRACE never files a complaint, contacts a bank, or
  reports to a portal. Complaints record what the user did themselves.
- **Seeded rules are unverified placeholders.** They demonstrate the engine; they are not
  legal provisions.
- **Signing is opt-in.** Without `ED25519_PRIVATE_KEY_B64`, signing returns `503
  signing_unavailable`.
- **Open policy questions.** Data erasure versus append-only history, investigator sharing
  beyond a single assignment, and retention policy remain undecided (documented in
  `docs/database-design.md` §9).
- **No password reset or email verification.** Both need an email provider that is not
  configured.

## Architecture constraints

- No microservices in the initial system.
- Never store OTPs, UPI PINs, or banking passwords.
- AI may assist extraction and classification, but regulatory decisions use deterministic,
  versioned, source-backed rules.
- Evidence hashes verify byte integrity; a hash alone does not prove that evidence
  originated from the claimed source.
- No actual banking integrations are included.
