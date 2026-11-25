"""Minimal structured logging with sensitive-value redaction.

Only identifiers and event names are logged. Amounts, names, contact details,
tokens and evidence contents are never logged.
"""

import logging
import sys

REDACTED = "[redacted]"
_configured = False


def configure_logging(debug: bool = False) -> None:
    global _configured
    if _configured:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.DEBUG if debug else logging.INFO)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
