"""immutability guards and least-privilege grants

Revision ID: 0002_immutability_guards
Revises: a07a0a6e0386
Create Date: 2026-11-24

This revision enforces the integrity rules that cannot be expressed as
constraints: append-only history tables, write-once regulatory assessments,
immutable active rules, and reduced privileges for the runtime role.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0002_immutability_guards"
down_revision: Union[str, None] = "a07a0a6e0386"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


APPEND_ONLY_FUNCTION = """
CREATE OR REPLACE FUNCTION fintrace_reject_mutation() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Table % is append-only: % is not permitted', TG_TABLE_NAME, TG_OP
        USING ERRCODE = 'restrict_violation';
END;
$$;
"""

ASSESSMENT_GUARD_FUNCTION = """
CREATE OR REPLACE FUNCTION fintrace_guard_regulatory_assessment() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.case_id IS DISTINCT FROM OLD.case_id
       OR NEW.rule_id IS DISTINCT FROM OLD.rule_id
       OR NEW.rule_code IS DISTINCT FROM OLD.rule_code
       OR NEW.rule_version IS DISTINCT FROM OLD.rule_version
       OR NEW.rule_title IS DISTINCT FROM OLD.rule_title
       OR NEW.rule_authority IS DISTINCT FROM OLD.rule_authority
       OR NEW.rule_source_reference IS DISTINCT FROM OLD.rule_source_reference
       OR NEW.result_status IS DISTINCT FROM OLD.result_status
       OR NEW.explanation IS DISTINCT FROM OLD.explanation
       OR NEW.matched_conditions IS DISTINCT FROM OLD.matched_conditions
       OR NEW.unmatched_conditions IS DISTINCT FROM OLD.unmatched_conditions
       OR NEW.input_snapshot IS DISTINCT FROM OLD.input_snapshot
       OR NEW.input_snapshot_hash IS DISTINCT FROM OLD.input_snapshot_hash
       OR NEW.applicable_on_date IS DISTINCT FROM OLD.applicable_on_date
       OR NEW.engine_version IS DISTINCT FROM OLD.engine_version
       OR NEW.assessed_at IS DISTINCT FROM OLD.assessed_at
       OR NEW.assessed_by_user_id IS DISTINCT FROM OLD.assessed_by_user_id
       OR NEW.supersedes_assessment_id IS DISTINCT FROM OLD.supersedes_assessment_id
    THEN
        RAISE EXCEPTION
            'regulatory_assessments rows are write-once; only review columns may change'
            USING ERRCODE = 'restrict_violation';
    END IF;
    RETURN NEW;
END;
$$;
"""

RULE_GUARD_FUNCTION = """
CREATE OR REPLACE FUNCTION fintrace_guard_active_rule() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF OLD.status = 'active' THEN
        IF NEW.rule_code IS DISTINCT FROM OLD.rule_code
           OR NEW.version IS DISTINCT FROM OLD.version
           OR NEW.rule_payload IS DISTINCT FROM OLD.rule_payload
           OR NEW.effective_from IS DISTINCT FROM OLD.effective_from
           OR NEW.effective_to IS DISTINCT FROM OLD.effective_to
           OR NEW.source_reference IS DISTINCT FROM OLD.source_reference
           OR NEW.source_url IS DISTINCT FROM OLD.source_url
           OR NEW.engine_schema_version IS DISTINCT FROM OLD.engine_schema_version
           OR NEW.verification_status IS DISTINCT FROM OLD.verification_status
        THEN
            RAISE EXCEPTION
                'An active regulatory rule is immutable; publish a new version instead'
                USING ERRCODE = 'restrict_violation';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;
"""


def upgrade() -> None:
    op.execute(APPEND_ONLY_FUNCTION)
    op.execute(ASSESSMENT_GUARD_FUNCTION)
    op.execute(RULE_GUARD_FUNCTION)

    for table in ("audit_events", "complaint_status_events", "evidence_signatures"):
        op.execute(
            f"""
            DROP TRIGGER IF EXISTS trg_{table}_append_only ON {table};
            CREATE TRIGGER trg_{table}_append_only
                BEFORE UPDATE OR DELETE ON {table}
                FOR EACH ROW EXECUTE FUNCTION fintrace_reject_mutation();
            """
        )

    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_regulatory_assessments_write_once ON regulatory_assessments;
        CREATE TRIGGER trg_regulatory_assessments_write_once
            BEFORE UPDATE ON regulatory_assessments
            FOR EACH ROW EXECUTE FUNCTION fintrace_guard_regulatory_assessment();
        """
    )
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_regulatory_rules_immutable ON regulatory_rules;
        CREATE TRIGGER trg_regulatory_rules_immutable
            BEFORE UPDATE ON regulatory_rules
            FOR EACH ROW EXECUTE FUNCTION fintrace_guard_active_rule();
        """
    )

    # Least privilege for the runtime role. Created if absent so the migration
    # is safe on a fresh server; grants are harmless when the role is unused.
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'fintrace_app') THEN
                CREATE ROLE fintrace_app NOLOGIN;
            END IF;
        END
        $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'fintrace_app') THEN
                EXECUTE 'GRANT USAGE ON SCHEMA public TO fintrace_app';
                EXECUTE 'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO fintrace_app';
                EXECUTE 'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO fintrace_app';
                EXECUTE 'REVOKE UPDATE, DELETE, TRUNCATE ON audit_events FROM fintrace_app';
                EXECUTE 'REVOKE UPDATE, DELETE, TRUNCATE ON complaint_status_events FROM fintrace_app';
                EXECUTE 'REVOKE UPDATE, DELETE, TRUNCATE ON evidence_signatures FROM fintrace_app';
                EXECUTE 'REVOKE DELETE, TRUNCATE ON cases, evidence, complaints, recovery_actions, regulatory_rules, regulatory_assessments FROM fintrace_app';
                EXECUTE 'REVOKE UPDATE ON regulatory_rules FROM fintrace_app';
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    for table in ("audit_events", "complaint_status_events", "evidence_signatures"):
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_append_only ON {table};")
    op.execute(
        "DROP TRIGGER IF EXISTS trg_regulatory_assessments_write_once ON regulatory_assessments;"
    )
    op.execute("DROP TRIGGER IF EXISTS trg_regulatory_rules_immutable ON regulatory_rules;")
    op.execute("DROP FUNCTION IF EXISTS fintrace_guard_active_rule();")
    op.execute("DROP FUNCTION IF EXISTS fintrace_guard_regulatory_assessment();")
    op.execute("DROP FUNCTION IF EXISTS fintrace_reject_mutation();")
