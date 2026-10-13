"""Versioned public job data. Candidate information does not belong here."""

from dataclasses import asdict, dataclass, fields
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


def job_from_dict(item: dict) -> Job:
    """Rebuild a public Job from a DynamoDB item without its index/TTL fields."""
    if not isinstance(item, dict) or item.get("schema_version") != "1.0":
        raise ValueError("unsupported public job")
    data = {field.name: item[field.name] for field in fields(Job)}
    raw_salary = data["salary"]
    if raw_salary is not None:
        data["salary"] = Salary(
            currency=raw_salary["currency"], interval=raw_salary["interval"],
            minimum=float(raw_salary["minimum"]) if raw_salary["minimum"] is not None else None,
            maximum=float(raw_salary["maximum"]) if raw_salary["maximum"] is not None else None,
        )
    return Job(**data)
