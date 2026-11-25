# Development guide

## Prerequisites

- Python 3.11+ (the project is verified on 3.14)
- Node.js 20+
- PostgreSQL 16, either through Docker Compose or a local server

## Setup

Copy the environment templates:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

The example values are placeholders only. Use local secrets that are not committed.

Required backend values:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | `postgresql+psycopg://user:password@host:5432/fintrace` |
| `TEST_DATABASE_URL` | A separate disposable database used by pytest |
| `JWT_SECRET` | Token signing secret; generate one per environment |
| `CORS_ORIGINS` | Comma-separated browser origins |
| `STORAGE_ROOT` | Private directory for evidence files (default `storage`) |
| `MAX_UPLOAD_BYTES` | Upload ceiling (default 10 MiB) |
| `ED25519_KEY_ID`, `ED25519_PRIVATE_KEY_B64` | Optional evidence signing; unset means reporting is "unavailable" |

Generate a secret with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Database

```bash
docker compose up -d postgres
```

Apply migrations from `backend/`:

```bash
cd backend
alembic upgrade head
```

The first revision creates all twelve tables, indexes and constraints; the second adds the
append-only triggers, the write-once assessment guard, the immutable-active-rule guard and
least-privilege grants for `fintrace_app`.

Seed the example regulatory rules (all marked `unverified`):

```bash
python scripts/seed_regulatory_rules.py
```

These rules exist to exercise the engine. Replace them with rules transcribed from a
reviewed primary source and set `verification_status = 'verified'` before relying on any
outcome.

## Backend

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --reload
```

The API is at `http://localhost:8000`, with Swagger at `/docs`.

## Backend tests

Tests run against a real PostgreSQL database, because the behaviour under test lives in the
database: CHECK constraints, the composite same-case foreign key, JSONB snapshots and the
append-only triggers. SQLite cannot exercise them.

```bash
export TEST_DATABASE_URL="postgresql+psycopg://fintrace:fintrace@localhost:5432/fintrace_test"
cd backend
pytest
```

The suite drops and recreates the `public` schema of that database, so never point
`TEST_DATABASE_URL` at a database you want to keep.

## Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
npm test           # Vitest
npm run build
```

`VITE_API_BASE_URL` selects the API root (default `http://localhost:8000/api/v1`).

## End-to-end check

With the API running:

```bash
python scripts/smoke_test.py            # defaults to http://127.0.0.1:8000/api/v1
```

It registers a throwaway user and walks the whole prototype: case, transaction, evidence
upload and verification, analysis, assessment, roadmap, complaint history, audit trail, and
the cross-account access check.

## Code organization

Keep HTTP concerns in endpoints, domain behavior in modules, persistence in SQLAlchemy
models, and public data shapes in Pydantic schemas. Add focused tests for behavior before
broad integrations.

Evidence files are written under `STORAGE_ROOT` in a content-derived path and are never
served by a static handler; `GET /cases/{id}/evidence/{id}/download` is the only read path.
