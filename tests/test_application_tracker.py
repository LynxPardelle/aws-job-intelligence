import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aji.application_tracker import (ApplicationTracker, register_discovered_from_summary,
                                     register_prepared_from_summary)


NOW = "2026-10-20T15:00:00Z"
PORTAL = "https://jobs.example.com/apply/101"


class ApplicationTrackerTests(unittest.TestCase):
    def test_register_and_transitions_are_idempotent_and_candidate_scoped(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tracker.sqlite3"
            tracker = ApplicationTracker(path, "fictional")
            app_id = tracker.register("job-101", PORTAL, NOW)
            self.assertEqual(tracker.register("job-101", PORTAL + "?utm_source=x", NOW), app_id)
            self.assertEqual(tracker.status(app_id), "DISCOVERED")
            self.assertEqual(len(tracker.events(app_id)), 1)
            self.assertTrue(tracker.advance(app_id, "ELIGIBLE", NOW, actor="policy"))
            self.assertFalse(tracker.advance(app_id, "ELIGIBLE", NOW, actor="policy"))
            self.assertEqual(tracker.summary(), {"total": 1, "by_status": {"ELIGIBLE": 1}})
            other = ApplicationTracker(path, "other")
            with self.assertRaises(ValueError):
                other.status(app_id)

    def test_submission_record_needs_prior_states_consent_and_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            tracker = ApplicationTracker(Path(directory) / "tracker.sqlite3", "fictional")
            app_id = tracker.register("job-101", PORTAL, NOW)
            for target in ("ELIGIBLE", "SHORTLISTED", "APPROVED", "PREPARED", "REVIEWED"):
                tracker.advance(app_id, target, NOW, actor="policy")
            with self.assertRaises(ValueError):
                tracker.advance(app_id, "SUBMITTED", NOW)
            consent = {"candidate_id": "fictional", "job_id": "job-101", "portal": PORTAL,
                       "consent_id": "fixture-consent", "revoked": False}
            with self.assertRaises(ValueError):
                tracker.advance(app_id, "SUBMISSION_AUTHORIZED", NOW, proof=consent,
                                actor="policy")
            tracker.advance(app_id, "SUBMISSION_AUTHORIZED", NOW, proof=consent)
            with self.assertRaises(ValueError):
                tracker.advance(app_id, "SUBMITTED", NOW, proof=consent)
            tracker.advance(app_id, "SUBMITTED", NOW,
                            proof={**consent, "technical_receipt": "fixture-response",
                                   "submitted_at": NOW}, actor="portal_receipt")
            self.assertEqual(tracker.status(app_id), "SUBMITTED")
            self.assertNotIn("fixture-response", str(tracker.events(app_id)))
            tracker.advance(app_id, "CONFIRMED", NOW, proof={"acknowledgment": "fixture-ack"})
            tracker.advance(app_id, "INTERVIEW", NOW,
                            proof={"evidence_ref": "private:fixture-interview"})
            self.assertEqual(tracker.summary()["by_status"], {"INTERVIEW": 1})

    def test_valid_preview_registers_discoveries_without_advancing_to_submission(self):
        with tempfile.TemporaryDirectory() as directory:
            tracker = ApplicationTracker(Path(directory) / "tracker.sqlite3", "fictional")
            summary = {"status": "READY", "candidate_id": "fictional",
                       "generated_at": NOW, "opportunities": [{
                           "job_id": "job-101", "apply_url": PORTAL,
                       }]}
            self.assertEqual(register_discovered_from_summary(tracker, summary)["added"], 1)
            self.assertEqual(register_discovered_from_summary(tracker, summary)["added"], 0)
            self.assertEqual(tracker.summary()["by_status"], {"DISCOVERED": 1})
            self.assertEqual(register_discovered_from_summary(
                tracker, {"status": "ERROR", "opportunities": []})["added"], 0)

    def test_completed_local_package_advances_only_to_prepared(self):
        with tempfile.TemporaryDirectory() as directory:
            tracker = ApplicationTracker(Path(directory) / "tracker.sqlite3", "fictional")
            summary = {"status": "READY", "candidate_id": "fictional",
                       "batch_id": "fictional:2026-10-20", "completed_at": NOW,
                       "completed_items": [{"job_id": "job-101", "apply_url": PORTAL}]}
            self.assertEqual(register_prepared_from_summary(tracker, summary)["advanced"], 1)
            app_id = tracker.register("job-101", PORTAL, NOW)
            self.assertEqual(tracker.status(app_id), "PREPARED")
            self.assertEqual(register_prepared_from_summary(tracker, summary)["advanced"], 0)
            self.assertEqual(tracker.summary()["by_status"], {"PREPARED": 1})


if __name__ == "__main__":
    unittest.main()
