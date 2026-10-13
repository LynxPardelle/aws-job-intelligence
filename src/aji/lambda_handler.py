"""AWS collector entry point. Disabled unless explicitly configured."""

import json
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from .connectors import build_feed_url
from .dedupe import deduplicate_jobs
from .normalizer import utc_timestamp
from .transport import fetch_jobs


def collect_once(sources: list[dict], now: str, *, fetcher, writer, max_sources: int) -> dict:
    active = [item for item in sources if item.get("enabled") is True]
    if max_sources < 1 or len(active) > max_sources:
        raise ValueError("source quota exceeded")
    for item in active:
        if not isinstance(item.get("company"), str) or not item["company"].strip():
            raise ValueError("company required")
        build_feed_url(item.get("source"), item.get("board"))

    retrieved_at = utc_timestamp(now)
    if retrieved_at is None:
        raise ValueError("collection time required")
    all_jobs = []
    for item in active:
        all_jobs.extend(fetcher(item["source"], item["board"], item["company"], retrieved_at))
        if len(all_jobs) > 1000:
            raise ValueError("job quota exceeded")
    unique = deduplicate_jobs(all_jobs)
    expiry = int((datetime.fromisoformat(retrieved_at.replace("Z", "+00:00")) + timedelta(days=30)).timestamp())
    for job in unique:
        item = job.to_dict()
        item["expires_at"] = expiry
        if len(json.dumps(item, ensure_ascii=False).encode("utf-8")) > 300_000:
            raise ValueError("job item exceeds size limit")
        writer(item)
    return {"status": "OK", "jobs_written": len(unique), "sources": len(active)}


def _dynamodb_types(value):
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {key: _dynamodb_types(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_dynamodb_types(item) for item in value]
    return value


def handler(event, context):
    if os.getenv("AJI_ENABLED") != "true":
        return {"status": "DISABLED", "jobs_written": 0}
    sources = json.loads(os.environ["AJI_SOURCES_JSON"])
    if not isinstance(sources, list) or not sources:
        raise ValueError("sources not configured")
    table_name = os.environ["AJI_JOBS_TABLE"]
    max_sources = int(os.environ.get("AJI_MAX_SOURCES", "10"))
    import boto3  # Lambda runtime SDK; not required for local tests.

    table = boto3.resource("dynamodb").Table(table_name)
    now = datetime.now(timezone.utc).isoformat()
    return collect_once(sources, now, fetcher=fetch_jobs,
                        writer=lambda item: table.put_item(Item=_dynamodb_types(item)),
                        max_sources=max_sources)
