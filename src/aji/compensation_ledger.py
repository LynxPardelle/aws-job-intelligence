"""Private, source-backed compensation observations; no tax inference."""

import hashlib
import json
import re
import sqlite3
from contextlib import closing
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .normalizer import public_https_url, utc_timestamp


_SOURCES = {
    "desired": {"holder"},
    "advertised": {"employer_posting"},
    "estimated_net": {"tax_scenario"},
    "offered": {"written_offer", "recruiter_message"},
    "actual": {"payment_record"},
}
_FIELDS = {"candidate_id", "job_id", "kind", "minimum", "maximum", "currency",
           "interval", "basis", "source_type", "source_ref", "observed_at"}


def _amount(value) -> str:
    if type(value) not in {str, int, float, Decimal}:
        raise ValueError("invalid compensation amount")
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("invalid compensation amount") from exc
    if not number.is_finite() or number < 0:
        raise ValueError("invalid compensation amount")
    return format(number, "f")


def _validate(raw: dict) -> dict:
    if not isinstance(raw, dict) or set(raw) != _FIELDS:
        raise ValueError("invalid compensation observation")
    candidate_id, job_id = raw["candidate_id"], raw["job_id"]
    if not isinstance(candidate_id, str) or not re.fullmatch(r"[a-z0-9_-]+", candidate_id) or \
            not isinstance(job_id, str) or not job_id or len(job_id) > 256:
        raise ValueError("invalid compensation identity")
    kind, source_type = raw["kind"], raw["source_type"]
    if kind not in _SOURCES or source_type not in _SOURCES[kind]:
        raise ValueError("compensation source cannot support this kind")
    minimum, maximum = _amount(raw["minimum"]), _amount(raw["maximum"])
    if Decimal(minimum) > Decimal(maximum):
        raise ValueError("invalid compensation range")
    if not isinstance(raw["currency"], str) or not re.fullmatch(r"[A-Z]{3}", raw["currency"]):
        raise ValueError("currency required")
    if raw["interval"] not in {"hour", "day", "week", "month", "year"} or \
            raw["basis"] not in {"gross", "net", "contract", "unknown"} or \
            (kind in {"estimated_net", "actual"} and raw["basis"] != "net"):
        raise ValueError("invalid compensation period or basis")
    source_ref = raw["source_ref"]
    if not isinstance(source_ref, str) or not source_ref or len(source_ref) > 1000:
        raise ValueError("compensation source required")
    if source_type == "employer_posting":
        public_https_url(source_ref)
    observed_at = utc_timestamp(raw["observed_at"])
    if observed_at is None:
        raise ValueError("observation time required")
    return {**raw, "minimum": minimum, "maximum": maximum,
            "observed_at": observed_at}


def record_compensation(path: Path, observation: dict) -> bool:
    entry = _validate(observation)
    event_id = hashlib.sha256(json.dumps(entry, sort_keys=True, separators=(",", ":"))
                              .encode("utf-8")).hexdigest()
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with closing(sqlite3.connect(db_path, timeout=5)) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS compensation (
                event_id TEXT PRIMARY KEY, candidate_id TEXT NOT NULL, job_id TEXT NOT NULL,
                kind TEXT NOT NULL, minimum TEXT NOT NULL, maximum TEXT NOT NULL,
                currency TEXT NOT NULL, interval TEXT NOT NULL, basis TEXT NOT NULL,
                source_type TEXT NOT NULL, source_ref TEXT NOT NULL, observed_at TEXT NOT NULL
            )""")
            with conn:
                cursor = conn.execute(
                    "INSERT OR IGNORE INTO compensation VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (event_id, *(entry[key] for key in (
                        "candidate_id", "job_id", "kind", "minimum", "maximum", "currency",
                        "interval", "basis", "source_type", "source_ref", "observed_at"))),
                )
            return cursor.rowcount == 1
    except sqlite3.Error as exc:
        raise OSError("private compensation ledger unavailable") from exc


def list_compensation(path: Path, candidate_id: str, job_id: str) -> list[dict]:
    if not re.fullmatch(r"[a-z0-9_-]+", candidate_id) or not job_id:
        raise ValueError("invalid compensation identity")
    if not Path(path).exists():
        return []
    try:
        with closing(sqlite3.connect(path, timeout=5)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT kind, minimum, maximum, currency, interval, basis, source_type, "
                "source_ref, observed_at FROM compensation WHERE candidate_id=? AND job_id=? "
                "ORDER BY observed_at, event_id", (candidate_id, job_id),
            ).fetchall()
            return [dict(row) for row in rows]
    except sqlite3.Error as exc:
        raise OSError("private compensation ledger unavailable") from exc


def record_advertised_salaries(path: Path, summary: dict) -> int:
    if summary.get("status") not in {"READY", "ALREADY_PROCESSED"}:
        return 0
    candidate_id = summary.get("candidate_id")
    observed_at = summary.get("generated_at")
    opportunities = summary.get("opportunities")
    if not isinstance(opportunities, list) or not observed_at:
        raise ValueError("ready summary lacks salary observation context")
    recorded = 0
    for item in opportunities:
        salary = item.get("salary")
        if not isinstance(salary, dict) or any(salary.get(key) is None for key in
                                               ("minimum", "maximum", "currency", "interval")):
            continue
        observation = {
            "candidate_id": candidate_id, "job_id": item.get("job_id"),
            "kind": "advertised", "minimum": salary["minimum"],
            "maximum": salary["maximum"], "currency": salary["currency"],
            "interval": salary["interval"], "basis": salary.get("basis", "unknown"),
            "source_type": "employer_posting", "source_ref": item.get("source_url"),
            "observed_at": observed_at,
        }
        recorded += int(record_compensation(path, observation))
    return recorded
