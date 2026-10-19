import sys
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aji.daily_preparation import prepare_daily_batch
from tests.test_application_package import inputs


class FakeStore:
    candidate_id = "fictional"

    def __init__(self, jobs, matches):
        self.jobs = jobs
        self.matches = matches

    def load(self, now):
        return ({"candidate_id": "fictional", "batch_id": "fictional:2026-10-13",
                 "status": "READY", "job_ids": [job["job_id"] for job in self.jobs]},
                self.jobs, self.matches)

    def acquire_lock(self, manifest, now):
        raise AssertionError("preparation must not consume the daily lock")


class DailyPreparationTests(unittest.TestCase):
    def test_prepares_only_shortlist_above_threshold_and_respects_daily_cap(self):
        job, match, profile = inputs()
        second_job = replace(job, job_id=job.job_id + "-2")
        second_match = replace(match, job_id=second_job.job_id)
        store = FakeStore([job.to_dict(), second_job.to_dict()],
                          [asdict(match), asdict(second_match)])
        with tempfile.TemporaryDirectory() as directory:
            result = prepare_daily_batch(store, "2026-10-13T15:00:00Z", profile,
                                         Path(directory), max_preparations=1,
                                         prepare_threshold=match.score)
            self.assertEqual(result["prepared"], 1)
            self.assertEqual(result["existing"], 0)
            self.assertEqual(len(list(Path(directory).rglob("resume-tailored.pdf"))), 1)
            repeated = prepare_daily_batch(store, "2026-10-13T15:00:00Z", profile,
                                           Path(directory), max_preparations=1,
                                           prepare_threshold=match.score)
            self.assertEqual(repeated["prepared"], 0)
            self.assertEqual(repeated["existing"], 1)

    def test_unapproved_profile_or_review_does_not_generate(self):
        job, match, profile = inputs()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = FakeStore([job.to_dict()], [asdict(match)])
            profile["approved_by_holder"] = False
            with self.assertRaises(ValueError):
                prepare_daily_batch(store, "2026-10-13T15:00:00Z", profile, root,
                                    max_preparations=3, prepare_threshold=70)
            profile["approved_by_holder"] = True
            store.matches[0]["decision"] = "review"
            result = prepare_daily_batch(store, "2026-10-13T15:00:00Z", profile, root,
                                         max_preparations=3, prepare_threshold=70)
            self.assertEqual(result["prepared"], 0)
            self.assertEqual(list(root.rglob("resume-tailored.pdf")), [])


if __name__ == "__main__":
    unittest.main()
