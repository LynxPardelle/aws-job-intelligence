"""Deduplication of normalized public jobs."""

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .models import Job
from .normalizer import public_https_url


def canonical_url(url: str) -> str:
    parts = urlsplit(public_https_url(url))
    host = parts.hostname.lower().rstrip(".")
    if parts.port == 443:
        host = f"{host}:443"
    query = [
        (key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in {"gh_src", "ref"}
    ]
    return urlunsplit(("https", host, parts.path.rstrip("/") or "/", urlencode(sorted(query)), ""))


def deduplicate_jobs(jobs: list[Job]) -> list[Job]:
    seen_ids: set[str] = set()
    seen_urls: set[str] = set()
    unique: list[Job] = []
    for job in jobs:
        url = canonical_url(job.source_url)
        if job.job_id in seen_ids or url in seen_urls:
            continue
        unique.append(job)
        seen_ids.add(job.job_id)
        seen_urls.add(url)
    return unique
