"""Private application event ledger. Recording a state never contacts a portal."""

import hashlib
import json
import re
import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path

from .dedupe import canonical_url
from .normalizer import utc_timestamp
from .workflow import application_key, transition


@contextmanager
def _database(path: Path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    try:
        with closing(sqlite3.connect(path, timeout=5)) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS applications (
                application_id TEXT PRIMARY KEY, candidate_id TEXT NOT NULL,
                job_id TEXT NOT NULL, portal TEXT NOT NULL, status TEXT NOT NULL,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            )""")
            conn.execute("""CREATE TABLE IF NOT EXISTS application_events (
                event_id TEXT PRIMARY KEY, application_id TEXT NOT NULL,
                candidate_id TEXT NOT NULL, from_status TEXT, to_status TEXT NOT NULL,
                actor TEXT NOT NULL, observed_at TEXT NOT NULL, proof_digest TEXT NOT NULL
            )""")
            yield conn
    except sqlite3.Error as exc:
        raise OSError("private application tracker unavailable") from exc


class ApplicationTracker:
    def __init__(self, path: Path, candidate_id: str) -> None:
        if not isinstance(candidate_id, str) or not re.fullmatch(r"[a-z0-9_-]+", candidate_id):
            raise ValueError("invalid candidate ID")
        self.path = Path(path)
        self.candidate_id = candidate_id

    def register(self, job_id: str, portal_url: str, observed_at: str) -> str:
        timestamp = utc_timestamp(observed_at)
        if not isinstance(job_id, str) or not job_id or timestamp is None:
            raise ValueError("invalid application identity")
        portal = canonical_url(portal_url)
        app_id = application_key(self.candidate_id, job_id, portal)
        with _database(self.path) as conn, conn:
            row = conn.execute(
                "SELECT candidate_id FROM applications WHERE application_id=?", (app_id,),
            ).fetchone()
            if row is not None:
                if row[0] != self.candidate_id:
                    raise ValueError("application belongs to another candidate")
                return app_id
            conn.execute("INSERT INTO applications VALUES (?, ?, ?, ?, ?, ?, ?)",
                         (app_id, self.candidate_id, job_id, portal,
                          "DISCOVERED", timestamp, timestamp))
            event_id = hashlib.sha256(f"{app_id}:DISCOVERED".encode("utf-8")).hexdigest()
            conn.execute("INSERT INTO application_events VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                         (event_id, app_id, self.candidate_id, None, "DISCOVERED",
                          "collector", timestamp, ""))
        return app_id

    def advance(self, app_id: str, target: str, observed_at: str, *,
                proof: dict | None = None, actor: str = "holder") -> bool:
        timestamp = utc_timestamp(observed_at)
        if timestamp is None or actor not in {"holder", "policy", "portal_receipt", "gmail_review"} or \
                not isinstance(proof, (dict, type(None))):
            raise ValueError("invalid application event")
        if target == "SUBMISSION_AUTHORIZED" and actor != "holder":
            raise ValueError("only the holder can authorize submission")
        if target == "SUBMITTED" and actor not in {"holder", "portal_receipt"}:
            raise ValueError("submission requires a holder or portal receipt")
        with _database(self.path) as conn, conn:
            row = conn.execute(
                "SELECT candidate_id, job_id, portal, status, updated_at FROM applications "
                "WHERE application_id=?", (app_id,),
            ).fetchone()
            if row is None or row[0] != self.candidate_id:
                raise ValueError("application not found for candidate")
            _, job_id, portal, current, updated_at = row
            if current == target:
                return False
            if timestamp < updated_at:
                raise ValueError("application event predates current state")
            transition(current, target, proof=proof, candidate_id=self.candidate_id,
                       job_id=job_id, portal=portal)
            try:
                proof_json = json.dumps(proof or {}, sort_keys=True, separators=(",", ":"))
            except TypeError as exc:
                raise ValueError("invalid application evidence") from exc
            proof_digest = hashlib.sha256(proof_json.encode("utf-8")).hexdigest()
            event_id = hashlib.sha256(
                f"{app_id}\n{current}\n{target}\n{timestamp}\n{proof_digest}".encode("utf-8")
            ).hexdigest()
            conn.execute("UPDATE applications SET status=?, updated_at=? WHERE application_id=?",
                         (target, timestamp, app_id))
            conn.execute("INSERT INTO application_events VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                         (event_id, app_id, self.candidate_id, current, target,
                          actor, timestamp, proof_digest))
        return True

    def status(self, app_id: str) -> str:
        with _database(self.path) as conn:
            row = conn.execute(
                "SELECT status FROM applications WHERE application_id=? AND candidate_id=?",
                (app_id, self.candidate_id),
            ).fetchone()
            if row is None:
                raise ValueError("application not found for candidate")
            return row[0]

    def events(self, app_id: str) -> list[dict]:
        with _database(self.path) as conn:
            rows = conn.execute(
                "SELECT from_status, to_status, actor, observed_at, proof_digest "
                "FROM application_events WHERE application_id=? AND candidate_id=? ORDER BY rowid",
                (app_id, self.candidate_id),
            ).fetchall()
            return [dict(zip(("from_status", "to_status", "actor", "observed_at",
                              "proof_digest"), row)) for row in rows]

    def summary(self) -> dict:
        with _database(self.path) as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) FROM applications WHERE candidate_id=? GROUP BY status",
                (self.candidate_id,),
            ).fetchall()
            by_status = {status: count for status, count in rows}
            return {"total": sum(by_status.values()), "by_status": by_status}


def register_discovered_from_summary(tracker: ApplicationTracker, summary: dict) -> dict:
    if summary.get("status") not in {"READY", "ALREADY_PROCESSED"}:
        return {"added": 0}
    if summary.get("candidate_id") != tracker.candidate_id or \
            not isinstance(summary.get("opportunities"), list):
        raise ValueError("summary belongs to another candidate")
    observed_at = summary.get("generated_at") or summary.get("retrieved_at")
    if utc_timestamp(observed_at) is None:
        raise ValueError("summary lacks observation time")
    before = tracker.summary()["total"]
    for item in summary["opportunities"]:
        tracker.register(item["job_id"], item["apply_url"], observed_at)
    after = tracker.summary()
    return {"added": after["total"] - before, **after}


def register_prepared_from_summary(tracker: ApplicationTracker, summary: dict) -> dict:
    if summary.get("status") != "READY":
        return {"advanced": 0}
    if summary.get("candidate_id") != tracker.candidate_id or \
            not isinstance(summary.get("completed_items"), list):
        raise ValueError("preparation belongs to another candidate")
    observed_at = summary.get("completed_at")
    if utc_timestamp(observed_at) is None:
        raise ValueError("preparation lacks completion time")
    path = ("DISCOVERED", "ELIGIBLE", "SHORTLISTED", "APPROVED", "PREPARED")
    advanced = 0
    for item in summary["completed_items"]:
        app_id = tracker.register(item["job_id"], item["apply_url"], observed_at)
        current = tracker.status(app_id)
        if current not in path:
            continue
        for target in path[path.index(current) + 1:]:
            proof = {"batch_id": summary.get("batch_id"), "mode": "PREPARE"} \
                if target == "APPROVED" else None
            tracker.advance(app_id, target, observed_at, proof=proof, actor="policy")
        advanced += int(current != "PREPARED")
    return {"advanced": advanced, **tracker.summary()}
