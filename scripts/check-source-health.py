"""Read the public Collector run marker with the authorized local AWS profile."""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aji.source_health import summarize_source_health  # noqa: E402


def main() -> int:
    try:
        config = json.loads((ROOT / "private" / "local-aws.json").read_text("utf-8"))
        if config.get("region") != "us-east-1" or config.get("profile") != "default":
            raise ValueError("unexpected local AWS configuration")
        import boto3
        session = boto3.Session(profile_name=config["profile"], region_name=config["region"])
        identity = session.client("sts").get_caller_identity()
        if identity["Account"] != config["account_id"] or \
                identity["Arn"] != config["principal_arn"]:
            raise ValueError("unexpected local AWS identity")
        table = session.resource("dynamodb").Table("aji-public-jobs-dev")
        day = datetime.now(ZoneInfo("America/Mexico_City")).date()

        def marker(for_day):
            return table.get_item(Key={"job_id": f"run#{for_day.isoformat()}"},
                                  ConsistentRead=True).get("Item")

        summary = summarize_source_health(marker(day), marker(day - timedelta(days=1)),
                                          day.isoformat())
    except Exception as exc:
        error_code = "COLLECTION_INCOMPLETE" if isinstance(exc, ValueError) else "AWS_READ_FAILED"
        print(json.dumps({"status": "ERROR", "error_code": error_code, "sources": []}))
        return 2
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
