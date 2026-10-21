import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aji.connectors import parse_feed
from aji.getonbrd_preview import build_getonbrd_preview
from aji.matcher import SearchPolicy


NOW = "2026-10-13T15:00:00Z"


def policy():
    return SearchPolicy(candidate_id="fictional", technologies=("Python", "AWS"),
                        allowed_seniority=("senior",), allowed_modalities=("remote",),
                        minimum_salary=95000, salary_currency="MXN",
                        shortlist_threshold=60, salary_interval="month", salary_basis="net",
                        travel_accepted=False, rotating_shifts_accepted=False)


def job(board, suffix):
    payload = json.loads((Path(__file__).parent / "fixtures" / "getonbrd.json").read_text("utf-8"))
    payload["data"] = payload["data"][:1]
    payload["data"][0]["id"] = suffix
    payload["data"][0]["links"]["public_url"] = f"https://www.getonbrd.com/jobs/{suffix}"
    return parse_feed("getonbrd", board, "Get on Board", payload, NOW)[0]


class GetOnBoardPreviewTests(unittest.TestCase):
    def test_scans_three_fixed_categories_and_keeps_unknown_conditions_in_review(self):
        calls = []

        def fetcher(source, board, company, now):
            calls.append((source, board, company, now))
            return [job(board, "same") if board != "machine-learning-ai" else job(board, "other")]

        summary = build_getonbrd_preview(policy(), NOW, fetcher=fetcher, max_jobs=10)
        self.assertEqual([item[1] for item in calls],
                         ["programming", "operations-management", "machine-learning-ai"])
        self.assertEqual(summary["jobs_fetched"], 3)
        self.assertEqual(summary["unique_jobs"], 2)
        self.assertEqual(summary["shortlisted"], 0)
        self.assertEqual(summary["needs_review"], 2)
        self.assertTrue(all(item["decision"] == "review" for item in summary["opportunities"]))
        self.assertTrue(summary["opportunities"][0]["apply_url"].startswith(
            "https://www.getonbrd.com/jobs/"))
        self.assertIn("mexico_eligibility", summary["opportunities"][0]["unknowns"])

    def test_empty_feed_is_explicit_and_source_failure_does_not_reuse_data(self):
        empty = build_getonbrd_preview(policy(), NOW, fetcher=lambda *_: [])
        self.assertEqual(empty["status"], "EMPTY")
        self.assertEqual(empty["opportunities"], [])
        with self.assertRaises(RuntimeError):
            build_getonbrd_preview(policy(), NOW,
                                   fetcher=lambda *_: (_ for _ in ()).throw(RuntimeError("offline")))

    def test_full_first_page_reports_possible_truncation_and_total_review_count(self):
        def fetcher(_, board, *__):
            return [job(board, f"{board}-{index}") for index in range(100)] if board == "programming" else []

        summary = build_getonbrd_preview(policy(), NOW, fetcher=fetcher, max_jobs=10)
        self.assertEqual(summary["total_needs_review"], 100)
        self.assertEqual(summary["needs_review"], 10)
        self.assertEqual(summary["possibly_truncated_categories"], ["programming"])


if __name__ == "__main__":
    unittest.main()
