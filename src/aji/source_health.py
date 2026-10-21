"""Pure summary of public collector markers; no candidate information."""

from datetime import date, timedelta
from decimal import Decimal


def _count(value) -> int:
    if type(value) not in {int, Decimal} or \
            (isinstance(value, Decimal) and not value.is_finite()) or \
            value < 0 or value != int(value):
        raise ValueError("invalid collection count")
    return int(value)


def summarize_source_health(today: dict | None, previous: dict | None, day: str) -> dict:
    if not isinstance(today, dict) or today.get("collection_day") != day:
        raise ValueError("today's collection is missing or stale")
    if today.get("status") != "COMPLETE":
        raise ValueError("today's collection is incomplete")
    total = _count(today.get("job_count"))
    entries = today.get("source_health")
    if entries is None:
        return {"status": "NOT_INSTRUMENTED", "collection_day": day,
                "total_jobs": total, "sources": []}
    if not isinstance(entries, list) or not entries:
        raise ValueError("invalid source health")

    prior_day = (date.fromisoformat(day) - timedelta(days=1)).isoformat()
    prior = {}
    if isinstance(previous, dict) and previous.get("collection_day") == prior_day and \
            previous.get("status") == "COMPLETE" and isinstance(previous.get("source_health"), list):
        for entry in previous["source_health"]:
            if isinstance(entry, dict):
                try:
                    prior[(entry.get("source"), entry.get("board"))] = _count(entry.get("job_count"))
                except ValueError:
                    pass

    summary = []
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("invalid source health entry")
        source, board = entry.get("source"), entry.get("board")
        count, status = _count(entry.get("job_count")), entry.get("status")
        identity = (source, board)
        if not all(isinstance(value, str) and value for value in identity) or \
                identity in seen or status not in {"active", "empty"} or \
                (count == 0) != (status == "empty"):
            raise ValueError("invalid source health entry")
        seen.add(identity)
        previous_count = prior.get(identity)
        warning = None
        if count == 0 and previous_count is not None and previous_count > 0:
            warning = "zero_after_active"
        elif previous_count is not None and previous_count >= 10 and count <= previous_count / 4:
            warning = "sharp_drop"
        summary.append({"source": source, "board": board, "status": status,
                        "job_count": count, "previous_count": previous_count,
                        "warning": warning})
    return {"status": "COMPLETE", "collection_day": day,
            "total_jobs": total, "sources": summary}
