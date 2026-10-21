"""Local, retryable preparation from a validated private batch.

The caller supplies a CandidateBatchStore; its load() validates the manifest and
checksums. This module never claims the permanent batch lock or sends forms.
The SQLite ledger persists daily reservations across runs and process restarts.
"""

import re
import sqlite3
from contextlib import closing, contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from .application_package import prepare_application
from .matcher import MatchResult
from .models import job_from_dict
from .normalizer import utc_timestamp


_MEXICO_CITY = ZoneInfo("America/Mexico_City")
_RESERVATION_TIMEOUT = timedelta(minutes=15)


@contextmanager
def _ledger(path: Path):
    try:
        with closing(sqlite3.connect(path, timeout=5)) as conn:
            yield conn
    except sqlite3.Error as exc:
        raise OSError("local preparation ledger unavailable") from exc


def _reserve(conn: sqlite3.Connection, day: str, job_id: str, limit: int,
             now_iso: str) -> str:
    """Atomically reserve a slot or report a completed/in-progress package."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        row = conn.execute(
            "SELECT status, reserved_at FROM preparations WHERE day=? AND job_id=?",
            (day, job_id),
        ).fetchone()
        if row and row[0] == "complete":
            outcome = "existing"
        elif row and datetime.fromisoformat(now_iso.replace("Z", "+00:00")) - \
                datetime.fromisoformat(row[1].replace("Z", "+00:00")) < _RESERVATION_TIMEOUT:
            outcome = "in_progress"
        elif row:
            conn.execute("UPDATE preparations SET reserved_at=? WHERE day=? AND job_id=?",
                         (now_iso, day, job_id))
            outcome = "retry"
        elif conn.execute("SELECT COUNT(*) FROM preparations WHERE day=?", (day,)).fetchone()[0] >= limit:
            outcome = "limit"
        else:
            conn.execute(
                "INSERT INTO preparations(day, job_id, status, reserved_at) VALUES (?, ?, 'reserved', ?)",
                (day, job_id, now_iso),
            )
            outcome = "new"
        conn.commit()
        return outcome
    except Exception:
        conn.rollback()
        raise


def _finish(conn: sqlite3.Connection, day: str, job_id: str, *, complete: bool) -> None:
    with conn:
        if complete:
            conn.execute("UPDATE preparations SET status='complete' WHERE day=? AND job_id=?",
                         (day, job_id))
        else:
            conn.execute("DELETE FROM preparations WHERE day=? AND job_id=?",
                         (day, job_id))


def prepare_daily_batch(store, now: str, profile: dict, output_root: Path, *,
                        max_preparations: int, prepare_threshold: int) -> dict:
    if type(max_preparations) is not int or not 1 <= max_preparations <= 10:
        raise ValueError("invalid daily preparation limit")
    if type(prepare_threshold) is not int or not 0 <= prepare_threshold <= 100:
        raise ValueError("invalid preparation threshold")
    if not isinstance(profile, dict) or profile.get("candidate_id") != store.candidate_id or \
            profile.get("approved_by_holder") is not True or not profile.get("validated_at") or \
            not isinstance(profile.get("claims"), list) or not profile["claims"]:
        raise ValueError("candidate profile is not verified and approved")
    if not re.fullmatch(r"[a-z0-9_-]+", store.candidate_id):
        raise ValueError("invalid candidate ID")

    manifest, raw_jobs, raw_matches = store.load(now)
    if manifest.get("candidate_id") != store.candidate_id or manifest.get("status") != "READY" or \
            len(raw_jobs) != len(raw_matches) or \
            [job.get("job_id") for job in raw_jobs] != manifest.get("job_ids"):
        raise ValueError("invalid candidate batch")

    result = {
        "status": "READY", "candidate_id": store.candidate_id,
        "batch_id": manifest["batch_id"], "jobs_found": len(raw_jobs),
        "prepared": 0, "existing": 0, "blocked": 0, "in_progress": 0,
        "daily_limit_reached": False, "blocked_job_ids": [],
        "confirmed_applications": 0,
    }
    normalized_now = utc_timestamp(now)
    if normalized_now is None:
        raise ValueError("current time required")
    local_day = datetime.fromisoformat(normalized_now.replace("Z", "+00:00")).astimezone(
        _MEXICO_CITY).date().isoformat()
    ledger_dir = Path(output_root) / store.candidate_id
    ledger_dir.mkdir(parents=True, exist_ok=True)
    with _ledger(ledger_dir / ".preparation-ledger.sqlite3") as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS preparations (
            day TEXT NOT NULL, job_id TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('reserved', 'complete')),
            reserved_at TEXT NOT NULL, PRIMARY KEY(day, job_id)
        )""")
        for raw_job, raw_match in zip(raw_jobs, raw_matches):
            if raw_match.get("job_id") != raw_job.get("job_id") or \
                    raw_match.get("candidate_id") != store.candidate_id:
                raise ValueError("match belongs to another job or candidate")
            if raw_match.get("decision") != "shortlist" or \
                    type(raw_match.get("score")) is not int or \
                    raw_match["score"] < prepare_threshold or \
                    raw_match.get("unknowns") or raw_match.get("reasons"):
                continue
            job_id = raw_job["job_id"]
            reservation = _reserve(conn, local_day, job_id, max_preparations, normalized_now)
            if reservation == "limit":
                result["daily_limit_reached"] = True
                break
            if reservation == "existing":
                result["existing"] += 1
                continue
            if reservation == "in_progress":
                package_dir = ledger_dir / re.sub(r"[^A-Za-z0-9_-]", "_", job_id)
                if (package_dir / "resume-tailored.pdf").is_file() and \
                        (package_dir / "evidence-map.json").is_file():
                    _finish(conn, local_day, job_id, complete=True)
                    result["existing"] += 1
                else:
                    result["in_progress"] += 1
                continue
            try:
                job = job_from_dict(raw_job)
                match = MatchResult(**raw_match)
                prepare_application(job, match, profile, output_root)
            except FileExistsError:
                _finish(conn, local_day, job_id, complete=reservation == "retry")
                result["existing"] += 1
            except ValueError:
                _finish(conn, local_day, job_id, complete=False)
                result["blocked"] += 1
                result["blocked_job_ids"].append(job_id)
            except Exception:
                _finish(conn, local_day, job_id, complete=False)
                raise
            else:
                _finish(conn, local_day, job_id, complete=True)
                result["prepared"] += 1
    return result
