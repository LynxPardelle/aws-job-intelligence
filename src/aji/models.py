"""Versioned public job data. Candidate information does not belong here."""

from dataclasses import asdict, dataclass
from typing import Literal


@dataclass(frozen=True)
class Salary:
    currency: str
    interval: str
    minimum: float | None
    maximum: float | None


@dataclass(frozen=True)
class Job:
    job_id: str
    source: Literal["greenhouse", "lever", "ashby"]
    board: str
    external_id: str
    company: str
    title: str
    description: str
    location: str | None
    modality: Literal["remote", "hybrid", "onsite", "unknown"]
    mexico_eligibility: Literal["eligible", "ineligible", "unknown"]
    seniority: str | None
    salary: Salary | None
    source_url: str
    apply_url: str
    published_at: str | None
    updated_at: str | None
    status: Literal["open", "closed", "unknown"]
    feed_url: str
    retrieved_at: str
    schema_version: str = "1.0"

    def to_dict(self) -> dict:
        return asdict(self)
