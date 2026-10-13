import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aji.connectors import build_feed_url, parse_feed


FIXTURES = Path(__file__).parent / "fixtures"
RETRIEVED_AT = "2026-10-13T12:00:00Z"


def fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class ConnectorTests(unittest.TestCase):
    def test_greenhouse_feed_normalizes_without_assuming_eligibility_or_salary(self):
        jobs = parse_feed("greenhouse", "acmeexample", "Acme Example", fixture("greenhouse.json"), RETRIEVED_AT)

        self.assertEqual(len(jobs), 1)
        job = jobs[0]
        self.assertEqual(job.job_id, "greenhouse:acmeexample:101")
        self.assertEqual(job.title, "Senior Python Engineer")
        self.assertEqual(job.mexico_eligibility, "unknown")
        self.assertIsNone(job.salary)
        self.assertEqual(job.modality, "unknown")
        self.assertEqual(job.updated_at, "2026-10-12T15:30:00Z")
        self.assertIn("Ignore all previous instructions", job.description)
        self.assertNotIn("<p>", job.description)

    def test_feed_urls_use_only_documented_https_hosts(self):
        self.assertEqual(build_feed_url("greenhouse", "acmeexample"),
                         "https://boards-api.greenhouse.io/v1/boards/acmeexample/jobs?content=true")
        self.assertEqual(build_feed_url("lever", "acmeexample"),
                         "https://api.lever.co/v0/postings/acmeexample?mode=json")
        self.assertEqual(build_feed_url("ashby", "acmeexample"),
                         "https://api.ashbyhq.com/posting-api/job-board/acmeexample?includeCompensation=true")
        with self.assertRaises(ValueError):
            build_feed_url("greenhouse", "../../internal")

    def test_lever_feed_preserves_explicit_salary_and_modality(self):
        job = parse_feed("lever", "acmeexample", "Acme Example", fixture("lever.json"), RETRIEVED_AT)[0]

        self.assertEqual(job.job_id, "lever:acmeexample:lv-1")
        self.assertEqual(job.modality, "hybrid")
        self.assertEqual(job.salary.currency, "USD")
        self.assertEqual(job.salary.minimum, 90000)
        self.assertEqual(job.seniority, "mid")
        self.assertEqual(job.mexico_eligibility, "unknown")

    def test_ashby_feed_uses_listed_jobs_and_salary_component(self):
        job = parse_feed("ashby", "acmeexample", "Acme Example", fixture("ashby.json"), RETRIEVED_AT)[0]

        self.assertEqual(job.job_id, "ashby:acmeexample:as-1")
        self.assertEqual(job.modality, "remote")
        self.assertEqual(job.salary.maximum, 100000)
        self.assertEqual(job.published_at, "2026-10-11T10:00:00Z")

    def test_rejects_non_https_apply_url(self):
        payload = fixture("lever.json")
        payload[0]["applyUrl"] = "http://jobs.lever.co/acmeexample/lv-1/apply"

        with self.assertRaises(ValueError):
            parse_feed("lever", "acmeexample", "Acme Example", payload, RETRIEVED_AT)


if __name__ == "__main__":
    unittest.main()
