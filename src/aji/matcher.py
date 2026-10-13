"""Candidate-specific scoring. Hard filters always outrank numeric scores."""

import re
from dataclasses import dataclass
from datetime import datetime

from .models import Job
from .normalizer import utc_timestamp


@dataclass(frozen=True)
class SearchPolicy:
    candidate_id: str
    technologies: tuple[str, ...]
    allowed_seniority: tuple[str, ...]
    allowed_modalities: tuple[str, ...]
    minimum_salary: float | None
    salary_currency: str | None
    shortlist_threshold: int
    salary_interval: str = "year"
    roles: tuple[str, ...] = ()
    excluded_companies: tuple[str, ...] = ()
    prepare_threshold: int | None = None

    def __post_init__(self) -> None:
        if not self.candidate_id or not 0 <= self.shortlist_threshold <= 100:
            raise ValueError("invalid search policy")
        if self.minimum_salary is not None and (self.minimum_salary < 0 or not self.salary_currency):
            raise ValueError("salary minimum requires currency")
        if self.prepare_threshold is not None and not self.shortlist_threshold <= self.prepare_threshold <= 100:
            raise ValueError("invalid preparation threshold")


@dataclass(frozen=True)
class MatchResult:
    candidate_id: str
    job_id: str
    decision: str
    score: int
    components: dict[str, int]
    matched_technologies: tuple[str, ...]
    missing_technologies: tuple[str, ...]
    unknowns: tuple[str, ...]
    reasons: tuple[str, ...]
    scoring_version: str = "1.0"


def _contains(text: str, term: str) -> bool:
    return bool(re.search(r"(?<!\w)" + re.escape(term.casefold()) + r"(?!\w)", text.casefold()))


def _annual_interval(value: str) -> str:
    return value.replace(" ", "").lower()


def match_job(job: Job, policy: SearchPolicy, now: str) -> MatchResult:
    now_iso = utc_timestamp(now)
    if now_iso is None:
        raise ValueError("now is required")
    current = datetime.fromisoformat(now_iso.replace("Z", "+00:00"))
    reasons: list[str] = []
    unknowns: list[str] = []
    review_flags: list[str] = []

    if job.status == "closed":
        reasons.append("closed")
    elif job.status == "unknown":
        unknowns.append("status")

    if job.mexico_eligibility == "ineligible":
        reasons.append("not_eligible_from_mexico")
    elif job.mexico_eligibility == "unknown":
        unknowns.append("mexico_eligibility")

    if policy.roles and not any(_contains(job.title, role) for role in policy.roles):
        reasons.append("incompatible_role")
    if job.company.casefold() in {company.casefold() for company in policy.excluded_companies}:
        reasons.append("excluded_company")

    modality_match = not policy.allowed_modalities or job.modality in policy.allowed_modalities
    if job.modality == "unknown" and policy.allowed_modalities:
        unknowns.append("modality")
    elif not modality_match:
        reasons.append("incompatible_modality")

    seniority_match = not policy.allowed_seniority or job.seniority in policy.allowed_seniority
    if job.seniority is None and policy.allowed_seniority:
        unknowns.append("seniority")
    elif not seniority_match:
        reasons.append("incompatible_seniority")

    text = f"{job.title} {job.description}"
    matched = tuple(term for term in policy.technologies if _contains(text, term))
    missing = tuple(term for term in policy.technologies if term not in matched)
    stack = round(30 * len(matched) / len(policy.technologies)) if policy.technologies else 0
    if not policy.technologies:
        unknowns.append("technologies_policy")

    eligibility_modality = 25 if job.mexico_eligibility == "eligible" and modality_match and job.modality != "unknown" else 0
    seniority = 20 if job.seniority is not None and seniority_match else 0

    salary = 0
    if job.salary is None or job.salary.minimum is None or job.salary.maximum is None:
        unknowns.append("salary")
    elif policy.minimum_salary is None:
        salary = 15
    elif job.salary.currency != policy.salary_currency or _annual_interval(job.salary.interval) not in {
        _annual_interval(policy.salary_interval), "1" + _annual_interval(policy.salary_interval)
    }:
        unknowns.append("salary_comparability")
    elif job.salary.maximum < policy.minimum_salary:
        reasons.append("below_salary_minimum")
    elif job.salary.minimum < policy.minimum_salary:
        review_flags.append("salary_range_overlaps_minimum")
    else:
        salary = 15

    latest = job.published_at or job.updated_at
    if latest:
        posted = datetime.fromisoformat(latest.replace("Z", "+00:00"))
        age_days = (current - posted).total_seconds() / 86400
        freshness_quality = 10 if 0 <= age_days <= 30 and job.description else 0
    else:
        freshness_quality = 5 if job.description else 0
        unknowns.append("job_date")

    components = {
        "stack": stack,
        "eligibility_modality": eligibility_modality,
        "seniority": seniority,
        "salary": salary,
        "freshness_quality": freshness_quality,
    }
    score = sum(components.values())
    if reasons:
        decision = "exclude"
    elif unknowns or review_flags or score < policy.shortlist_threshold:
        decision = "review"
    else:
        decision = "shortlist"
    return MatchResult(policy.candidate_id, job.job_id, decision, score, components,
                       matched, missing, tuple(unknowns), tuple(reasons + review_flags))
