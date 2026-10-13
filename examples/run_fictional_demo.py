"""Offline, fictional batch-to-review demo. No AWS or portal calls."""

import json
import sys
from dataclasses import replace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aji.application_package import prepare_application  # noqa: E402
from aji.batch import BatchLock, build_manifest, validate_batch  # noqa: E402
from aji.connectors import parse_feed  # noqa: E402
from aji.matcher import SearchPolicy, match_job  # noqa: E402


def main(output_root: Path) -> Path:
    fixtures = ROOT / "tests" / "fixtures"
    feed = json.loads((fixtures / "ashby.json").read_text("utf-8"))
    profile = json.loads((fixtures / "verified_profile.json").read_text("utf-8"))
    job = parse_feed("ashby", "acmeexample", "Acme Example", feed, "2026-10-13T14:00:00Z")[0]
    job = replace(job, mexico_eligibility="eligible")  # Fictional manual verification in this demo only.

    manifest = build_manifest("fictional", "batch-demo", [job.to_dict()],
                              "2026-10-13T14:00:00Z", "2026-10-13T18:00:00Z")
    validate_batch(manifest, [job.to_dict()], "fictional", "2026-10-13T15:00:00Z")
    if not BatchLock().try_acquire("fictional", manifest["batch_id"]):
        raise RuntimeError("fictional batch already handled")

    policy = SearchPolicy("fictional", ("python", "data"), ("senior",), ("remote",), 75000, "USD", 70)
    match = match_job(job, policy, "2026-10-13T15:00:00Z")
    package = prepare_application(job, match, profile, output_root)
    (package / "daily-summary.md").write_text(
        "# Fictional offline demo — 2026-10-13\n\n"
        f"- Batch: {manifest['batch_id']} (READY, checksum verified)\n"
        "- Jobs found: 1\n- Shortlisted: 1\n- CVs prepared: 1\n"
        "- Confirmed applications: 0\n- Pending review: 1\n- Errors: 0\n"
        "- AWS cost from this local run: USD 0\n"
        "- Real eligibility and candidate consent: **not established by this fixture**\n",
        encoding="utf-8",
    )
    return package


if __name__ == "__main__":
    destination = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "applications"
    print(main(destination))
