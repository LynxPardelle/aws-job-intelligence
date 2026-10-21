"""Extract quoted JD requirements and related approved claims, without inference."""

import re

from .normalizer import plain_text


_REQUIRED = re.compile(r"\b(required|must have|must possess|experience with|proficient in|you have)\b",
                       re.IGNORECASE)
_PREFERRED = re.compile(r"\b(nice to have|preferred|bonus)\b", re.IGNORECASE)


def _contains(text: str, term: str) -> bool:
    return bool(re.search(r"(?<!\w)" + re.escape(term.casefold()) + r"(?!\w)", text.casefold()))


def requirement_evidence_matrix(description: str, claims: list[dict]) -> list[dict]:
    if not isinstance(description, str) or not isinstance(claims, list):
        raise ValueError("invalid requirement inputs")
    sentences = re.split(r"(?<=[.!?])\s+", plain_text(description))
    matrix = []
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if _REQUIRED.search(sentence):
            priority = "required"
        elif _PREFERRED.search(sentence):
            priority = "preferred"
        else:
            continue
        related = []
        for claim in claims:
            if not isinstance(claim, dict):
                continue
            evidence = claim.get("evidence")
            if not isinstance(evidence, dict) or evidence.get("reuse_approved") is not True or \
                    not all(evidence.get(key) for key in
                            ("source_document", "reference", "verified_at")) or \
                    not claim.get("claim_id") or not isinstance(claim.get("keywords"), list):
                continue
            if any(isinstance(term, str) and term and _contains(sentence, term)
                   for term in claim["keywords"]):
                related.append(claim["claim_id"])
        matrix.append({"priority": priority, "quote": sentence[:400],
                       "status": "related_evidence" if related else "unverified",
                       "claim_ids": related})
        if len(matrix) >= 12:
            break
    return matrix
