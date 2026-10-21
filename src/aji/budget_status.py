"""Read-only summary of observed, tagged AWS project spend."""

from decimal import Decimal, InvalidOperation


def _positive_amount(value) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValueError("invalid budget amount")
    try:
        amount = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("invalid budget amount") from exc
    if not amount.is_finite() or amount < 0:
        raise ValueError("invalid budget amount")
    return amount


def summarize_budget(budget: dict, notifications: list[dict]) -> dict:
    if not isinstance(budget, dict) or budget.get("BudgetName") != "aji-project-dev" or \
            not isinstance(notifications, list):
        raise ValueError("unexpected project budget")
    try:
        limit = budget["BudgetLimit"]
        actual = budget["CalculatedSpend"]["ActualSpend"]
        if limit["Unit"] != "USD" or actual["Unit"] != "USD":
            raise ValueError("project budget currency is not USD")
        limit_amount = _positive_amount(limit["Amount"])
        actual_amount = _positive_amount(actual["Amount"])
    except (KeyError, TypeError) as exc:
        raise ValueError("project budget data is incomplete") from exc
    if limit_amount <= 0:
        raise ValueError("project budget limit is invalid")

    alerts = set()
    for item in notifications:
        if not isinstance(item, dict):
            raise ValueError("invalid budget notification")
        if item.get("NotificationType") != "ACTUAL" or \
                item.get("ThresholdType") != "ABSOLUTE_VALUE":
            continue
        if item.get("ComparisonOperator") not in {"GREATER_THAN", "EQUAL_TO"}:
            continue
        threshold = _positive_amount(item.get("Threshold"))
        if threshold <= 0:
            raise ValueError("invalid budget alert threshold")
        alerts.add(threshold)
    if not alerts:
        raise ValueError("actual spend alerts are missing")
    crossed = [amount for amount in alerts if actual_amount >= amount]
    return {
        "status": "AT_OR_ABOVE_ALERT" if crossed else "BELOW_ALERT",
        "observed_usd": float(actual_amount),
        "limit_usd": float(limit_amount),
        "alert_thresholds_usd": [float(amount) for amount in sorted(alerts)],
        "highest_crossed_alert_usd": float(max(crossed)) if crossed else None,
        "coverage": "tagged_project_only",
        "costs_may_lag": True,
    }
