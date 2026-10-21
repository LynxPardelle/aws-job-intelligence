"""Read the approved project budget without changing AWS."""

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aji.budget_status import summarize_budget  # noqa: E402


def main() -> int:
    try:
        config = json.loads((ROOT / "private" / "local-aws.json").read_text("utf-8"))
        if config.get("profile") != "default" or config.get("region") != "us-east-1":
            raise ValueError("unexpected local AWS configuration")

        import boto3
        from botocore.config import Config

        session = boto3.Session(profile_name=config["profile"], region_name=config["region"])
        limits = Config(connect_timeout=5, read_timeout=10,
                        retries={"max_attempts": 2, "mode": "standard"})
        identity = session.client("sts", config=limits).get_caller_identity()
        if identity["Account"] != config["account_id"] or \
                identity["Arn"] != config["principal_arn"]:
            raise ValueError("unexpected local AWS identity")
        client = session.client("budgets", config=limits)
        request = {"AccountId": config["account_id"], "BudgetName": "aji-project-dev"}
        budget = client.describe_budget(**request)["Budget"]
        notifications = client.describe_notifications_for_budget(**request)["Notifications"]
        summary = summarize_budget(budget, notifications)
    except Exception:
        print(json.dumps({"status": "ERROR", "error_code": "BUDGET_READ_FAILED"}))
        return 2
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
