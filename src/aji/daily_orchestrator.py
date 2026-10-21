"""Coordinate Alec's local daily read and PREPARE steps without submitting."""

import json
import math
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo

from .normalizer import utc_timestamp


_MEXICO_CITY = ZoneInfo("America/Mexico_City")
_SAFE_CODE = re.compile(r"[A-Z][A-Z0-9_]{1,64}\Z")


@dataclass(frozen=True)
class StepResult:
    exit_code: int
    payload: dict | None


def _call(runner: Callable[[str], StepResult], step: str) -> StepResult:
    try:
        result = runner(step)
    except TimeoutError:
        return StepResult(2, {"error_code": "STEP_TIMEOUT"})
    except Exception:
        return StepResult(2, {"error_code": "STEP_FAILED"})
    return result if isinstance(result, StepResult) else StepResult(2, {"error_code": "STEP_FAILED"})


def _code(result: StepResult, fallback: str) -> str:
    raw = result.payload.get("error_code") if isinstance(result.payload, dict) else None
    return raw if isinstance(raw, str) and _SAFE_CODE.fullmatch(raw) else fallback


def _count(value: object, *, maximum: int) -> bool:
    return type(value) is int and 0 <= value <= maximum


def _money(value: object) -> bool:
    return type(value) in {int, float} and math.isfinite(value) and value >= 0


def _confirmed(payload: dict) -> int | None:
    tracker = payload.get("tracker")
    if not isinstance(tracker, dict) or not isinstance(tracker.get("by_status"), dict):
        return None
    counts = tracker["by_status"]
    confirmed = ("CONFIRMED", "INTERVIEW", "OFFER", "HIRED")
    if any(not _count(counts.get(key, 0), maximum=10_000) for key in confirmed):
        return None
    return sum(counts.get(key, 0) for key in confirmed)


