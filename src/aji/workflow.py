"""Application state guards; this module never interacts with a portal."""

import hashlib

from .dedupe import canonical_url
from .normalizer import utc_timestamp


_NEXT = {
    "DISCOVERED": {"ELIGIBLE"},
    "ELIGIBLE": {"SHORTLISTED"},
    "SHORTLISTED": {"APPROVED", "REJECTED"},
    "APPROVED": {"PREPARED"},
    "PREPARED": {"REVIEWED"},
    "REVIEWED": {"SUBMISSION_AUTHORIZED"},
    "SUBMISSION_AUTHORIZED": {"SUBMITTED"},
    "SUBMITTED": {"CONFIRMED", "REJECTED"},
    "CONFIRMED": {"INTERVIEW", "OFFER", "REJECTED"},
    "INTERVIEW": {"OFFER", "REJECTED"},
    "OFFER": {"HIRED", "REJECTED"},
    "HIRED": set(),
    "REJECTED": set(),
    "BLOCKED": set(),
    "FAILED": set(),
    "WITHDRAWN": set(),
}


def transition(current: str, target: str, *, proof: dict | None = None,
               candidate_id: str | None = None, job_id: str | None = None,
               portal: str | None = None) -> str:
    allowed = _NEXT.get(current)
    if allowed is None or (target not in allowed and not (
        target in {"BLOCKED", "FAILED", "WITHDRAWN"} and current not in {"CONFIRMED", "REJECTED"}
    )):
        raise ValueError("invalid application transition")
    evidence = proof or {}
    if target in {"SUBMISSION_AUTHORIZED", "SUBMITTED"}:
        if not all((candidate_id, job_id, portal, evidence.get("consent_id"))):
            raise ValueError("specific consent required")
        if evidence.get("revoked") is not False or any(
            evidence.get(key) != value for key, value in (
                ("candidate_id", candidate_id), ("job_id", job_id), ("portal", portal)
            )
        ):
            raise ValueError("consent does not match candidate, job and portal")
    if target == "SUBMITTED":
        if not evidence.get("technical_receipt") or not utc_timestamp(evidence.get("submitted_at")):
            raise ValueError("technical submission evidence required")
    elif target == "CONFIRMED":
        if not evidence.get("acknowledgment"):
            raise ValueError("acknowledgment required")
    elif target in {"INTERVIEW", "OFFER", "HIRED"} or \
            (target == "REJECTED" and current in {"SUBMITTED", "CONFIRMED", "INTERVIEW", "OFFER"}):
        if not evidence.get("evidence_ref"):
            raise ValueError("outcome evidence required")
    return target


def application_key(candidate_id: str, job_id: str, portal_url: str) -> str:
    if not candidate_id or not job_id:
        raise ValueError("candidate and job required")
    identity = f"{candidate_id}\n{job_id}\n{canonical_url(portal_url)}".encode("utf-8")
    return hashlib.sha256(identity).hexdigest()
