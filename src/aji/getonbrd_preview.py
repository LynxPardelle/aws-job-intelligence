"""Bounded local discovery from Get on Board; never prepares or submits."""

from dataclasses import asdict

from .dedupe import deduplicate_jobs
from .matcher import SearchPolicy, match_job
from .normalizer import utc_timestamp
from .transport import fetch_jobs


CATEGORIES = ("programming", "operations-management", "machine-learning-ai")


def build_getonbrd_preview(policy: SearchPolicy, now: str, *, fetcher=fetch_jobs,
                           max_jobs: int = 10) -> dict:
    if type(max_jobs) is not int or not 1 <= max_jobs <= 10:
        raise ValueError("invalid local preview quota")
    timestamp = utc_timestamp(now)
    if timestamp is None:
        raise ValueError("current time required")
    all_jobs = []
    counts = []
    for category in CATEGORIES:
        jobs = fetcher("getonbrd", category, "Get on Board", timestamp)
        if not isinstance(jobs, list):
            raise ValueError("invalid Get on Board feed result")
        all_jobs.extend(jobs)
        if len(all_jobs) > 300:
            raise ValueError("local discovery quota exceeded")
        counts.append({"category": category, "job_count": len(jobs)})
    unique = deduplicate_jobs(all_jobs)
    evaluated = [(job, match_job(job, policy, timestamp)) for job in unique]
    eligible = [(job, match) for job, match in evaluated if match.decision != "exclude"]
    eligible.sort(key=lambda pair: (0 if pair[1].decision == "shortlist" else 1,
                                   -pair[1].score, pair[0].job_id))
    opportunities = [{
        "job_id": job.job_id, "title": job.title, "company": job.company,
        "source_url": job.source_url, "apply_url": job.apply_url,
        "location": job.location,
        "decision": match.decision, "score": match.score,
        "salary": asdict(job.salary) if job.salary else None,
        "unknowns": list(match.unknowns), "reasons": list(match.reasons),
    } for job, match in eligible[:max_jobs]]
    return {
        "status": "READY" if all_jobs else "EMPTY", "candidate_id": policy.candidate_id,
        "retrieved_at": timestamp, "categories": counts,
        "jobs_fetched": len(all_jobs), "unique_jobs": len(unique),
        "excluded": len(unique) - len(eligible),
        "possibly_truncated_categories": [entry["category"] for entry in counts
                                          if entry["job_count"] >= 100],
        "total_shortlisted": sum(match.decision == "shortlist" for _, match in eligible),
        "total_needs_review": sum(match.decision == "review" for _, match in eligible),
        "shortlisted": sum(item["decision"] == "shortlist" for item in opportunities),
        "needs_review": sum(item["decision"] == "review" for item in opportunities),
        "opportunities": opportunities,
    }
