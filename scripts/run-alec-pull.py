"""Inspect Alec's current private batch; optionally prepare approved local CVs.

Run only after the approved Alec stack exists and private/local-aws.json contains
alec_role_arn and alec_bucket from that stack's CloudFormation outputs.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aji.aws_batch_io import CandidateBatchStore  # noqa: E402
from aji.daily_pull import inspect_daily_batch  # noqa: E402
from aji.daily_preparation import prepare_daily_batch  # noqa: E402


MAX_PREPARATIONS_PER_DAY = 3


def load_preparation_inputs(root: Path) -> tuple[dict, int]:
    """Require an explicitly approved Alec profile before attempting AWS preparation."""
    try:
        folder = root / "private" / "alec"
        profile = json.loads((folder / "verified-profile.json").read_text(encoding="utf-8"))
        policy = json.loads((folder / "search-policy.active.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError("approved Alec profile and policy required") from exc
    threshold = policy.get("prepare_threshold")
    if profile.get("schema_version") != "1.0" or profile.get("candidate_id") != "alec" or \
            profile.get("approved_by_holder") is not True or \
            not profile.get("validated_at") or not profile.get("display_name") or \
            not isinstance(profile.get("claims"), list) or not profile["claims"] or \
            any(not isinstance(claim, dict) or not claim.get("claim_id") or
                not claim.get("text") or not isinstance(claim.get("keywords"), list) or
                not isinstance(claim.get("evidence"), dict) or
                not all(claim["evidence"].get(key) for key in
                        ("source_document", "reference", "verified_at")) or
                claim["evidence"].get("reuse_approved") is not True
                for claim in profile["claims"]) or \
            policy.get("candidate_id") != "alec" or policy.get("application_mode") != "PREPARE" or \
            type(threshold) is not int or not 0 <= threshold <= 100:
        raise ValueError("approved Alec profile and policy required")
    return profile, threshold


def read_batch_summary(store: CandidateBatchStore, now: str, claim: bool) -> tuple[dict, int]:
    try:
        return inspect_daily_batch(store, now, acquire_lock=claim), 0
    except Exception as exc:
        code = getattr(exc, "response", {}).get("Error", {}).get("Code")
        if code in {"AccessDenied", "NoSuchKey", "404"}:
            error_code = "BATCH_UNAVAILABLE_OR_DENIED"
        elif isinstance(code, str) and code:
            error_code = "BATCH_AWS_ERROR"
        elif isinstance(exc, ValueError):
            error_code = "BATCH_INVALID_OR_STALE"
        else:
            raise
        return {
            "status": "ERROR", "candidate_id": "alec", "error_code": error_code,
            "jobs_found": 0, "shortlisted": 0, "needs_review": 0,
            "cvs_prepared": 0, "confirmed_applications": 0, "opportunities": [],
        }, 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Read today's Alec batch using an assumed role")
    parser.add_argument("--claim", action="store_true", help="Acquire the daily DynamoDB lock")
    parser.add_argument("--prepare", action="store_true",
                        help="Prepare at most three local CV packages from approved profile and shortlist")
    args = parser.parse_args()
    if args.claim and args.prepare:
        parser.error("--prepare cannot be combined with --claim")

    preparation_profile = None
    preparation_threshold = None
    if args.prepare:
        try:
            preparation_profile, preparation_threshold = load_preparation_inputs(ROOT)
        except ValueError:
            print(json.dumps({"status": "ERROR", "candidate_id": "alec",
                              "error_code": "PROFILE_NOT_APPROVED", "prepared": 0,
                              "confirmed_applications": 0}))
            return 2

    config_path = ROOT / "private" / "local-aws.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    account = config["account_id"]
    region = config["region"]
    role_arn = config["alec_role_arn"]
    if role_arn != f"arn:aws:iam::{account}:role/aji-alec-access-dev":
        raise ValueError("Alec role does not match the authorized account")
    bucket = config["alec_bucket"]
    if not isinstance(bucket, str) or not bucket:
        raise ValueError("Alec bucket is missing")

    import boto3
    from botocore.config import Config

    limits = Config(connect_timeout=5, read_timeout=10,
                    retries={"max_attempts": 2, "mode": "standard"})
    admin = boto3.Session(profile_name=config["profile"], region_name=region)
    sts = admin.client("sts", config=limits)
    identity = sts.get_caller_identity()
    if identity["Account"] != account or identity["Arn"] != config["principal_arn"]:
        raise ValueError("AWS identity differs from the authorized first PC")
    assumed = sts.assume_role(RoleArn=role_arn, RoleSessionName="aji-alec-daily")
    temporary = assumed["Credentials"]
    candidate = boto3.Session(
        aws_access_key_id=temporary["AccessKeyId"],
        aws_secret_access_key=temporary["SecretAccessKey"],
        aws_session_token=temporary["SessionToken"], region_name=region,
    )
    candidate_identity = candidate.client("sts", config=limits).get_caller_identity()
    expected_prefix = f"arn:aws:sts::{account}:assumed-role/aji-alec-access-dev/"
    if candidate_identity["Account"] != account or not candidate_identity["Arn"].startswith(expected_prefix):
        raise ValueError("assumed session is not Alec's restricted role")

    store = CandidateBatchStore(
        "alec", bucket, candidate.client("s3", config=limits),
        candidate.resource("dynamodb", config=limits).Table("aji-alec-state-dev"),
    )
    if args.prepare:
        try:
            summary = prepare_daily_batch(
                store, datetime.now(timezone.utc).isoformat(), preparation_profile,
                ROOT / "applications", max_preparations=MAX_PREPARATIONS_PER_DAY,
                prepare_threshold=preparation_threshold,
            )
        except Exception as exc:
            code = getattr(exc, "response", {}).get("Error", {}).get("Code")
            if code in {"AccessDenied", "NoSuchKey", "404"}:
                error_code = "BATCH_UNAVAILABLE_OR_DENIED"
            elif isinstance(code, str) and code:
                error_code = "BATCH_AWS_ERROR"
            elif isinstance(exc, ValueError):
                error_code = "BATCH_INVALID_OR_PREPARATION_BLOCKED"
            elif isinstance(exc, OSError):
                error_code = "PREPARATION_IO_ERROR"
            else:
                raise
            print(json.dumps({"status": "ERROR", "candidate_id": "alec",
                              "error_code": error_code, "prepared": 0,
                              "confirmed_applications": 0}))
            return 2
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    summary, exit_code = read_batch_summary(
        store, datetime.now(timezone.utc).isoformat(), args.claim,
    )
    if args.claim and summary["status"] == "READY":
        destination = ROOT / "applications" / "alec" / "daily-summary.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = destination.with_suffix(".tmp")
        temporary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary_path.replace(destination)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
