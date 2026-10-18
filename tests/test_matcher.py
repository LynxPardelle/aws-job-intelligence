import json
import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aji.connectors import parse_feed
from aji.matcher import SearchPolicy, match_job


def example_job():
    path = Path(__file__).parent / "fixtures" / "ashby.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return parse_feed("ashby", "acmeexample", "Acme Example", payload, "2026-10-13T12:00:00Z")[0]


POLICY = SearchPolicy(
    candidate_id="fictional", technologies=("python", "data"),
    allowed_seniority=("senior",), allowed_modalities=("remote",),
    minimum_salary=75000, salary_currency="USD", shortlist_threshold=70,
)


class MatcherTests(unittest.TestCase):
    def test_verified_match_has_explainable_weighted_score(self):
        job = replace(example_job(), mexico_eligibility="eligible")

        result = match_job(job, POLICY, now="2026-10-13T12:00:00Z")

        self.assertEqual(result.decision, "shortlist")
        self.assertEqual(result.score, 100)
        self.assertEqual(result.components, {"stack": 30, "eligibility_modality": 25,
                                             "seniority": 20, "salary": 15, "freshness_quality": 10})
        self.assertEqual(result.matched_technologies, ("python", "data"))
        self.assertEqual(result.unknowns, ())

    def test_unknown_mexico_eligibility_requires_review(self):
        result = match_job(example_job(), POLICY, now="2026-10-13T12:00:00Z")

        self.assertEqual(result.decision, "review")
        self.assertIn("mexico_eligibility", result.unknowns)

    def test_explicit_ineligibility_excludes_even_with_high_score(self):
        job = replace(example_job(), mexico_eligibility="ineligible")

        result = match_job(job, POLICY, now="2026-10-13T12:00:00Z")

        self.assertEqual(result.decision, "exclude")
        self.assertIn("not_eligible_from_mexico", result.reasons)

    def test_missing_salary_does_not_satisfy_minimum(self):
        job = replace(example_job(), mexico_eligibility="eligible", salary=None)

        result = match_job(job, POLICY, now="2026-10-13T12:00:00Z")

        self.assertEqual(result.decision, "review")
        self.assertEqual(result.components["salary"], 0)
        self.assertIn("salary", result.unknowns)

    def test_salary_below_minimum_excludes(self):
        job = replace(example_job(), mexico_eligibility="eligible",
                      salary=replace(example_job().salary, minimum=40000, maximum=50000))

        result = match_job(job, POLICY, now="2026-10-13T12:00:00Z")

        self.assertEqual(result.decision, "exclude")
        self.assertIn("below_salary_minimum", result.reasons)

    def test_reported_monthly_amount_does_not_prove_net_income(self):
        job = replace(example_job(), mexico_eligibility="eligible",
                      salary=replace(example_job().salary, currency="EUR", interval="month",
                                     minimum=8000, maximum=10000))
        net_policy = replace(POLICY, minimum_salary=6500, salary_currency="EUR",
                             salary_interval="month", salary_basis="net")

        result = match_job(job, net_policy, now="2026-10-13T12:00:00Z")

        self.assertEqual(result.decision, "review")
        self.assertEqual(result.components["salary"], 0)
        self.assertIn("net_salary_unverified", result.unknowns)
        self.assertNotIn("below_salary_minimum", result.reasons)

    def test_closed_or_incompatible_modality_excludes(self):
        job = replace(example_job(), mexico_eligibility="eligible")

        self.assertEqual(match_job(replace(job, status="closed"), POLICY, now="2026-10-13T12:00:00Z").decision,
                         "exclude")
        self.assertEqual(match_job(replace(job, modality="onsite"), POLICY, now="2026-10-13T12:00:00Z").decision,
                         "exclude")

    def test_role_and_company_preferences_are_enforced(self):
        job = replace(example_job(), mexico_eligibility="eligible")
        wrong_role = replace(POLICY, roles=("Frontend Developer",))
        excluded_company = replace(POLICY, excluded_companies=("acme example",))
        self.assertIn("incompatible_role", match_job(job, wrong_role,
                      now="2026-10-13T12:00:00Z").reasons)
        self.assertIn("excluded_company", match_job(job, excluded_company,
                      now="2026-10-13T12:00:00Z").reasons)
        allowed = replace(POLICY, roles=("Data Engineer",))
        self.assertEqual(match_job(job, allowed, now="2026-10-13T12:00:00Z").decision,
                         "shortlist")


if __name__ == "__main__":
    unittest.main()
