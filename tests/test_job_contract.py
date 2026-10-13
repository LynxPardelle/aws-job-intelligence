import json
import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aji.connectors import parse_feed
from aji.dedupe import canonical_url, deduplicate_jobs


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "greenhouse.json"


def example_job():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return parse_feed("greenhouse", "acmeexample", "Acme Example", payload, "2026-10-13T12:00:00Z")[0]


class JobContractTests(unittest.TestCase):
    def test_normalized_job_matches_versioned_contract(self):
        job = example_job().to_dict()
        schema = json.loads((ROOT / "schemas" / "job.schema.json").read_text(encoding="utf-8"))

        self.assertEqual(job["schema_version"], "1.0")
        self.assertEqual(set(job), set(schema["required"]))
        self.assertFalse(schema["additionalProperties"])
        self.assertIn("unknown", schema["properties"]["mexico_eligibility"]["enum"])
        self.assertIsNone(job["salary"])

    def test_canonical_url_removes_tracking_but_keeps_job_identifier(self):
        self.assertEqual(
            canonical_url("https://CAREERS.example.com/jobs?gh_jid=101&utm_source=email#apply"),
            "https://careers.example.com/jobs?gh_jid=101",
        )

    def test_deduplication_uses_external_id_and_canonical_url(self):
        original = example_job()
        same_id = replace(original, source_url="https://careers.example.com/jobs/101")
        same_url = replace(original, job_id="lever:acmeexample:other", external_id="other",
                           source_url="https://boards.greenhouse.io/acmeexample/jobs/101?utm_campaign=x")
        distinct = replace(original, job_id="greenhouse:acmeexample:102", external_id="102",
                           source_url="https://boards.greenhouse.io/acmeexample/jobs/102")

        self.assertEqual(deduplicate_jobs([original, same_id, same_url, distinct]), [original, distinct])


if __name__ == "__main__":
    unittest.main()