def run_daily(now: str, runner: Callable[[str], StepResult]) -> dict:
    normalized = utc_timestamp(now)
    if normalized is None:
        raise ValueError("current time required")
    day = datetime.fromisoformat(normalized.replace("Z", "+00:00")).astimezone(
        _MEXICO_CITY).date().isoformat()
    batch_id = f"alec:{day}"
    report = {
        "status": "ERROR", "candidate_id": "alec", "local_day": day,
        "generated_at": normalized, "batch_id": None,
        "source_health": None, "budget": None, "aws": None,
        "getonbrd": None, "preparation": None,
        "confirmed_applications": None, "errors": [], "warnings": [],
    }
    core_error = False
    budget_alert = False

    preflight = _call(runner, "preflight")
    identity_ok = preflight.exit_code == 0
    if not identity_ok:
        report["errors"].append({"step": "preflight", "code": "AWS_IDENTITY_UNVERIFIED"})
        core_error = True
    else:
        budget = _call(runner, "budget")
        value = budget.payload
        if budget.exit_code == 0 and isinstance(value, dict) and \
                value.get("status") in {"BELOW_ALERT", "AT_OR_ABOVE_ALERT"} and \
                _money(value.get("observed_usd")) and _money(value.get("limit_usd")) and \
                isinstance(value.get("alert_thresholds_usd"), list):
            report["budget"] = value
            budget_alert = value["status"] == "AT_OR_ABOVE_ALERT"
        if report["budget"] is None:
            report["errors"].append({"step": "budget", "code": _code(budget, "BUDGET_READ_FAILED")})

        health = _call(runner, "source_health")
        value = health.payload
        health_ok = health.exit_code == 0 and isinstance(value, dict) and \
            value.get("status") in {"COMPLETE", "NOT_INSTRUMENTED"} and \
            value.get("collection_day") == day
        if health_ok:
            report["source_health"] = value
            if value["status"] == "NOT_INSTRUMENTED":
                report["warnings"].append({"step": "source_health",
                                           "code": "SOURCE_HEALTH_NOT_INSTRUMENTED"})
            else:
                for source in value.get("sources", []):
                    if not isinstance(source, dict):
                        continue
                    warning = source.get("warning")
                    code = {"zero_after_active": "SOURCE_ZERO_AFTER_ACTIVE",
                            "sharp_drop": "SOURCE_SHARP_DROP"}.get(warning) \
                        if isinstance(warning, str) else None
                    if code is None and source.get("status") == "empty":
                        code = "SOURCE_EMPTY"
                    if code:
                        report["warnings"].append({
                            "step": "source_health", "code": code,
                            "source": source.get("source"), "board": source.get("board"),
                        })
        else:
            report["errors"].append({"step": "source_health",
                                     "code": _code(health, "COLLECTION_INCOMPLETE")})
            core_error = True

        preview = _call(runner, "batch_preview")
        value = preview.payload
        batch_ok = preview.exit_code == 0 and isinstance(value, dict) and \
            value.get("status") == "READY" and value.get("candidate_id") == "alec" and \
            value.get("batch_id") == batch_id and _count(value.get("jobs_found"), maximum=10) and \
            _count(value.get("shortlisted"), maximum=10) and \
            _count(value.get("needs_review"), maximum=10) and \
            value["shortlisted"] + value["needs_review"] <= value["jobs_found"] and \
            isinstance(value.get("opportunities"), list)
        if batch_ok:
            report["batch_id"] = batch_id
            report["aws"] = value
            report["confirmed_applications"] = _confirmed(value)
        else:
            report["errors"].append({"step": "batch_preview",
                                     "code": _code(preview, "BATCH_INVALID_OR_STALE")})
            core_error = True

    local_preview = _call(runner, "getonbrd_preview")
    value = local_preview.payload
    local_ok = local_preview.exit_code == 0 and isinstance(value, dict) and \
        value.get("status") in {"READY", "EMPTY"} and value.get("candidate_id") == "alec" and \
        _count(value.get("jobs_fetched"), maximum=300) and \
        isinstance(value.get("opportunities"), list)
    if local_ok:
        report["getonbrd"] = value
    else:
        report["errors"].append({"step": "getonbrd_preview",
                                 "code": _code(local_preview, "GETONBRD_UNAVAILABLE")})

    if identity_ok and report["source_health"] is not None and report["aws"] is not None:
        preparation = _call(runner, "prepare")
        value = preparation.payload
        prep_ok = preparation.exit_code == 0 and isinstance(value, dict) and \
            value.get("status") == "READY" and value.get("candidate_id") == "alec" and \
            value.get("batch_id") == batch_id and \
            value.get("jobs_found") == report["aws"]["jobs_found"] and \
            _count(value.get("prepared"), maximum=3) and \
            _count(value.get("existing"), maximum=3) and \
            value["prepared"] + value["existing"] <= 3 and \
            isinstance(value.get("completed_items"), list) and \
            len(value["completed_items"]) == value["prepared"] + value["existing"]
        if prep_ok:
            report["preparation"] = value
            report["confirmed_applications"] = _confirmed(value)
        else:
            report["errors"].append({"step": "prepare",
                                     "code": _code(preparation, "PREPARATION_INVALID")})
            report["confirmed_applications"] = None
            core_error = True

    if core_error:
        report["status"] = "ERROR"
    elif budget_alert:
        report["status"] = "ATTENTION"
    elif report["errors"] or report["warnings"]:
        report["status"] = "PARTIAL"
    else:
        report["status"] = "READY"
    return report


def save_daily_report(path: Path, report: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=target.parent,
                                         prefix=".daily-report-", suffix=".tmp",
                                         delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temporary, target)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def compact_report(report: dict) -> dict:
    """Print only run counters; full opportunity details stay in the ignored file."""
    aws = report.get("aws") or {}
    local = report.get("getonbrd") or {}
    preparation = report.get("preparation") or {}
    health = report.get("source_health") or {}
    budget = report.get("budget") or {}
    return {
        "status": report["status"], "local_day": report["local_day"],
        "batch_id": report.get("batch_id"),
        "report_file": "applications/alec/daily-report.json",
        "source_health": {"status": health.get("status"),
                          "sources_checked": len(health.get("sources", []))},
        "budget": {"status": budget.get("status"),
                   "observed_usd": budget.get("observed_usd"),
                   "highest_crossed_alert_usd": budget.get("highest_crossed_alert_usd"),
                   "costs_may_lag": budget.get("costs_may_lag")},
        "aws": {key: aws.get(key) for key in
                ("jobs_found", "shortlisted", "needs_review", "new_opportunities",
                 "repeated_opportunities")},
        "getonbrd": {key: local.get(key) for key in
                      ("status", "jobs_fetched", "shortlisted", "needs_review",
                       "possibly_truncated_categories")},
        "preparation": {key: preparation.get(key) for key in
                        ("prepared", "existing", "blocked", "daily_limit_reached")},
        "confirmed_applications": report.get("confirmed_applications"),
        "errors": report["errors"], "warnings": report["warnings"],
    }
