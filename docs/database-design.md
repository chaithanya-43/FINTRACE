# Database design

PostgreSQL is the primary database. SQLAlchemy provides ORM mapping and Alembic provides migrations.

## Initial conventions

- SQLAlchemy models derive from `app.database.base.Base`.
- Model definitions belong in `app/models`.
- Pydantic data transfer objects belong in `app/schemas`.
- Database sessions are created by `app/database/connection.py`.
- Schema changes should use Alembic migrations rather than direct production schema edits.

## Future domain entities

Domain models can be organized when implementation begins for:

- incidents and cases
- extracted and classified information
- regulatory rule versions and assessment results
- evidence metadata and signatures
- recovery actions and progress records

Sensitive personal and financial fields require explicit data classification and retention rules. OTPs, UPI PINs, and banking passwords must never be stored.
