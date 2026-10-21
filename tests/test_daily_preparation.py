import sys
import tempfile
import unittest
import sqlite3
from contextlib import closing
from dataclasses import asdict, replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aji.daily_preparation import prepare_daily_batch
from aji.liveness import LivenessResult
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
            self.assertEqual(result["completed_items"][0]["job_id"], job.job_id)
            self.assertEqual(result["completed_items"][0]["apply_url"], job.apply_url)
            self.assertEqual(len(list(Path(directory).rglob("resume-tailored.pdf"))), 1)
            repeated = prepare_daily_batch(store, "2026-10-13T15:00:00Z", profile,
                                           Path(directory), max_preparations=1,
                                           prepare_threshold=match.score)
            self.assertEqual(repeated["prepared"], 0)
            self.assertEqual(repeated["existing"], 1)
            self.assertEqual(len(repeated["completed_items"]), 1)

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

    def test_preparation_limit_persists_across_runs_for_same_day(self):
        job, match, profile = inputs()
        later_job = replace(job, job_id=job.job_id + "-later")
        later_match = replace(match, job_id=later_job.job_id)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = prepare_daily_batch(FakeStore([job.to_dict()], [asdict(match)]),
                                        "2026-10-13T15:00:00Z", profile, root,
                                        max_preparations=1, prepare_threshold=match.score)
            second = prepare_daily_batch(FakeStore([later_job.to_dict()], [asdict(later_match)]),
                                         "2026-10-13T16:00:00Z", profile, root,
                                         max_preparations=1, prepare_threshold=match.score)

            self.assertEqual(first["prepared"], 1)
            self.assertEqual(second["prepared"], 0)
            self.assertEqual(len(list(root.rglob("resume-tailored.pdf"))), 1)

    def test_completed_package_recovers_if_process_stopped_before_ledger_update(self):
        job, match, profile = inputs()
        store = FakeStore([job.to_dict()], [asdict(match)])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prepare_daily_batch(store, "2026-10-13T15:00:00Z", profile, root,
                                max_preparations=1, prepare_threshold=match.score)
            ledger = root / "fictional" / ".preparation-ledger.sqlite3"
            with closing(sqlite3.connect(ledger)) as connection:
                with connection:
                    connection.execute("UPDATE preparations SET status='reserved'")

            result = prepare_daily_batch(store, "2026-10-13T15:01:00Z", profile, root,
                                         max_preparations=1, prepare_threshold=match.score)

            self.assertEqual(result["existing"], 1)
            self.assertEqual(result["in_progress"], 0)

    def test_missing_package_file_is_not_reported_as_prepared(self):
        job, match, profile = inputs()
        store = FakeStore([job.to_dict()], [asdict(match)])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prepare_daily_batch(store, "2026-10-13T15:00:00Z", profile, root,
                                max_preparations=1, prepare_threshold=match.score)
            next(root.rglob("resume-tailored.pdf")).unlink()

            result = prepare_daily_batch(store, "2026-10-13T15:01:00Z", profile, root,
                                         max_preparations=1, prepare_threshold=match.score)

            self.assertEqual(result["prepared"], 0)
            self.assertEqual(result["existing"], 0)
            self.assertEqual(result["blocked"], 1)
            self.assertEqual(result["completed_items"], [])
            self.assertEqual(result["blocked_job_ids"], [job.job_id])

    def test_unavailable_ledger_fails_as_safe_local_io_error(self):
        job, match, profile = inputs()
        with tempfile.TemporaryDirectory() as directory:
            ledger_path = Path(directory) / "fictional" / ".preparation-ledger.sqlite3"
            ledger_path.mkdir(parents=True)

            with self.assertRaises(OSError):
                prepare_daily_batch(FakeStore([job.to_dict()], [asdict(match)]),
                                    "2026-10-13T15:00:00Z", profile, Path(directory),
                                    max_preparations=1, prepare_threshold=match.score)

    def test_unknown_liveness_blocks_preparation_without_using_daily_quota(self):
        job, match, profile = inputs()
        store = FakeStore([job.to_dict()], [asdict(match)])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            blocked = prepare_daily_batch(
                store, "2026-10-13T15:00:00Z", profile, root,
                max_preparations=1, prepare_threshold=match.score,
                liveness_checker=lambda *_: LivenessResult(
                    "unknown", "official_feed_unavailable", "2026-10-13T15:00:00Z"))
            self.assertEqual(blocked["prepared"], 0)
            self.assertEqual(blocked["blocked"], 1)
            self.assertEqual(list(root.rglob("resume-tailored.pdf")), [])
            active = prepare_daily_batch(
                store, "2026-10-13T15:01:00Z", profile, root,
                max_preparations=1, prepare_threshold=match.score,
                liveness_checker=lambda *_: LivenessResult(
                    "active", "present_in_official_feed", "2026-10-13T15:01:00Z"))
            self.assertEqual(active["prepared"], 1)


if __name__ == "__main__":
    unittest.main()
