import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aji.connectors import parse_feed
from aji.liveness import check_job_liveness


NOW = "2026-10-13T15:00:00Z"


def fixture_job(source, name, board="acmeexample"):
    payload = json.loads((Path(__file__).parent / "fixtures" / name).read_text("utf-8"))
    return parse_feed(source, board, "Example", payload, NOW)[0]


class LivenessTests(unittest.TestCase):
    def test_exact_job_in_official_feed_is_active(self):
        job = fixture_job("greenhouse", "greenhouse.json")
        result = check_job_liveness(job, NOW, fetcher=lambda *_: [job])
        self.assertEqual(result.status, "active")
        self.assertEqual(result.reason, "present_in_official_feed")

    def test_missing_job_on_full_ats_board_is_closed_but_aggregator_is_unknown(self):
        ats = fixture_job("greenhouse", "greenhouse.json")
        board = fixture_job("getonbrd", "getonbrd.json", "programming")
        self.assertEqual(check_job_liveness(ats, NOW, fetcher=lambda *_: []).status, "closed")
        self.assertEqual(check_job_liveness(board, NOW, fetcher=lambda *_: []).status, "unknown")

    def test_feed_error_and_changed_url_cannot_confirm_liveness(self):
        job = fixture_job("greenhouse", "greenhouse.json")
        unavailable = check_job_liveness(job, NOW,
                                         fetcher=lambda *_: (_ for _ in ()).throw(
                                             RuntimeError("private upstream detail")))
        self.assertEqual(unavailable.status, "unknown")
        self.assertNotIn("private upstream detail", unavailable.reason)
        changed = fixture_job("greenhouse", "greenhouse.json")
        changed = type(changed)(**{**changed.to_dict(), "source_url": "https://boards.greenhouse.io/acmeexample/jobs/other"})
        self.assertEqual(check_job_liveness(job, NOW, fetcher=lambda *_: [changed]).status, "unknown")


if __name__ == "__main__":
    unittest.main()
