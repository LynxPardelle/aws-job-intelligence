"""Candidate-scoped local memory of seen public posting URLs."""

import re
import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path

from .dedupe import canonical_url


def record_seen_jobs(path: Path, candidate_id: str, day: str,
                     postings: list[dict]) -> list[dict]:
    if not isinstance(candidate_id, str) or not re.fullmatch(r"[a-z0-9_-]+", candidate_id):
        raise ValueError("invalid candidate ID")
    if date.fromisoformat(day).isoformat() != day or not isinstance(postings, list):
        raise ValueError("invalid history date or postings")
    normalized = []
    for posting in postings:
        if not isinstance(posting, dict) or not isinstance(posting.get("job_id"), str) or \
                not posting["job_id"] or len(posting["job_id"]) > 256:
            raise ValueError("invalid posting identity")
        normalized.append((posting["job_id"], canonical_url(posting.get("source_url", ""))))

    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with closing(sqlite3.connect(db_path, timeout=5)) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS seen_jobs (
                candidate_id TEXT NOT NULL, canonical_url TEXT NOT NULL,
                first_seen TEXT NOT NULL, last_seen TEXT NOT NULL,
                seen_days INTEGER NOT NULL, last_job_id TEXT NOT NULL,
                PRIMARY KEY(candidate_id, canonical_url)
            )""")
            conn.execute("BEGIN IMMEDIATE")
            result = []
            try:
                for job_id, url in normalized:
                    row = conn.execute(
                        "SELECT first_seen, last_seen, seen_days, last_job_id FROM seen_jobs "
                        "WHERE candidate_id=? AND canonical_url=?", (candidate_id, url),
                    ).fetchone()
                    if row and row[1] > day:
                        raise ValueError("history date goes backwards")
                    if row:
                        first_seen, last_seen, seen_days, last_job_id = row
                        seen_days += int(last_seen != day)
                        conn.execute(
                            "UPDATE seen_jobs SET last_seen=?, seen_days=?, last_job_id=? "
                            "WHERE candidate_id=? AND canonical_url=?",
                            (day, seen_days, job_id, candidate_id, url),
                        )
                    else:
                        first_seen, seen_days, last_job_id = day, 1, job_id
                        conn.execute(
                            "INSERT INTO seen_jobs VALUES (?, ?, ?, ?, ?, ?)",
                            (candidate_id, url, day, day, seen_days, job_id),
                        )
                    result.append({"seen_before": first_seen < day,
                                   "first_seen": first_seen, "seen_days": seen_days,
                                   "possible_repost": bool(row and last_job_id != job_id)})
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            return result
    except sqlite3.Error as exc:
        raise OSError("local job history unavailable") from exc


def annotate_summary_history(summary: dict, path: Path, candidate_id: str,
                             day: str) -> dict:
    if summary.get("status") not in {"READY", "ALREADY_PROCESSED"}:
        return summary
    if summary.get("candidate_id", candidate_id) != candidate_id or \
            not isinstance(summary.get("opportunities"), list):
        raise ValueError("summary belongs to another candidate or has no opportunities")
    opportunities = summary["opportunities"]
    annotations = record_seen_jobs(path, candidate_id, day, opportunities)
    decorated = [{**posting, **annotation} for posting, annotation in
                 zip(opportunities, annotations)]
    return {**summary, "opportunities": decorated,
            "new_opportunities": sum(not entry["seen_before"] for entry in annotations),
            "repeated_opportunities": sum(entry["seen_before"] for entry in annotations),
            "possible_reposts": sum(entry["possible_repost"] for entry in annotations)}
