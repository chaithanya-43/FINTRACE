# Development guide

## Setup

Copy the environment templates:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

The example values are placeholders only. Use local secrets that are not committed.

## Database

```bash
docker compose up -d postgres
```

Run migrations from the repository root:

```bash
cd backend
alembic upgrade head
```

## Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --reload
```

Run backend tests:

```bash
pytest backend/tests
```

## Frontend

```bash
cd frontend
npm install
npm run dev
npm run test
npm run build
```

## Code organization

Keep HTTP concerns in endpoints, domain behavior in modules, persistence in SQLAlchemy models, and public data shapes in Pydantic schemas. Add focused tests for behavior before broad integrations.
