import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aji.daily_orchestrator import StepResult, compact_report, run_daily, save_daily_report


NOW = "2026-10-20T15:00:00Z"
DAY = "2026-10-20"


def success_steps():
    return {
        "preflight": StepResult(0, None),
        "budget": StepResult(0, {"status": "BELOW_ALERT", "observed_usd": 0.001,
                                  "limit_usd": 5.0, "alert_thresholds_usd": [3.0, 5.0],
                                  "coverage": "tagged_project_only", "costs_may_lag": True}),
        "source_health": StepResult(0, {"status": "COMPLETE", "collection_day": DAY,
                                        "total_jobs": 35, "sources": []}),
        "batch_preview": StepResult(0, {"status": "READY", "candidate_id": "alec",
                                         "batch_id": f"alec:{DAY}", "jobs_found": 10,
                                         "shortlisted": 1, "needs_review": 9,
                                         "opportunities": [{"job_id": "fixture", "decision": "review"}],
                                         "tracker": {"total": 1,
                                                     "by_status": {"DISCOVERED": 1}}}),
        "getonbrd_preview": StepResult(0, {"status": "READY", "candidate_id": "alec",
                                             "jobs_fetched": 207, "unique_jobs": 207,
                                             "shortlisted": 0, "needs_review": 10,
                                             "possibly_truncated_categories": ["programming"],
                                             "opportunities": []}),
        "prepare": StepResult(0, {"status": "READY", "candidate_id": "alec",
                                  "batch_id": f"alec:{DAY}", "jobs_found": 10,
                                  "prepared": 1, "existing": 0, "blocked": 0,
                                  "completed_items": [{"job_id": "fixture"}],
                                  "tracker": {"total": 1,
                                              "by_status": {"PREPARED": 1}}}),
    }


