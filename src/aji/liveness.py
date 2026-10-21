"""Recheck a job against its allowlisted public feed before local preparation."""

from dataclasses import dataclass

from .dedupe import canonical_url
from .models import Job
from .normalizer import utc_timestamp
from .transport import fetch_jobs


@dataclass(frozen=True)
class LivenessResult:
    status: str
    reason: str
    checked_at: str


def check_job_liveness(job: Job, now: str, *, fetcher=fetch_jobs) -> LivenessResult:
    checked_at = utc_timestamp(now)
    if checked_at is None:
        raise ValueError("current time required")
    if job.status != "open":
        return LivenessResult("closed" if job.status == "closed" else "unknown",
                              "job_status_not_open", checked_at)
    try:
        current_jobs = fetcher(job.source, job.board, job.company, checked_at)
        if not isinstance(current_jobs, list):
            raise ValueError("invalid feed result")
        matching = [current for current in current_jobs if current.job_id == job.job_id]
        if matching:
            if any(canonical_url(current.source_url) == canonical_url(job.source_url)
                   for current in matching):
                return LivenessResult("active", "present_in_official_feed", checked_at)
            return LivenessResult("unknown", "posting_url_changed", checked_at)
        if job.source == "getonbrd":
            return LivenessResult("unknown", "not_in_bounded_category_page", checked_at)
        return LivenessResult("closed", "not_in_official_ats_feed", checked_at)
    except Exception:
        return LivenessResult("unknown", "official_feed_unavailable", checked_at)
