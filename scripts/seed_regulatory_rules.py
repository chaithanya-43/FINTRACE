"""Seed example regulatory rules.

These rules are deliberately marked ``unverified``. They exist so the
assessment engine can be exercised end to end, and every assessment they
produce carries ``rule_verification_status = 'unverified'`` so the interface
can warn that the source has not been reviewed.

Nothing here claims to restate an RBI circular, statute or any other legal
instrument. Before operational use, replace these rows (or add new versions)
with rules transcribed from a reviewed primary source, then set
``verification_status = 'verified'``, ``verified_by`` and ``verified_at``.

Usage (from the repository root):

    python scripts/seed_regulatory_rules.py
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from sqlalchemy import select  # noqa: E402

from app.database.connection import SessionLocal  # noqa: E402
from app.models import RegulatoryRule  # noqa: E402

UNVERIFIED_AUTHORITY = "Unverified example - not a legal provision"

RULES = [
    {
        "rule_code": "EXAMPLE-EARLY-REPORTING",
        "version": 1,
        "title": "Incident reported within the early reporting window (example)",
        "authority": UNVERIFIED_AUTHORITY,
        "source_reference": (
            "Placeholder configuration used to demonstrate the engine. It is not "
            "transcribed from any statute, circular or regulation."
        ),
        "source_url": "https://cybercrime.gov.in",
        "effective_from": date(2020, 1, 1),
        "rule_payload": {
            "logic": "all",
            "conditions": [
                {"fact": "hours_since_incident", "operator": "lte", "value": 72},
                {"fact": "transaction_count", "operator": "gte", "value": 1},
            ],
        },
        "notes": "Replace with a reviewed source before relying on this outcome.",
    },
    {
        "rule_code": "EXAMPLE-UNAUTHORISED-DEBIT",
        "version": 1,
        "title": "Transaction recorded as unauthorised (example)",
        "authority": UNVERIFIED_AUTHORITY,
        "source_reference": (
            "Placeholder configuration used to demonstrate the engine. It is not "
            "transcribed from any statute, circular or regulation."
        ),
        "source_url": "https://cybercrime.gov.in",
        "effective_from": date(2020, 1, 1),
        "rule_payload": {
            "logic": "all",
            "conditions": [
                {
                    "fact": "authorization_types",
                    "operator": "contains_any",
                    "value": ["unauthorized"],
                },
                {"fact": "loss_amount", "operator": "gte", "value": 1},
            ],
        },
        "notes": "Replace with a reviewed source before relying on this outcome.",
    },
    {
        "rule_code": "EXAMPLE-EVIDENCE-SUFFICIENCY",
        "version": 1,
        "title": "Supporting evidence recorded for the dispute (example)",
        "authority": UNVERIFIED_AUTHORITY,
        "source_reference": (
            "Placeholder configuration used to demonstrate the engine. It is not "
            "transcribed from any statute, circular or regulation."
        ),
        "source_url": "https://cybercrime.gov.in",
        "effective_from": date(2020, 1, 1),
        "rule_payload": {
            "logic": "all",
            "conditions": [
                {"fact": "evidence_count", "operator": "gte", "value": 1},
                {"fact": "transaction_count", "operator": "gte", "value": 1},
            ],
        },
        "notes": "Replace with a reviewed source before relying on this outcome.",
    },
]


def main() -> None:
    created = 0
    session = SessionLocal()
    try:
        for definition in RULES:
            existing = session.scalar(
                select(RegulatoryRule).where(
                    RegulatoryRule.rule_code == definition["rule_code"],
                    RegulatoryRule.version == definition["version"],
                )
            )
            if existing is not None:
                continue
            session.add(
                RegulatoryRule(
                    **definition,
                    jurisdiction="IN",
                    status="active",
                    verification_status="unverified",
                )
            )
            created += 1
        session.commit()
        print(f"Seeded {created} new rule(s); {len(RULES)} example rules defined.")
        print("All examples are marked unverified. Review and replace before operational use.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
