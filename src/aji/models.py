"""Versioned public job data. Candidate information does not belong here."""

from dataclasses import MISSING, asdict, dataclass, fields
from typing import Literal


@dataclass(frozen=True)
class Salary:
    currency: str
    interval: str
    minimum: float | None
    maximum: float | None
    basis: Literal["gross", "net", "contract", "unknown"] = "unknown"

    def __post_init__(self) -> None:
        if self.basis not in {"gross", "net", "contract", "unknown"}:
            raise ValueError("invalid salary basis")


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
    schema_version: str = "1.1"
    travel_requirement: Literal["required", "not_required", "unknown"] = "unknown"
    rotating_shifts_requirement: Literal["required", "not_required", "unknown"] = "unknown"

    def __post_init__(self) -> None:
        valid = {"required", "not_required", "unknown"}
        if self.schema_version != "1.1":
            raise ValueError("unsupported public job version")
        if self.travel_requirement not in valid or self.rotating_shifts_requirement not in valid:
            raise ValueError("invalid job requirement status")

    def to_dict(self) -> dict:
        return asdict(self)


def job_from_dict(item: dict) -> Job:
    """Rebuild a public Job from a DynamoDB item without its index/TTL fields."""
    if not isinstance(item, dict) or item.get("schema_version") not in {"1.0", "1.1"}:
        raise ValueError("unsupported public job")
    legacy = item["schema_version"] == "1.0"
    if not legacy and ("travel_requirement" not in item or "rotating_shifts_requirement" not in item):
        raise ValueError("current public job is missing requirement status")
    data = {field.name: item[field.name] if field.default is MISSING else
            item.get(field.name, field.default) for field in fields(Job)}
    if legacy:
        data["schema_version"] = "1.1"
        data["travel_requirement"] = "unknown"
        data["rotating_shifts_requirement"] = "unknown"
    raw_salary = data["salary"]
    if raw_salary is not None:
        data["salary"] = Salary(
            currency=raw_salary["currency"], interval=raw_salary["interval"],
            minimum=float(raw_salary["minimum"]) if raw_salary["minimum"] is not None else None,
            maximum=float(raw_salary["maximum"]) if raw_salary["maximum"] is not None else None,
            basis=raw_salary.get("basis", "unknown"),
        )
    return Job(**data)
