"""Guard against storing banking authentication secrets.

FINTRACE never needs an OTP, UPI PIN, card CVV, password or banking password.
Users sometimes paste them into a narrative anyway, so free-text fields are
checked before persistence instead of relying on documentation alone.
"""

import re

from app.core.exceptions import InvalidRequest

_SECRET_PATTERNS = (
    re.compile(r"\b(?:otp|one[\s-]?time\s+password)\b[^.\n]{0,20}?\b\d{4,8}\b", re.I),
    re.compile(r"\b\d{4,8}\b[^.\n]{0,20}?\b(?:otp|one[\s-]?time\s+password)\b", re.I),
    re.compile(r"\b(?:upi\s*pin|atm\s*pin|card\s*pin|pin)\b\s*(?:is|[:=])?\s*\d{4,6}\b", re.I),
    re.compile(r"\b\d{4,6}\b[^.\n]{0,16}?\b(?:upi\s*pin|atm\s*pin|card\s*pin)\b", re.I),
    re.compile(r"\bcvv\b\s*(?:is|[:=])?\s*\d{3,4}\b", re.I),
    re.compile(r"\b\d{3,4}\b[^.\n]{0,12}?\bcvv\b", re.I),
    re.compile(r"\b(?:password|passcode)\b\s*(?:is|[:=])\s*\S+", re.I),
    re.compile(r"\b(?:net\s*banking|internet\s*banking)\s+(?:password|pin)\b\s*(?:is|[:=])?\s*\S+", re.I),
)

_MESSAGE = (
    "This text appears to contain an OTP, PIN, CVV or password. FINTRACE never "
    "stores these. Remove the secret and describe the event instead "
    "(for example: \"received an OTP call I did not initiate\")."
)


def assert_no_authentication_secrets(*values: str | None) -> None:
    for value in values:
        if not value:
            continue
        for pattern in _SECRET_PATTERNS:
            if pattern.search(value):
                raise InvalidRequest(_MESSAGE, code="sensitive_data_rejected")
