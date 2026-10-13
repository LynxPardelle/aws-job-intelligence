import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aji.application_package import prepare_application
from aji.batch import BatchLock, build_manifest, validate_batch
from aji.connectors import parse_feed
from aji.matcher import SearchPolicy, match_job


class EndToEndTests(unittest.TestCase):
    def test_fictional_batch_creates_review_package_without_submission(self):
        root = Path(__file__).parent / "fixtures"
        feed = json.loads((root / "ashby.json").read_text("utf-8"))
        profile = json.loads((root / "verified_profile.json").read_text("utf-8"))
        job = parse_feed("ashby", "acmeexample", "Acme Example", feed, "2026-10-13T14:00:00Z")[0]
        job = replace(job, mexico_eligibility="eligible")  # Only fixture simulates verification.
        batch = build_manifest("fictional", "batch-demo", [job.to_dict()],
                               "2026-10-13T14:00:00Z", "2026-10-13T18:00:00Z")
        validate_batch(batch, [job.to_dict()], "fictional", "2026-10-13T15:00:00Z")
        locks = BatchLock()
        self.assertTrue(locks.try_acquire("fictional", batch["batch_id"]))
        policy = SearchPolicy("fictional", ("python", "data"), ("senior",), ("remote",), 75000, "USD", 70)
        match = match_job(job, policy, "2026-10-13T15:00:00Z")
        self.assertEqual(match.decision, "shortlist")

        with tempfile.TemporaryDirectory() as directory:
            output = prepare_application(job, match, profile, Path(directory))
            self.assertTrue((output / "resume-tailored.pdf").exists())
            self.assertTrue((output / "review-checklist.md").exists())
            self.assertFalse((output / "submission-record.json").exists())
        self.assertFalse(locks.try_acquire("fictional", batch["batch_id"]))


if __name__ == "__main__":
    unittest.main()
