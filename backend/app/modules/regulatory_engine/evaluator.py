"""Deterministic regulatory rule evaluation.

No model, score or probabilistic guess is involved. Every outcome is a function
of the recorded facts, the rule payload and the evaluation date, so the same
inputs always produce the same result.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal

from app.models import Case, Transaction
from app.utils.enums import ResultStatus

SUPPORTED_OPERATORS = {"eq", "neq", "in", "not_in", "gte", "lte", "gt", "lt", "contains_any", "exists"}


@dataclass
class ConditionOutcome:
    fact: str
    operator: str
    expected: object
    actual: object
    status: str
    text: str

    def as_dict(self) -> dict:
        return {
            "fact": self.fact,
            "operator": self.operator,
            "expected": self.expected,
            "actual": self.actual,
            "status": self.status,
            "text": self.text,
        }


@dataclass
class Evaluation:
    result_status: str
    explanation: str
    matched: list[dict] = field(default_factory=list)
    unmatched: list[dict] = field(default_factory=list)
    missing: list[dict] = field(default_factory=list)


class RulePayloadError(ValueError):
    pass


def build_facts(
    case: Case,
    transactions: list[Transaction],
    evidence_count: int,
    now: datetime | None = None,
) -> dict[str, dict]:
    """Facts known to the engine, each tagged with how it was obtained."""
    moment = now or datetime.now(UTC)
    facts: dict[str, dict] = {}

    def put(name: str, value, source: str) -> None:
        facts[name] = {"value": value, "source": source}

    put("incident_type", case.incident_type, "user_provided")
    put("fraud_channel", case.fraud_channel, "user_provided")
    put("currency", case.currency, "user_provided")
    put(
        "loss_amount",
        float(case.estimated_loss_amount)
        if isinstance(case.estimated_loss_amount, Decimal)
        else case.estimated_loss_amount,
        "user_provided" if case.estimated_loss_amount is not None else "missing",
    )
    put("is_disputed", case.is_disputed, "user_provided")
    put("transaction_count", len(transactions), "derived")
    put(
        "transaction_amount_total",
        float(sum((t.amount for t in transactions), Decimal("0"))),
        "derived",
    )
    put(
        "authorization_types",
        sorted({t.authorization_type for t in transactions}),
        "derived",
    )
    put(
        "transaction_channels",
        sorted({t.channel for t in transactions if t.channel}),
        "derived",
    )
    put("evidence_count", evidence_count, "derived")

    if case.incident_occurred_at is not None:
        occurred = case.incident_occurred_at
        if occurred.tzinfo is None:
            occurred = occurred.replace(tzinfo=UTC)
        hours = (moment - occurred).total_seconds() / 3600
        put("hours_since_incident", round(hours, 2), "derived")
        put("days_since_incident", round(hours / 24, 2), "derived")
    else:
        put("hours_since_incident", None, "missing")
        put("days_since_incident", None, "missing")

    return facts


def _describe(fact: str, operator: str, expected) -> str:  # noqa: ANN001
    if operator == "eq":
        return f"{fact} equals {expected!r}"
    if operator == "neq":
        return f"{fact} is not {expected!r}"
    if operator == "in":
        return f"{fact} is one of {expected!r}"
    if operator == "not_in":
        return f"{fact} is not one of {expected!r}"
    if operator in {"gte", "lte", "gt", "lt"}:
        symbol = {"gte": ">=", "lte": "<=", "gt": ">", "lt": "<"}[operator]
        return f"{fact} {symbol} {expected!r}"
    if operator == "contains_any":
        return f"{fact} contains any of {expected!r}"
    if operator == "exists":
        return f"{fact} is recorded"
    return f"{fact} {operator} {expected!r}"


def _compare(actual, operator: str, expected) -> bool:  # noqa: ANN001
    if operator == "eq":
        return actual == expected
    if operator == "neq":
        return actual != expected
    if operator == "in":
        return actual in expected
    if operator == "not_in":
        return actual not in expected
    if operator == "gte":
        return actual is not None and actual >= expected
    if operator == "lte":
        return actual is not None and actual <= expected
    if operator == "gt":
        return actual is not None and actual > expected
    if operator == "lt":
        return actual is not None and actual < expected
    if operator == "contains_any":
        if not isinstance(actual, (list, tuple, set, str)):
            return False
        return any(item in actual for item in expected)
    if operator == "exists":
        return actual is not None
    raise RulePayloadError(f"Unsupported operator '{operator}'.")


def evaluate(rule_payload: dict, facts: dict[str, dict], *, on_date) -> Evaluation:  # noqa: ANN001
    conditions = rule_payload.get("conditions") or []
    logic = rule_payload.get("logic", "all")
    if not isinstance(conditions, list) or not conditions:
        return Evaluation(
            result_status=ResultStatus.INCONCLUSIVE.value,
            explanation="The stored rule has no machine-evaluable conditions, so no result can be asserted.",
        )
    if logic not in {"all", "any"}:
        raise RulePayloadError(f"Unsupported rule logic '{logic}'.")

    outcomes: list[ConditionOutcome] = []
    for condition in conditions:
        try:
            fact = condition["fact"]
            operator = condition["operator"]
        except (KeyError, TypeError) as exc:
            raise RulePayloadError("Each condition needs 'fact' and 'operator'.") from exc
        if operator not in SUPPORTED_OPERATORS:
            raise RulePayloadError(f"Unsupported operator '{operator}'.")

        expected = condition.get("value")
        entry = facts.get(fact)
        actual = entry["value"] if entry else None
        if actual is None or (isinstance(actual, list) and not actual):
            outcomes.append(
                ConditionOutcome(
                    fact=fact,
                    operator=operator,
                    expected=expected,
                    actual=actual,
                    status="missing",
                    text=f"Cannot confirm: {_describe(fact, operator, expected)} (fact not recorded).",
                )
            )
            continue
        matched = _compare(actual, operator, expected)
        outcomes.append(
            ConditionOutcome(
                fact=fact,
                operator=operator,
                expected=expected,
                actual=actual,
                status="matched" if matched else "unmatched",
                text=("Confirmed: " if matched else "Not met: ")
                + _describe(fact, operator, expected),
            )
        )

    matched = [o.as_dict() for o in outcomes if o.status == "matched"]
    unmatched = [o.as_dict() for o in outcomes if o.status == "unmatched"]
    missing = [o.as_dict() for o in outcomes if o.status == "missing"]

    if logic == "all":
        if not unmatched and not missing:
            status = ResultStatus.APPLIES
        elif matched and (unmatched or missing):
            status = ResultStatus.MAY_APPLY
        elif not matched and missing and not unmatched:
            status = ResultStatus.INCONCLUSIVE
        elif not matched and unmatched:
            status = ResultStatus.DOES_NOT_APPLY
        else:
            status = ResultStatus.INCONCLUSIVE
    else:  # any
        if matched:
            status = ResultStatus.APPLIES
        elif missing:
            status = ResultStatus.INCONCLUSIVE
        else:
            status = ResultStatus.DOES_NOT_APPLY

    status = _downgrade_if_disputed(status, facts)
    return Evaluation(
        result_status=status.value,
        explanation=_explain(status, matched, unmatched, missing, on_date),
        matched=matched,
        unmatched=unmatched,
        missing=missing,
    )


def _downgrade_if_disputed(status: ResultStatus, facts: dict[str, dict]) -> ResultStatus:
    """A dispute about the underlying facts prevents an asserted outcome."""
    if not facts.get("is_disputed", {}).get("value"):
        return status
    if status in (ResultStatus.APPLIES, ResultStatus.DOES_NOT_APPLY):
        return ResultStatus.DISPUTED
    return status


def _explain(status, matched, unmatched, missing, on_date) -> str:  # noqa: ANN001
    parts = [
        f"Evaluated on {on_date.isoformat()} against the facts recorded for this case."
    ]
    if matched:
        parts.append("Conditions met: " + "; ".join(item["text"] for item in matched) + ".")
    if unmatched:
        parts.append(
            "Conditions not met: " + "; ".join(item["text"] for item in unmatched) + "."
        )
    if missing:
        parts.append(
            "Unconfirmed information: "
            + "; ".join(item["text"] for item in missing)
            + "."
        )
    label = {
        "applies": "The rule's conditions are met on the recorded facts.",
        "may_apply": "The rule could apply, but some conditions are unmet or unconfirmed.",
        "does_not_apply": "The rule's conditions are not met on the recorded facts.",
        "inconclusive": "There is not enough recorded information to decide.",
        "disputed": "The recorded facts are disputed, so no outcome is asserted.",
    }[status.value]
    parts.append(label)
    parts.append(
        "This is a deterministic evaluation of recorded facts against a stored rule; "
        "it is not a legal or regulatory determination."
    )
    return " ".join(parts)
