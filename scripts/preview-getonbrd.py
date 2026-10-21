"""Read three public Get on Board categories for Alec; local preview only."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aji.getonbrd_preview import build_getonbrd_preview  # noqa: E402
from aji.publisher_handler import _policy_from_dict  # noqa: E402
from aji.job_history import annotate_summary_history  # noqa: E402
from aji.application_tracker import ApplicationTracker, register_discovered_from_summary  # noqa: E402


def load_private_policy(root: Path):
    path = root / "private" / "alec" / "search-policy.active.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return _policy_from_dict(raw, "alec")


def main() -> int:
    try:
        policy, quota = load_private_policy(ROOT)
    except (OSError, ValueError):
        print(json.dumps({"status": "ERROR", "error_code": "POLICY_UNAVAILABLE",
                          "candidate_id": "alec", "opportunities": []}))
        return 2
    try:
        now = datetime.now(timezone.utc)
        summary = build_getonbrd_preview(policy, now.isoformat(),
                                          max_jobs=min(quota, 10))
    except Exception:
        print(json.dumps({"status": "ERROR", "error_code": "GETONBRD_UNAVAILABLE",
                          "candidate_id": "alec", "opportunities": []}))
        return 2
    if summary["status"] == "READY":
        try:
            summary = annotate_summary_history(
                summary, ROOT / "applications" / "alec" / ".job-history.sqlite3",
                "alec", now.astimezone(ZoneInfo("America/Mexico_City")).date().isoformat(),
            )
        except (OSError, ValueError):
            summary["history_status"] = "UNAVAILABLE"
        try:
            tracker = ApplicationTracker(ROOT / "applications" / "alec" / ".tracker.sqlite3",
                                         "alec")
            summary["tracker"] = register_discovered_from_summary(tracker, summary)
        except (OSError, ValueError, KeyError):
            summary["tracker_status"] = "UNAVAILABLE"
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
