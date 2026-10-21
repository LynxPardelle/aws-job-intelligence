"""Inspect one fresh candidate batch and optionally claim its idempotency lock.

The batch store handles AWS access. This module never generates documents or
submits applications; the returned titles and URLs remain untrusted data.
"""


def inspect_daily_batch(store, now: str, *, acquire_lock: bool = False) -> dict:
    manifest, jobs, matches = store.load(now)
    candidate_id = store.candidate_id
    if manifest.get("candidate_id") != candidate_id or manifest.get("status") != "READY":
        raise ValueError("invalid candidate batch")
    if len(jobs) != len(matches) or [job.get("job_id") for job in jobs] != manifest.get("job_ids"):
        raise ValueError("batch jobs do not match manifest")
    opportunities = []
    for job, match in zip(jobs, matches):
        if match.get("job_id") != job.get("job_id") or match.get("candidate_id") != candidate_id:
            raise ValueError("match belongs to another job or candidate")
        if match.get("decision") not in {"shortlist", "review"} or \
                type(match.get("score")) is not int or not 0 <= match["score"] <= 100:
            raise ValueError("invalid match decision or score")
        opportunities.append({
            "job_id": job["job_id"], "title": job["title"], "company": job["company"],
            "source_url": job["source_url"], "decision": match["decision"],
            "score": match["score"], "salary": job.get("salary"),
            "unknowns": match.get("unknowns", []), "reasons": match.get("reasons", []),
        })

    status = "READY"
    if acquire_lock and not store.acquire_lock(manifest, now):
        status = "ALREADY_PROCESSED"
    return {
        "status": status, "candidate_id": candidate_id, "batch_id": manifest["batch_id"],
        "jobs_found": len(jobs),
        "shortlisted": sum(item["decision"] == "shortlist" for item in opportunities),
        "needs_review": sum(item["decision"] == "review" for item in opportunities),
        "cvs_prepared": 0, "confirmed_applications": 0,
        "opportunities": opportunities,
    }
