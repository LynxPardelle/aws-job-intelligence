"""Local, retryable package preparation from a validated private batch.

The caller supplies a CandidateBatchStore; its load() validates the manifest and
checksums. This module never claims the permanent batch lock or sends forms.
"""

from pathlib import Path

from .application_package import prepare_application
from .matcher import MatchResult
from .models import job_from_dict


def prepare_daily_batch(store, now: str, profile: dict, output_root: Path, *,
                        max_preparations: int, prepare_threshold: int) -> dict:
    if type(max_preparations) is not int or not 1 <= max_preparations <= 10:
        raise ValueError("invalid daily preparation limit")
    if type(prepare_threshold) is not int or not 0 <= prepare_threshold <= 100:
        raise ValueError("invalid preparation threshold")
    if not isinstance(profile, dict) or profile.get("candidate_id") != store.candidate_id or \
            profile.get("approved_by_holder") is not True or not profile.get("validated_at") or \
            not isinstance(profile.get("claims"), list) or not profile["claims"]:
        raise ValueError("candidate profile is not verified and approved")

    manifest, raw_jobs, raw_matches = store.load(now)
    if manifest.get("candidate_id") != store.candidate_id or manifest.get("status") != "READY" or \
            len(raw_jobs) != len(raw_matches) or \
            [job.get("job_id") for job in raw_jobs] != manifest.get("job_ids"):
        raise ValueError("invalid candidate batch")

    result = {
        "status": "READY", "candidate_id": store.candidate_id,
        "batch_id": manifest["batch_id"], "jobs_found": len(raw_jobs),
        "prepared": 0, "existing": 0, "blocked": 0,
        "blocked_job_ids": [], "confirmed_applications": 0,
    }
    for raw_job, raw_match in zip(raw_jobs, raw_matches):
        if raw_match.get("job_id") != raw_job.get("job_id") or \
                raw_match.get("candidate_id") != store.candidate_id:
            raise ValueError("match belongs to another job or candidate")
        if raw_match.get("decision") != "shortlist" or \
                type(raw_match.get("score")) is not int or \
                raw_match["score"] < prepare_threshold or \
                raw_match.get("unknowns") or raw_match.get("reasons"):
            continue
        if result["prepared"] + result["existing"] >= max_preparations:
            break
        try:
            job = job_from_dict(raw_job)
            match = MatchResult(**raw_match)
            prepare_application(job, match, profile, output_root)
            result["prepared"] += 1
        except FileExistsError:
            result["existing"] += 1
        except ValueError:
            result["blocked"] += 1
            result["blocked_job_ids"].append(raw_job["job_id"])
    return result
