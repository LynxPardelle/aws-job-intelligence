"""Candidate-scoped batch publisher Lambda. Disabled until approved and configured."""

import json
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .aws_batch_io import mark_failed_batch, publish_candidate_batch
from .matcher import SearchPolicy
from .models import job_from_dict
from .normalizer import utc_timestamp


_MEXICO_CITY = ZoneInfo("America/Mexico_City")
MAX_POLICY_BYTES = 65_536


def _policy_from_dict(raw: dict, candidate_id: str) -> tuple[SearchPolicy, int]:
    if not isinstance(raw, dict) or raw.get("candidate_id") != candidate_id:
        raise ValueError("policy belongs to another candidate")
    allowed_keys = {"candidate_id", "roles", "technologies", "allowed_seniority",
                    "allowed_modalities", "eligible_countries", "minimum_salary",
                    "salary_currency", "salary_interval", "salary_basis", "excluded_companies",
                    "shortlist_threshold", "prepare_threshold", "max_jobs_per_day",
                    "application_mode"}
    if set(raw) - allowed_keys:
        raise ValueError("unsupported search policy field")
    if raw.get("eligible_countries", ["MX"]) != ["MX"]:
        raise ValueError("only Mexican eligibility is implemented")
    if raw.get("application_mode", "PREPARE") != "PREPARE":
        raise ValueError("automatic submission is disabled")

    def terms(key: str) -> tuple[str, ...]:
        values = raw.get(key, [])
        if not isinstance(values, list) or any(not isinstance(v, str) or not v.strip() for v in values):
            raise ValueError(f"invalid {key} list")
        return tuple(values)

    threshold = raw.get("shortlist_threshold")
    prepare = raw.get("prepare_threshold", threshold)
    max_jobs = raw.get("max_jobs_per_day", 10)
    if any(type(value) is not int for value in (threshold, prepare, max_jobs)):
        raise ValueError("thresholds and quota must be integers")
    policy = SearchPolicy(
        candidate_id=candidate_id,
        technologies=terms("technologies"),
        allowed_seniority=terms("allowed_seniority"),
        allowed_modalities=terms("allowed_modalities"),
        minimum_salary=raw.get("minimum_salary"),
        salary_currency=raw.get("salary_currency"),
        shortlist_threshold=threshold,
        salary_interval=raw.get("salary_interval", "year"),
        salary_basis=raw.get("salary_basis", "reported"),
        roles=terms("roles"),
        excluded_companies=terms("excluded_companies"),
        prepare_threshold=prepare,
    )
    if not 1 <= max_jobs <= 100:
        raise ValueError("invalid candidate daily quota")
    return policy, max_jobs


def publish_once(candidate_id: str, public_table, s3, bucket: str,
                 policy: SearchPolicy, now: str, *, max_jobs: int = 10) -> dict:
    """Require a completed collection marker before querying one collection run."""
    normalized = utc_timestamp(now)
    if normalized is None:
        raise ValueError("publication time required")
    local_day = datetime.fromisoformat(normalized.replace("Z", "+00:00")).astimezone(
        _MEXICO_CITY).date().isoformat()
    try:
        if policy.candidate_id != candidate_id:
            raise ValueError("policy belongs to another candidate")
        marker = public_table.get_item(Key={"job_id": f"run#{local_day}"},
                                       ConsistentRead=True).get("Item")
        if not isinstance(marker, dict) or marker.get("status") != "COMPLETE" or not marker.get("run_id"):
            raise ValueError("today's public collection is incomplete")
        run_id = marker["run_id"]
        items = []
        start_key = None
        while True:
            request = {
                "IndexName": "collection-run-index",
                "KeyConditionExpression": "collection_run_id = :run_id",
                "ExpressionAttributeValues": {":run_id": run_id},
            }
            if start_key is not None:
                request["ExclusiveStartKey"] = start_key
            page = public_table.query(**request)
            items.extend(page.get("Items", []))
            if len(items) > 1000:
                raise ValueError("collection result exceeds quota")
            start_key = page.get("LastEvaluatedKey")
            if not start_key:
                break
        if len(items) != int(marker.get("job_count", -1)) or any(
                item.get("record_type") != "job" or item.get("collection_run_id") != run_id
                for item in items):
            raise ValueError("public collection count or identity mismatch")
        jobs = [job_from_dict(item) for item in items]
        return publish_candidate_batch(jobs, policy, normalized, s3, bucket, max_jobs=max_jobs)
    except Exception:
        mark_failed_batch(candidate_id, normalized, s3, bucket)
        raise


def handler(event, context):
    if os.getenv("AJI_PUBLISH_ENABLED") != "true":
        return {"status": "DISABLED"}
    candidate_id = os.environ["AJI_CANDIDATE_ID"]
    bucket = os.environ["AJI_PRIVATE_BUCKET"]
    policy_key = os.environ.get("AJI_POLICY_KEY", "config/search-policy.json")
    now = datetime.now(timezone.utc).isoformat()
    import boto3  # Available in the Lambda runtime; injected clients are used in local tests.

    s3 = boto3.client("s3")
    try:
        response = s3.get_object(Bucket=bucket, Key=policy_key)
        stream = response["Body"]
        try:
            if response.get("ContentLength", 0) > MAX_POLICY_BYTES:
                raise ValueError("private policy exceeds size limit")
            raw_bytes = stream.read(MAX_POLICY_BYTES + 1)
        finally:
            stream.close()
        if len(raw_bytes) > MAX_POLICY_BYTES:
            raise ValueError("private policy exceeds size limit")
        raw = json.loads(raw_bytes)
        policy, max_jobs = _policy_from_dict(raw, candidate_id)
        table = boto3.resource("dynamodb").Table(os.environ["AJI_PUBLIC_TABLE"])
    except Exception:
        mark_failed_batch(candidate_id, now, s3, bucket)
        raise
    manifest = publish_once(candidate_id, table, s3, bucket, policy, now, max_jobs=max_jobs)
    return {"status": "READY", "jobs_published": len(manifest["job_ids"])}
