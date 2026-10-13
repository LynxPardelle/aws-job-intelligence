"""Private batch manifests and a local idempotency simulation."""

import hashlib
import json
from datetime import datetime
from zoneinfo import ZoneInfo

from .normalizer import utc_timestamp


_MEXICO_CITY = ZoneInfo("America/Mexico_City")


def _checksum(jobs: list[dict]) -> str:
    canonical = json.dumps(jobs, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def _datetime(value: str) -> datetime:
    normalized = utc_timestamp(value)
    if normalized is None:
        raise ValueError("timestamp required")
    return datetime.fromisoformat(normalized.replace("Z", "+00:00"))


def build_manifest(candidate_id: str, batch_id: str, jobs: list[dict], generated_at: str,
                   expires_at: str, *, status: str = "READY") -> dict:
    if not candidate_id or not batch_id or status not in {"READY", "FAILED"}:
        raise ValueError("invalid manifest identity or status")
    ids = [job["job_id"] for job in jobs]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate job in batch")
    return {
        "schema_version": "1.0", "batch_id": batch_id, "candidate_id": candidate_id,
        "status": status, "generated_at": utc_timestamp(generated_at),
        "expires_at": utc_timestamp(expires_at), "job_ids": ids,
        "checksum": _checksum(jobs), "scoring_version": "1.0",
    }


def validate_batch(manifest: dict, jobs: list[dict], candidate_id: str, now: str) -> None:
    if manifest.get("schema_version") != "1.0" or manifest.get("scoring_version") != "1.0":
        raise ValueError("unsupported batch version")
    if manifest.get("candidate_id") != candidate_id or manifest.get("status") != "READY":
        raise ValueError("batch not ready for candidate")
    current = _datetime(now)
    generated = _datetime(manifest["generated_at"])
    expires = _datetime(manifest["expires_at"])
    if generated > current or current >= expires:
        raise ValueError("batch outside valid time window")
    if generated.astimezone(_MEXICO_CITY).date() != current.astimezone(_MEXICO_CITY).date():
        raise ValueError("batch is not from current Mexico City day")
    ids = [job.get("job_id") for job in jobs]
    if ids != manifest.get("job_ids") or len(ids) != len(set(ids)):
        raise ValueError("batch job list differs")
    if _checksum(jobs) != manifest.get("checksum"):
        raise ValueError("batch checksum mismatch")


class BatchLock:
    """Local test double; AWS implementation must use a conditional DynamoDB write."""

    def __init__(self) -> None:
        self._locks: set[tuple[str, str]] = set()

    def try_acquire(self, candidate_id: str, batch_id: str) -> bool:
        key = (candidate_id, batch_id)
        if key in self._locks:
            return False
        self._locks.add(key)
        return True
