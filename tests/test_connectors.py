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
        self.assertEqual(job.modality, "remote")
        self.assertEqual(job.updated_at, "2026-10-12T15:30:00Z")
        self.assertIn("Ignore all previous instructions", job.description)
        self.assertNotIn("<p>", job.description)

    def test_greenhouse_explicit_employer_salary_preserves_gross_basis(self):
        payload = fixture("greenhouse.json")
        payload["jobs"][0]["content"] = (
            "<p>The salary range for this role is $5,000 - $9,500 per month (Gross in USD)</p>"
        )

        job = parse_feed("greenhouse", "acmeexample", "Acme Example", payload, RETRIEVED_AT)[0]

        self.assertEqual(job.salary.currency, "USD")
        self.assertEqual(job.salary.interval, "month")
        self.assertEqual(job.salary.minimum, 5000)
        self.assertEqual(job.salary.maximum, 9500)
        self.assertEqual(job.salary.basis, "gross")

    def test_greenhouse_conflicting_salary_ranges_remain_unverified(self):
        payload = fixture("greenhouse.json")
        payload["jobs"][0]["content"] = (
            "<p>The salary range for this role is $5,000 - $9,500 per month (Gross in USD).</p>"
            "<p>The salary range for this role is $3,000 - $5,000 per month (Gross in USD).</p>"
        )

        job = parse_feed("greenhouse", "acmeexample", "Acme Example", payload, RETRIEVED_AT)[0]

        self.assertIsNone(job.salary)

    def test_greenhouse_us_only_pay_disclosure_is_not_mexico_salary(self):
        payload = fixture("greenhouse.json")
        payload["jobs"][0]["location"] = {"name": "Mexico, Remote"}
        payload["jobs"][0]["content"] = (
            "<p>For US-based employees, the salary range for this role is "
            "$150,000 - $200,000 per year (Gross in USD). "
            "Compensation outside the United States differs.</p>"
        )

        job = parse_feed("greenhouse", "acmeexample", "Acme Example", payload, RETRIEVED_AT)[0]

        self.assertIsNone(job.salary)

    def test_greenhouse_explicit_monthly_b2b_rate_keeps_contract_basis(self):
        payload = fixture("greenhouse.json")
        payload["jobs"][0]["content"] = (
            "<p>Contract Type: Fixed-rate monthly Independent B2B Service Agreement "
            "executed via Rippling, $6,000-$8,000 USD/mo based on experience.</p>"
        )

        job = parse_feed("greenhouse", "acmeexample", "Acme Example", payload, RETRIEVED_AT)[0]

        self.assertEqual(job.salary.currency, "USD")
        self.assertEqual(job.salary.interval, "month")
        self.assertEqual(job.salary.minimum, 6000)
        self.assertEqual(job.salary.maximum, 8000)
        self.assertEqual(job.salary.basis, "contract")

    def test_greenhouse_mexico_remote_location_is_explicit_eligibility(self):
        payload = fixture("greenhouse.json")
        payload["jobs"][0]["location"] = {"name": "Mexico - remote"}

        job = parse_feed("greenhouse", "acmeexample", "Acme Example", payload, RETRIEVED_AT)[0]

        self.assertEqual(job.modality, "remote")
        self.assertEqual(job.mexico_eligibility, "eligible")

    def test_greenhouse_brazil_only_posting_is_not_mexico_eligible(self):
        payload = fixture("greenhouse.json")
        payload["jobs"][0]["title"] = "Backend Engineer Consultant - (remote - Brazil)"
        payload["jobs"][0]["location"] = {"name": "Brazil - remote"}

        job = parse_feed("greenhouse", "acmeexample", "Acme Example", payload, RETRIEVED_AT)[0]

        self.assertEqual(job.mexico_eligibility, "ineligible")

    def test_feed_urls_use_only_documented_https_hosts(self):
        self.assertEqual(build_feed_url("greenhouse", "acmeexample"),
                         "https://boards-api.greenhouse.io/v1/boards/acmeexample/jobs?content=true")
        self.assertEqual(build_feed_url("lever", "acmeexample"),
                         "https://api.lever.co/v0/postings/acmeexample?mode=json")
        self.assertEqual(build_feed_url("ashby", "acmeexample"),
                         "https://api.ashbyhq.com/posting-api/job-board/acmeexample?includeCompensation=true")
        with self.assertRaises(ValueError):
            build_feed_url("greenhouse", "../../internal")

    def test_getonbrd_feed_uses_fixed_host_and_validated_category(self):
        self.assertEqual(
            build_feed_url("getonbrd", "machine-learning-ai"),
            "https://www.getonbrd.com/api/v0/categories/machine-learning-ai/jobs?per_page=100&expand%5B%5D=company&page=1",
        )
        with self.assertRaises(ValueError):
            build_feed_url("getonbrd", "../internal")

    def test_getonbrd_normalizes_description_without_assuming_mexico_or_currency(self):
        jobs = parse_feed("getonbrd", "programming", "Get on Board",
                          fixture("getonbrd.json"), RETRIEVED_AT)
        self.assertEqual(len(jobs), 2)
        self.assertEqual(jobs[0].job_id, "getonbrd:programming:sample-101")
        self.assertEqual(jobs[0].company, "Example Technology")
        self.assertEqual(jobs[0].modality, "remote")
        self.assertEqual(jobs[0].mexico_eligibility, "unknown")
        self.assertIsNone(jobs[0].salary)
        self.assertIn("Work with Python and AWS.", jobs[0].description)
        self.assertEqual(jobs[0].published_at, "2026-10-13T12:00:00Z")
        self.assertEqual(jobs[1].modality, "unknown")
        self.assertEqual(jobs[1].mexico_eligibility, "unknown")

    def test_getonbrd_rejects_off_host_posting_url_and_invalid_payload(self):
        payload = fixture("getonbrd.json")
        payload["data"][0]["links"]["public_url"] = "https://evil.example/jobs/steal"
        with self.assertRaises(ValueError):
            parse_feed("getonbrd", "programming", "Get on Board", payload, RETRIEVED_AT)
        with self.assertRaises(ValueError):
            parse_feed("getonbrd", "programming", "Get on Board", {"message": "blocked"}, RETRIEVED_AT)
        malformed = fixture("getonbrd.json")
        malformed["data"][0]["attributes"]["company"] = "not-an-object"
        with self.assertRaises(ValueError):
            parse_feed("getonbrd", "programming", "Get on Board", malformed, RETRIEVED_AT)

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
