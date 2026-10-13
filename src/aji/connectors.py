"""Read-only public ATS feed adapters. No application submission endpoints."""

import re
from urllib.parse import urlsplit

from .models import Job, Salary
from .normalizer import explicit_modality, explicit_seniority, plain_text, public_https_url, utc_timestamp


_BOARD = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z")
_SOURCES = {"greenhouse", "lever", "ashby"}


def build_feed_url(source: str, board: str) -> str:
    if source not in _SOURCES or not _BOARD.fullmatch(board):
        raise ValueError("unsupported source or board")
    if source == "greenhouse":
        return f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
    if source == "lever":
        return f"https://api.lever.co/v0/postings/{board}?mode=json"
    return f"https://api.ashbyhq.com/posting-api/job-board/{board}?includeCompensation=true"


def _required_url(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("job URL missing")
    return public_https_url(value)


def _salary_from_lever(raw: dict) -> Salary | None:
    value = raw.get("salaryRange")
    if not isinstance(value, dict) or not value.get("currency") or not value.get("interval"):
        return None
    return Salary(str(value["currency"]).upper(), str(value["interval"]).lower(), value.get("min"), value.get("max"))


def _salary_from_ashby(raw: dict) -> Salary | None:
    compensation = raw.get("compensation") or {}
    components = compensation.get("summaryComponents") or []
    salaries = [item for item in components if item.get("compensationType") == "Salary"]
    if len(salaries) != 1:
        return None
    value = salaries[0]
    if not value.get("currencyCode") or not value.get("interval"):
        return None
    return Salary(str(value["currencyCode"]).upper(), str(value["interval"]).lower(), value.get("minValue"), value.get("maxValue"))


def _job(source: str, board: str, company: str, external_id: str, title: str,
         description: str, location: str | None, modality: str, salary: Salary | None,
         source_url: str, apply_url: str, published_at: object, updated_at: object,
         retrieved_at: str, seniority: str | None = None) -> Job:
    if not external_id or not title.strip() or not company.strip():
        raise ValueError("required job field missing")
    return Job(
        job_id=f"{source}:{board}:{external_id}", source=source, board=board,
        external_id=external_id, company=company, title=title.strip(),
        description=description, location=location, modality=modality,
        mexico_eligibility="unknown", seniority=seniority, salary=salary,
        source_url=_required_url(source_url), apply_url=_required_url(apply_url),
        published_at=utc_timestamp(published_at), updated_at=utc_timestamp(updated_at),
        status="open", feed_url=build_feed_url(source, board),
        retrieved_at=utc_timestamp(retrieved_at) or "",
    )


def parse_feed(source: str, board: str, company: str, payload: object, retrieved_at: str) -> list[Job]:
    build_feed_url(source, board)
    if source == "lever":
        entries = payload
    else:
        entries = payload.get("jobs") if isinstance(payload, dict) else None
    if not isinstance(entries, list):
        raise ValueError("invalid ATS feed")

    jobs: list[Job] = []
    for raw in entries:
        if not isinstance(raw, dict):
            raise ValueError("invalid ATS job")
        if source == "greenhouse":
            if raw.get("internal_job_id") is None:
                continue
            url = raw.get("absolute_url")
            jobs.append(_job(source, board, company, str(raw.get("id") or ""),
                             str(raw.get("title") or ""), plain_text(raw.get("content")),
                             (raw.get("location") or {}).get("name"), "unknown", None,
                             url, url, None, raw.get("updated_at"), retrieved_at,
                             explicit_seniority(str(raw.get("title") or ""))))
        elif source == "lever":
            categories = raw.get("categories") or {}
            jobs.append(_job(source, board, company, str(raw.get("id") or ""),
                             str(raw.get("text") or ""),
                             plain_text(raw.get("descriptionPlain") or raw.get("description")),
                             categories.get("location"), explicit_modality(raw.get("workplaceType")),
                             _salary_from_lever(raw), raw.get("hostedUrl"), raw.get("applyUrl"),
                             raw.get("createdAt"), raw.get("updatedAt"), retrieved_at,
                             explicit_seniority(str(raw.get("text") or ""), categories.get("level"))))
        else:
            if raw.get("isListed") is False:
                continue
            url = _required_url(raw.get("jobUrl"))
            parts = urlsplit(url)
            path = parts.path.strip("/").split("/")
            if parts.hostname != "jobs.ashbyhq.com" or len(path) < 2 or path[0].lower() != board.lower():
                raise ValueError("Ashby job URL does not match board")
            jobs.append(_job(source, board, company, path[1], str(raw.get("title") or ""),
                             plain_text(raw.get("descriptionPlain") or raw.get("descriptionHtml")),
                             raw.get("location"), explicit_modality(raw.get("workplaceType")),
                             _salary_from_ashby(raw), url, raw.get("applyUrl"),
                             raw.get("publishedAt"), None, retrieved_at,
                             explicit_seniority(str(raw.get("title") or ""))))
    return jobs