class DailyOrchestratorTests(unittest.TestCase):
    def test_successful_run_prepares_only_after_valid_same_day_batch(self):
        steps = success_steps()
        called = []

        def runner(name):
            called.append(name)
            return steps[name]

        report = run_daily(NOW, runner)

        self.assertEqual(called, ["preflight", "budget", "source_health", "batch_preview",
                                  "getonbrd_preview", "prepare"])
        self.assertEqual(report["status"], "READY")
        self.assertEqual(report["batch_id"], f"alec:{DAY}")
        self.assertEqual(report["aws"]["jobs_found"], 10)
        self.assertEqual(report["preparation"]["prepared"], 1)
        self.assertEqual(report["confirmed_applications"], 0)
        self.assertEqual(report["getonbrd"]["jobs_fetched"], 207)
        self.assertEqual(report["budget"]["observed_usd"], 0.001)
        self.assertEqual(report["errors"], [])

    def test_invalid_or_stale_batch_never_triggers_preparation_or_reuses_old_data(self):
        steps = success_steps()
        steps["batch_preview"] = StepResult(0, {**steps["batch_preview"].payload,
                                                  "batch_id": "alec:2026-10-19"})
        called = []
        report = run_daily(NOW, lambda name: (called.append(name), steps[name])[1])

        self.assertEqual(report["status"], "ERROR")
        self.assertNotIn("prepare", called)
        self.assertIsNone(report["batch_id"])
        self.assertIsNone(report["aws"])
        self.assertEqual(report["errors"][0]["code"], "BATCH_INVALID_OR_STALE")
        self.assertEqual(report["getonbrd"]["jobs_fetched"], 207)

    def test_preflight_failure_skips_aws_and_prep_but_keeps_separate_local_preview(self):
        steps = success_steps()
        steps["preflight"] = StepResult(2, None)
        called = []
        report = run_daily(NOW, lambda name: (called.append(name), steps[name])[1])

        self.assertEqual(called, ["preflight", "getonbrd_preview"])
        self.assertEqual(report["status"], "ERROR")
        self.assertIsNone(report["aws"])
        self.assertEqual(report["errors"][0]["code"], "AWS_IDENTITY_UNVERIFIED")

    def test_source_health_error_blocks_preparation_even_with_ready_batch(self):
        steps = success_steps()
        steps["source_health"] = StepResult(2, {"status": "ERROR",
                                                 "error_code": "COLLECTION_INCOMPLETE"})
        called = []
        report = run_daily(NOW, lambda name: (called.append(name), steps[name])[1])

        self.assertIn("batch_preview", called)
        self.assertNotIn("prepare", called)
        self.assertEqual(report["status"], "ERROR")
        self.assertEqual(report["errors"][0]["code"], "COLLECTION_INCOMPLETE")

    def test_unknown_source_coverage_is_visible_but_does_not_block_valid_preparation(self):
        steps = success_steps()
        steps["source_health"] = StepResult(0, {"status": "NOT_INSTRUMENTED",
                                                 "collection_day": DAY,
                                                 "total_jobs": 35, "sources": []})
        report = run_daily(NOW, lambda name: steps[name])

        self.assertEqual(report["status"], "PARTIAL")
        self.assertEqual(report["warnings"], [{"step": "source_health",
                                               "code": "SOURCE_HEALTH_NOT_INSTRUMENTED"}])
        self.assertEqual(report["preparation"]["prepared"], 1)

    def test_empty_source_is_reported_as_warning(self):
        steps = success_steps()
        steps["source_health"].payload["sources"] = [
            {"source": "greenhouse", "board": "sample", "status": "empty",
             "job_count": 0, "warning": "zero_after_active"}]
        report = run_daily(NOW, lambda name: steps[name])

        self.assertEqual(report["status"], "PARTIAL")
        self.assertEqual(report["warnings"], [{"step": "source_health",
                                               "code": "SOURCE_ZERO_AFTER_ACTIVE",
                                               "source": "greenhouse", "board": "sample"}])

    def test_local_preview_failure_is_reported_without_blocking_aws_preparation(self):
        steps = success_steps()
        steps["getonbrd_preview"] = StepResult(2, {"status": "ERROR",
                                                   "error_code": "GETONBRD_UNAVAILABLE"})
        report = run_daily(NOW, lambda name: steps[name])

        self.assertEqual(report["status"], "PARTIAL")
        self.assertEqual(report["preparation"]["prepared"], 1)
        self.assertIsNone(report["getonbrd"])
        self.assertEqual(report["errors"][0]["code"], "GETONBRD_UNAVAILABLE")

    def test_budget_read_failure_is_partial_but_does_not_claim_spend_is_zero(self):
        steps = success_steps()
        steps["budget"] = StepResult(2, {"status": "ERROR",
                                          "error_code": "BUDGET_READ_FAILED"})
        report = run_daily(NOW, lambda name: steps[name])

        self.assertEqual(report["status"], "PARTIAL")
        self.assertIsNone(report["budget"])
        self.assertEqual(report["preparation"]["prepared"], 1)

    def test_crossed_budget_alert_requires_attention(self):
        steps = success_steps()
        steps["budget"] = StepResult(0, {**steps["budget"].payload,
                                        "status": "AT_OR_ABOVE_ALERT",
                                        "observed_usd": 3.5,
                                        "highest_crossed_alert_usd": 3.0})
        report = run_daily(NOW, lambda name: steps[name])

        self.assertEqual(report["status"], "ATTENTION")
        self.assertEqual(report["budget"]["highest_crossed_alert_usd"], 3.0)

    def test_zero_observed_budget_spend_is_valid(self):
        steps = success_steps()
        steps["budget"] = StepResult(0, {**steps["budget"].payload,
                                        "observed_usd": 0})
        report = run_daily(NOW, lambda name: steps[name])

        self.assertEqual(report["status"], "READY")
        self.assertEqual(report["budget"]["observed_usd"], 0)

    def test_preparation_must_belong_to_the_same_batch_and_never_fakes_completion(self):
        steps = success_steps()
        steps["prepare"] = StepResult(0, {**steps["prepare"].payload,
                                          "batch_id": "alec:2026-10-19"})
        report = run_daily(NOW, lambda name: steps[name])

        self.assertEqual(report["status"], "ERROR")
        self.assertIsNone(report["preparation"])
        self.assertIsNone(report["confirmed_applications"])
        self.assertEqual(report["errors"][0]["code"], "PREPARATION_INVALID")

    def test_failed_run_replaces_old_ready_report_with_current_error(self):
        steps = success_steps()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "daily-report.json"
            save_daily_report(path, run_daily(NOW, lambda name: steps[name]))
            steps["batch_preview"] = StepResult(2, {"status": "ERROR",
                                                    "error_code": "BATCH_INVALID_OR_STALE"})
            save_daily_report(path, run_daily(NOW, lambda name: steps[name]))

            persisted = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(persisted["status"], "ERROR")
            self.assertIsNone(persisted["batch_id"])
            self.assertIsNone(persisted["aws"])

    def test_stdout_digest_has_counts_and_codes_without_job_payload(self):
        report = run_daily(NOW, lambda name: success_steps()[name])
        digest = compact_report(report)

        self.assertEqual(digest["status"], "READY")
        self.assertEqual(digest["aws"]["jobs_found"], 10)
        self.assertEqual(digest["preparation"]["prepared"], 1)
        self.assertNotIn("opportunities", digest["aws"])
        self.assertNotIn("opportunities", digest["getonbrd"])
        self.assertNotIn("fixture", json.dumps(digest))


if __name__ == "__main__":
    unittest.main()
