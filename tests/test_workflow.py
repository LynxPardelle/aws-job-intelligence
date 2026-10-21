import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aji.workflow import application_key, transition


class WorkflowTests(unittest.TestCase):
    def test_prepare_path_cannot_skip_human_review(self):
        self.assertEqual(transition("DISCOVERED", "ELIGIBLE"), "ELIGIBLE")
        with self.assertRaises(ValueError):
            transition("SHORTLISTED", "PREPARED")
        self.assertEqual(transition("APPROVED", "PREPARED"), "PREPARED")
        self.assertEqual(transition("PREPARED", "REVIEWED"), "REVIEWED")

    def test_submission_requires_specific_authorization_and_receipt(self):
        authorization = {"candidate_id": "fictional", "job_id": "job-1", "portal": "jobs.example.com",
                         "consent_id": "consent-test", "revoked": False}

        with self.assertRaises(ValueError):
            transition("REVIEWED", "SUBMISSION_AUTHORIZED")
        self.assertEqual(transition("REVIEWED", "SUBMISSION_AUTHORIZED", proof=authorization,
                                    candidate_id="fictional", job_id="job-1", portal="jobs.example.com"),
                         "SUBMISSION_AUTHORIZED")
        with self.assertRaises(ValueError):
            transition("SUBMISSION_AUTHORIZED", "SUBMITTED")
        self.assertEqual(transition("SUBMISSION_AUTHORIZED", "SUBMITTED",
                                    proof={**authorization, "technical_receipt": "test-response",
                                           "submitted_at": "2026-10-13T15:00:00Z"},
                                    candidate_id="fictional", job_id="job-1", portal="jobs.example.com"),
                         "SUBMITTED")
        with self.assertRaises(ValueError):
            transition("SUBMITTED", "CONFIRMED")
        self.assertEqual(transition("SUBMITTED", "CONFIRMED", proof={"acknowledgment": "test-ack"}),
                         "CONFIRMED")

    def test_revoked_or_wrong_candidate_authorization_is_rejected(self):
        proof = {"candidate_id": "other", "job_id": "job-1", "portal": "jobs.example.com",
                 "consent_id": "consent-test", "revoked": False}

        with self.assertRaises(ValueError):
            transition("REVIEWED", "SUBMISSION_AUTHORIZED", proof=proof,
                       candidate_id="fictional", job_id="job-1", portal="jobs.example.com")
        with self.assertRaises(ValueError):
            transition("SUBMISSION_AUTHORIZED", "SUBMITTED",
                       proof={**proof, "technical_receipt": "test-response",
                              "submitted_at": "2026-10-13T15:00:00Z"},
                       candidate_id="fictional", job_id="job-1", portal="jobs.example.com")
        proof["candidate_id"] = "fictional"
        proof["revoked"] = True
        with self.assertRaises(ValueError):
            transition("REVIEWED", "SUBMISSION_AUTHORIZED", proof=proof,
                       candidate_id="fictional", job_id="job-1", portal="jobs.example.com")

    def test_application_key_is_candidate_job_portal_specific(self):
        self.assertNotEqual(application_key("alec", "job-1", "https://jobs.example.com/apply"),
                            application_key("hector", "job-1", "https://jobs.example.com/apply"))
        self.assertEqual(application_key("alec", "job-1", "https://jobs.example.com/apply?utm_source=x"),
                         application_key("alec", "job-1", "https://jobs.example.com/apply"))

    def test_confirmed_application_can_track_evidenced_interview_and_offer(self):
        with self.assertRaises(ValueError):
            transition("CONFIRMED", "INTERVIEW")
        self.assertEqual(transition("CONFIRMED", "INTERVIEW",
                                    proof={"evidence_ref": "private:calendar-event"}), "INTERVIEW")
        self.assertEqual(transition("INTERVIEW", "OFFER",
                                    proof={"evidence_ref": "private:offer-letter"}), "OFFER")
        self.assertEqual(transition("OFFER", "HIRED",
                                    proof={"evidence_ref": "private:signed-contract"}), "HIRED")
        self.assertEqual(transition("CONFIRMED", "REJECTED",
                                    proof={"evidence_ref": "private:employer-response"}), "REJECTED")
        with self.assertRaises(ValueError):
            transition("HIRED", "REJECTED")


if __name__ == "__main__":
    unittest.main()
