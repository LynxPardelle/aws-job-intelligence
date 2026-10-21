import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aji.job_history import annotate_summary_history, record_seen_jobs


POSTING = {"job_id": "greenhouse:sample:101",
           "source_url": "https://boards.greenhouse.io/sample/jobs/101?utm_source=mail"}


class JobHistoryTests(unittest.TestCase):
    def test_same_day_is_idempotent_and_next_day_is_repeat(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.sqlite3"
            first = record_seen_jobs(path, "fictional", "2026-10-13", [POSTING])[0]
            same_day = record_seen_jobs(path, "fictional", "2026-10-13", [POSTING])[0]
            next_day = record_seen_jobs(path, "fictional", "2026-10-14", [POSTING])[0]
            self.assertFalse(first["seen_before"])
            self.assertEqual(first["seen_days"], 1)
            self.assertFalse(same_day["seen_before"])
            self.assertEqual(same_day["seen_days"], 1)
            self.assertTrue(next_day["seen_before"])
            self.assertEqual(next_day["seen_days"], 2)

    def test_same_url_new_id_is_flagged_but_not_hidden_and_candidates_are_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.sqlite3"
            record_seen_jobs(path, "fictional", "2026-10-13", [POSTING])
            changed = {**POSTING, "job_id": "greenhouse:sample:202",
                       "source_url": "https://boards.greenhouse.io/sample/jobs/101"}
            repeat = record_seen_jobs(path, "fictional", "2026-10-14", [changed])[0]
            other = record_seen_jobs(path, "other", "2026-10-14", [changed])[0]
            self.assertTrue(repeat["possible_repost"])
            self.assertTrue(repeat["seen_before"])
            self.assertFalse(other["seen_before"])
            self.assertFalse(other["possible_repost"])

    def test_invalid_identity_or_url_never_creates_a_history(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.sqlite3"
            with self.assertRaises(ValueError):
                record_seen_jobs(path, "../other", "2026-10-13", [POSTING])
            with self.assertRaises(ValueError):
                record_seen_jobs(path, "fictional", "2026-10-13",
                                 [{**POSTING, "source_url": "http://localhost/private"}])
            self.assertFalse(path.exists())

    def test_only_ready_summary_is_annotated_and_failed_batch_is_not_reused(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.sqlite3"
            failed = annotate_summary_history(
                {"status": "ERROR", "opportunities": [POSTING]}, path,
                "fictional", "2026-10-13")
            self.assertEqual(failed["status"], "ERROR")
            self.assertFalse(path.exists())
            ready = annotate_summary_history(
                {"status": "READY", "opportunities": [POSTING]}, path,
                "fictional", "2026-10-13")
            self.assertEqual(ready["new_opportunities"], 1)
            self.assertFalse(ready["opportunities"][0]["seen_before"])


if __name__ == "__main__":
    unittest.main()
