"""Candidate-scoped S3 batches and a conditional DynamoDB lock.

The injected clients allow offline tests. This module never creates AWS clients or
submits an application.
"""

import json
import re
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from .batch import build_manifest, validate_batch
from .matcher import SearchPolicy, match_job
from .models import Job
from .normalizer import utc_timestamp


_MEXICO_CITY = ZoneInfo("America/Mexico_City")
MAX_BATCH_OBJECT_BYTES = 32_000_000


def _batch_time(now: str) -> tuple[str, str, str]:
    generated_at = utc_timestamp(now)
    if generated_at is None:
        raise ValueError("current time required")
    current = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
    local_day = current.astimezone(_MEXICO_CITY).date()
    next_midnight = datetime.combine(local_day + timedelta(days=1), datetime.min.time(), _MEXICO_CITY)
    expires_at = next_midnight.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return generated_at, local_day.isoformat(), expires_at


def _put_json(s3, bucket: str, key: str, value: object) -> None:
    s3.put_object(Bucket=bucket, Key=key,
                  Body=json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
                  ContentType="application/json")


def mark_failed_batch(candidate_id: str, now: str, s3, bucket: str) -> dict:
    """Invalidate a candidate's current-day manifest after a failed publication."""
    if not re.fullmatch(r"[a-z0-9_-]+", candidate_id) or not bucket:
        raise ValueError("invalid candidate publication settings")
    generated_at, local_day, expires_at = _batch_time(now)
    manifest = build_manifest(candidate_id, f"{candidate_id}:{local_day}", [],
                              generated_at, expires_at, matches=[], status="FAILED")
    _put_json(s3, bucket, f"batches/{local_day}/manifest.json", manifest)
    return manifest


def publish_candidate_batch(jobs: list[Job], policy: SearchPolicy, now: str,
                            s3, bucket: str, *, max_jobs: int = 10) -> dict:
    """Publish a FAILED guard first, then a READY manifest after all data is stored."""
    if not bucket or max_jobs < 1 or not re.fullmatch(r"[a-z0-9_-]+", policy.candidate_id):
        raise ValueError("invalid candidate publication settings")
    generated_at, local_day, expires_at = _batch_time(now)
    for job in jobs:
        retrieved = utc_timestamp(job.retrieved_at)
        if retrieved is None or datetime.fromisoformat(retrieved.replace("Z", "+00:00")).astimezone(
                _MEXICO_CITY).date().isoformat() != local_day:
            raise ValueError("stale public job cannot be republished")

    results = [(job, match_job(job, policy, generated_at)) for job in jobs]
    results = [(job, match) for job, match in results if match.decision != "exclude"]
    results.sort(key=lambda pair: (0 if pair[1].decision == "shortlist" else 1,
                                   -pair[1].score, pair[0].job_id))
    results = results[:max_jobs]
    selected_jobs = [job.to_dict() for job, _ in results]
    selected_matches = [asdict(match) for _, match in results]
    batch_id = f"{policy.candidate_id}:{local_day}"
    prefix = f"batches/{local_day}/"
    ready = build_manifest(policy.candidate_id, batch_id, selected_jobs, generated_at,
                           expires_at, matches=selected_matches)
    mark_failed_batch(policy.candidate_id, generated_at, s3, bucket)
    _put_json(s3, bucket, prefix + "jobs.json", selected_jobs)
    _put_json(s3, bucket, prefix + "matches.json", selected_matches)
    _put_json(s3, bucket, prefix + "manifest.json", ready)
    return ready


class CandidateBatchStore:
    def __init__(self, candidate_id: str, bucket: str, s3, state_table) -> None:
        if not re.fullmatch(r"[a-z0-9_-]+", candidate_id) or not bucket:
            raise ValueError("invalid candidate batch store")
        self.candidate_id = candidate_id
        self.bucket = bucket
        self.s3 = s3
        self.state_table = state_table

    def _get_json(self, key: str):
        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=key)
            stream = response["Body"]
            try:
                if response.get("ContentLength", 0) > MAX_BATCH_OBJECT_BYTES:
                    raise ValueError("private batch object exceeds size limit")
                body = stream.read(MAX_BATCH_OBJECT_BYTES + 1)
            finally:
                stream.close()
        except Exception as exc:
            code = getattr(exc, "response", {}).get("Error", {}).get("Code")
            if isinstance(exc, KeyError) or code in {"NoSuchKey", "404"}:
                raise ValueError("batch object missing") from exc
            raise
        if len(body) > MAX_BATCH_OBJECT_BYTES:
            raise ValueError("private batch object exceeds size limit")
        return json.loads(body)

    def load(self, now: str) -> tuple[dict, list[dict], list[dict]]:
        _, local_day, _ = _batch_time(now)
        prefix = f"batches/{local_day}/"
        manifest = self._get_json(prefix + "manifest.json")
        if not isinstance(manifest, dict) or manifest.get("status") != "READY":
            raise ValueError("candidate batch is not ready")
        jobs = self._get_json(prefix + "jobs.json")
        matches = self._get_json(prefix + "matches.json")
        if not isinstance(jobs, list) or not isinstance(matches, list):
            raise ValueError("invalid candidate batch payload")
        validate_batch(manifest, jobs, self.candidate_id, now, matches=matches)
        if [item.get("job_id") for item in matches] != manifest["job_ids"] or any(
                item.get("candidate_id") != self.candidate_id for item in matches):
            raise ValueError("match results do not belong to this batch")
        return manifest, jobs, matches

    def acquire_lock(self, manifest: dict, now: str) -> bool:
        current, local_day, _ = _batch_time(now)
        if manifest.get("candidate_id") != self.candidate_id or manifest.get("status") != "READY" or \
                manifest.get("batch_id") != f"{self.candidate_id}:{local_day}":
            raise ValueError("lock requires current candidate batch")
        expires = utc_timestamp(manifest.get("expires_at"))
        if expires is None or current >= expires:
            raise ValueError("batch lock expired")
        item = {
            "pk": f"BATCH#{self.candidate_id}#{manifest['batch_id']}", "sk": "LOCK",
            "candidate_id": self.candidate_id, "batch_id": manifest["batch_id"],
            "created_at": current,
            "expires_at": int(datetime.fromisoformat(expires.replace("Z", "+00:00")).timestamp()),
        }
        try:
            self.state_table.put_item(Item=item,
                                      ConditionExpression="attribute_not_exists(pk) AND attribute_not_exists(sk)")
        except Exception as exc:
            if getattr(exc, "response", {}).get("Error", {}).get("Code") == "ConditionalCheckFailedException":
                return False
            raise
        return True
