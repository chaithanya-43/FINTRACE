"""Deterministic incident classification.

This is a keyword/pattern classifier, not a language model. It never produces a
regulatory or legal outcome, and its output is always labelled as a suggestion
that the user or an investigator must confirm.
"""

from app.utils.enums import FRAUD_CATEGORIES, FRAUD_CHANNELS

_CATEGORY_SIGNALS: dict[str, tuple[str, ...]] = {
    "upi_fraud": ("upi", "gpay", "phonepe", "paytm", "vpa", "collect request", "upi id"),
    "card_fraud": ("card", "cvv", "credit card", "debit card", "card not present", "skim"),
    "net_banking_fraud": ("net banking", "netbanking", "internet banking", "bank login"),
    "investment_fraud": (
        "investment",
        "trading",
        "stock tips",
        "crypto",
        "returns",
        "profit guarantee",
        "telegram group",
    ),
    "loan_app_fraud": ("loan app", "instant loan", "loan application", "emi", "recovery agent"),
    "job_offer_fraud": ("job offer", "work from home", "task", "part time job", "joining fee"),
    "otp_phishing": ("otp", "one time password", "verification code", "phishing link"),
    "sextortion": ("video call", "nude", "intimate", "blackmail", "sextortion"),
    "sim_swap": ("sim swap", "sim card", "port", "network lost", "no signal"),
    "impersonation": (
        "impersonat",
        "pretending to be",
        "fake officer",
        "police officer",
        "bank official",
        "customs",
    ),
    "merchant_fraud": ("merchant", "qr code", "payment link", "shop", "refund"),
}

_CHANNEL_SIGNALS: dict[str, tuple[str, ...]] = {
    "whatsapp": ("whatsapp", "wa.me"),
    "phone_call": ("phone call", "called me", "caller", "ivr", "telecaller"),
    "sms": ("sms", "text message", "message received"),
    "email": ("email", "mail", "inbox"),
    "social_media": ("instagram", "facebook", "telegram", "twitter", "linkedin", "snapchat"),
    "mobile_app": ("app", "application", "apk", "play store"),
    "net_banking": ("net banking", "netbanking", "internet banking"),
    "upi": ("upi", "gpay", "phonepe", "paytm"),
    "card": ("card", "atm", "pos machine", "swipe"),
    "in_person": ("in person", "at the branch", "handed over cash"),
}


def _score(text: str, signals: dict[str, tuple[str, ...]]) -> dict[str, int]:
    lowered = text.lower()
    return {
        category: sum(1 for keyword in keywords if keyword in lowered)
        for category, keywords in signals.items()
    }


def classify(
    description: str,
    *,
    incident_type: str = "unknown",
    fraud_channel: str = "unknown",
) -> dict:
    """Suggest a category and channel without overriding recorded values.

    A value the user already recorded wins over an inferred one: the classifier
    only fills gaps, it does not relabel confirmed case data.
    """
    text = description or ""
    category_scores = _score(text, _CATEGORY_SIGNALS)
    channel_scores = _score(text, _CHANNEL_SIGNALS)

    best_category, best_score = max(category_scores.items(), key=lambda item: item[1])
    best_channel, best_channel_score = max(channel_scores.items(), key=lambda item: item[1])

    if incident_type not in FRAUD_CATEGORIES:
        incident_type = "unknown"
    if fraud_channel not in FRAUD_CHANNELS:
        fraud_channel = "unknown"

    suggested_category = incident_type if incident_type != "unknown" else best_category
    if not best_score and incident_type == "unknown":
        suggested_category = "unknown"
    if suggested_category not in FRAUD_CATEGORIES:
        suggested_category = "unknown"

    suggested_channel = fraud_channel if fraud_channel != "unknown" else best_channel
    if not best_channel_score and fraud_channel == "unknown":
        suggested_channel = "unknown"
    if suggested_channel not in FRAUD_CHANNELS:
        suggested_channel = "unknown"

    total_signal = sum(category_scores.values())
    return {
        "suggested_incident_type": suggested_category,
        "suggested_fraud_channel": suggested_channel,
        "matched_keywords": [
            keyword
            for keyword in _CATEGORY_SIGNALS.get(suggested_category, ())
            if keyword in text.lower()
        ],
        "signal_count": total_signal,
        "confidence_note": (
            "Keyword-based suggestion from the written description. "
            "It is not a legal classification and must be confirmed by the user "
            "or an investigator."
        ),
    }
