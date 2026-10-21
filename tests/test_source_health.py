import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aji.source_health import summarize_source_health


class SourceHealthTests(unittest.TestCase):
    def test_reports_empty_and_drop_without_calling_a_valid_zero_a_failure(self):
        today = {"status": "COMPLETE", "collection_day": "2026-10-20", "job_count": 11,
                 "source_health": [
                     {"source": "greenhouse", "board": "first", "status": "empty", "job_count": 0},
                     {"source": "greenhouse", "board": "second", "status": "active", "job_count": 11},
                 ]}
        yesterday = {"status": "COMPLETE", "collection_day": "2026-10-19",
                     "source_health": [
                         {"source": "greenhouse", "board": "first", "status": "active", "job_count": 20},
                         {"source": "greenhouse", "board": "second", "status": "active", "job_count": 12},
                     ]}
        summary = summarize_source_health(today, yesterday, "2026-10-20")
        self.assertEqual(summary["status"], "COMPLETE")
        self.assertEqual(summary["total_jobs"], 11)
        self.assertEqual(summary["sources"][0]["warning"], "zero_after_active")
        self.assertEqual(summary["sources"][0]["status"], "empty")
        self.assertIsNone(summary["sources"][1]["warning"])

    def test_missing_or_stale_collection_is_error_not_previous_day_success(self):
        with self.assertRaises(ValueError):
            summarize_source_health(None, None, "2026-10-20")
        with self.assertRaises(ValueError):
            summarize_source_health({"status": "COMPLETE", "collection_day": "2026-10-19",
                                     "source_health": []}, None, "2026-10-20")

    def test_old_marker_without_source_health_is_explicitly_uninstrumented(self):
        summary = summarize_source_health(
            {"status": "COMPLETE", "collection_day": "2026-10-20", "job_count": 4},
            None, "2026-10-20")
        self.assertEqual(summary["status"], "NOT_INSTRUMENTED")
        self.assertEqual(summary["sources"], [])

    def test_dynamodb_decimal_counts_are_accepted_only_when_integral(self):
        summary = summarize_source_health(
            {"status": "COMPLETE", "collection_day": "2026-10-20",
             "job_count": Decimal("2"), "source_health": [
                 {"source": "greenhouse", "board": "first", "status": "active",
                  "job_count": Decimal("2")},
             ]}, None, "2026-10-20")
        self.assertEqual(summary["total_jobs"], 2)
        self.assertEqual(summary["sources"][0]["job_count"], 2)
        with self.assertRaises(ValueError):
            summarize_source_health(
                {"status": "COMPLETE", "collection_day": "2026-10-20",
                 "job_count": Decimal("1.5"), "source_health": []}, None, "2026-10-20")


if __name__ == "__main__":
    unittest.main()
