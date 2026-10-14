"""Inspect Alec's current private batch. --claim also writes its daily lock.

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


def read_batch_summary(store: CandidateBatchStore, now: str, claim: bool) -> tuple[dict, int]:
    try:
        return inspect_daily_batch(store, now, acquire_lock=claim), 0
    except Exception as exc:
        code = getattr(exc, "response", {}).get("Error", {}).get("Code")
        if code in {"AccessDenied", "NoSuchKey", "404"}:
            error_code = "BATCH_UNAVAILABLE_OR_DENIED"
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
    args = parser.parse_args()

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
