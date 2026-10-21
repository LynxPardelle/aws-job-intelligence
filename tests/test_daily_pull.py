import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aji.daily_pull import inspect_daily_batch


class FakeStore:
    candidate_id = "alec"

    def __init__(self, lock_available=True):
        self.lock_available = lock_available
        self.lock_calls = 0

    def load(self, now):
        return (
            {"batch_id": "alec:2026-10-13", "candidate_id": "alec", "status": "READY",
             "generated_at": "2026-10-13T14:30:00Z", "job_ids": ["job-1", "job-2"]},
            [{"job_id": "job-1", "title": "Data Engineer", "company": "Example",
              "source_url": "https://example.invalid/1",
              "apply_url": "https://jobs.example.invalid/apply/1"},
             {"job_id": "job-2", "title": "Developer", "company": "Example",
              "source_url": "https://example.invalid/2",
              "apply_url": "https://jobs.example.invalid/apply/2"}],
            [{"job_id": "job-1", "candidate_id": "alec", "decision": "shortlist", "score": 90},
             {"job_id": "job-2", "candidate_id": "alec", "decision": "review", "score": 55}],
        )

    def acquire_lock(self, manifest, now):
        self.lock_calls += 1
        return self.lock_available


class DailyPullTests(unittest.TestCase):
    def test_preview_reads_batch_without_claiming_it(self):
        store = FakeStore()
        summary = inspect_daily_batch(store, "2026-10-13T15:00:00Z")
        self.assertEqual(summary["status"], "READY")
        self.assertEqual(summary["jobs_found"], 2)
        self.assertEqual(summary["shortlisted"], 1)
        self.assertEqual(summary["needs_review"], 1)
        self.assertEqual(summary["confirmed_applications"], 0)
        self.assertEqual(summary["generated_at"], "2026-10-13T14:30:00Z")
        self.assertEqual(summary["opportunities"][0]["apply_url"],
                         "https://jobs.example.invalid/apply/1")
        self.assertEqual(store.lock_calls, 0)

    def test_run_claims_lock_and_reports_already_processed(self):
        store = FakeStore(lock_available=False)
        summary = inspect_daily_batch(store, "2026-10-13T15:00:00Z", acquire_lock=True)
        self.assertEqual(summary["status"], "ALREADY_PROCESSED")
        self.assertEqual(store.lock_calls, 1)

    def test_preview_exposes_public_salary_basis_and_review_gaps(self):
        store = FakeStore()
        load = store.load

        def with_salary(now):
            manifest, jobs, matches = load(now)
            jobs[0]["salary"] = {"currency": "USD", "interval": "month",
                                  "minimum": 5000, "maximum": 9500, "basis": "gross"}
            matches[0]["unknowns"] = ["net_salary_unverified"]
            matches[0]["reasons"] = ["salary_range_overlaps_minimum"]
            return manifest, jobs, matches

        store.load = with_salary
        summary = inspect_daily_batch(store, "2026-10-13T15:00:00Z")

        self.assertEqual(summary["opportunities"][0]["salary"],
                         {"currency": "USD", "interval": "month",
                          "minimum": 5000, "maximum": 9500, "basis": "gross"})
        self.assertEqual(summary["opportunities"][0]["unknowns"], ["net_salary_unverified"])
        self.assertEqual(summary["opportunities"][0]["reasons"],
                         ["salary_range_overlaps_minimum"])

    def test_invalid_decision_fails_before_lock(self):
        store = FakeStore()
        load = store.load

        def invalid(now):
            manifest, jobs, matches = load(now)
            matches[0]["decision"] = "submitted"
            return manifest, jobs, matches

        store.load = invalid
        with self.assertRaises(ValueError):
            inspect_daily_batch(store, "2026-10-13T15:00:00Z", acquire_lock=True)
        self.assertEqual(store.lock_calls, 0)


if __name__ == "__main__":
    unittest.main()
