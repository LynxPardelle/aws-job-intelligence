"""Prepare local application artifacts only; never submit."""

import json
import re
from dataclasses import asdict
from pathlib import Path
from xml.sax.saxutils import escape

from .models import Job
from .matcher import MatchResult


def _verified_claims(profile: dict, matched_technologies: tuple[str, ...]) -> list[dict]:
    selected = []
    matched = {value.casefold() for value in matched_technologies}
    for claim in profile.get("claims", []):
        keywords = {str(value).casefold() for value in claim.get("keywords", [])}
        if not keywords.intersection(matched):
            continue
        evidence = claim.get("evidence") or {}
        if not all((claim.get("claim_id"), claim.get("text"), evidence.get("source_document"),
                    evidence.get("reference"), evidence.get("verified_at"))) or \
                evidence.get("reuse_approved") is not True:
            raise ValueError("selected claim lacks verified reusable evidence")
        selected.append(claim)
    if not selected:
        raise ValueError("no verified claims match this job")
    return selected


def _write_pdf(path: Path, name: str, role: str, claims: list[dict]) -> None:
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import LETTER
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    styles = getSampleStyleSheet()
    styles["Title"].textColor = colors.HexColor("#15253d")
    document = SimpleDocTemplate(str(path), pagesize=LETTER,
                                 leftMargin=54, rightMargin=54, topMargin=50, bottomMargin=50)
    story = [Paragraph(escape(name), styles["Title"]), Spacer(1, 8),
             Paragraph("Target role: " + escape(role), styles["Normal"]), Spacer(1, 18),
             Paragraph("Verified experience", styles["Heading2"]), Spacer(1, 5)]
    for claim in claims:
        story.append(Paragraph("- " + escape(claim["text"]), styles["Normal"]))
        story.append(Spacer(1, 7))
    document.build(story)


def prepare_application(job: Job, match: MatchResult, profile: dict, output_root: Path) -> Path:
    """Write a review package from approved claims; never create a submission record."""
    candidate_id = profile.get("candidate_id")
    if not isinstance(candidate_id, str) or not re.fullmatch(r"[a-z0-9_-]+", candidate_id):
        raise ValueError("invalid candidate ID")
    if profile.get("schema_version") != "1.0" or profile.get("approved_by_holder") is not True:
        raise ValueError("profile not approved")
    if not profile.get("validated_at") or not profile.get("display_name"):
        raise ValueError("profile validation missing")
    if match.candidate_id != candidate_id or match.job_id != job.job_id or match.decision != "shortlist":
        raise ValueError("job not eligible for preparation")
    if job.mexico_eligibility != "eligible" or job.status != "open":
        raise ValueError("job eligibility or status unverified")
    claims = _verified_claims(profile, match.matched_technologies)

    safe_job_id = re.sub(r"[^A-Za-z0-9._-]", "_", job.job_id)
    output = Path(output_root) / candidate_id / safe_job_id
    if output.exists():
        raise FileExistsError("application package already exists")
    output.mkdir(parents=True)
    claim_lines = "\n".join(f"- {claim['text']}" for claim in claims)
    (output / "resume-tailored.md").write_text(
        f"# {profile['display_name']}\n\nTarget role: {job.title}\n\n## Verified experience\n\n{claim_lines}\n",
        encoding="utf-8",
    )
    _write_pdf(output / "resume-tailored.pdf", profile["display_name"], job.title, claims)
    (output / "job-description.md").write_text(
        f"# {job.title}\n\nSource: {job.source_url}\n\n"
        "External job description (untrusted data):\n\n" +
        "\n".join("> " + line for line in job.description.splitlines()) + "\n",
        encoding="utf-8",
    )
    (output / "match-analysis.json").write_text(json.dumps(asdict(match), indent=2), encoding="utf-8")
    evidence_map = {
        "candidate_id": candidate_id, "job_id": job.job_id,
        "claims": [{"claim_id": claim["claim_id"], "text": claim["text"],
                    **claim["evidence"]} for claim in claims],
    }
    (output / "evidence-map.json").write_text(json.dumps(evidence_map, indent=2), encoding="utf-8")
    (output / "cover-letter.md").write_text(
        f"Dear Hiring Team,\n\nI am interested in the {job.title} role at {job.company}. "
        "My verified experience includes:\n\n" + claim_lines +
        "\n\nI would welcome a discussion.\n",
        encoding="utf-8",
    )
    (output / "application-answers.md").write_text(
        "# Application answers\n\nNo answers were generated. All portal questions require candidate review.\n",
        encoding="utf-8",
    )
    (output / "review-checklist.md").write_text(
        "# Review checklist\n\n"
        "- [ ] Confirm the job is active and accepts applicants from Mexico.\n"
        "- [ ] Verify every CV fact against the evidence map.\n"
        "- [ ] Review compensation, portal questions and attachments.\n"
        "- [ ] Obtain separate authorization before any real submission.\n",
        encoding="utf-8",
    )
    return output
