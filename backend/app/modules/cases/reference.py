"""Human-readable public case references.

The UUID primary key stays the real identifier; this reference exists so a
victim can quote something short over the phone.
"""

import secrets
from datetime import UTC, datetime

# Ambiguous characters are excluded so the reference can be read aloud.
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_public_reference(when: datetime | None = None) -> str:
    stamp = (when or datetime.now(UTC)).year
    suffix = "".join(secrets.choice(_ALPHABET) for _ in range(6))
    return f"FT-{stamp}-{suffix}"
