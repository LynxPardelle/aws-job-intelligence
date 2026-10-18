import json
import sys
import unittest
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aji.connectors import parse_feed
from aji.dedupe import canonical_url, deduplicate_jobs
from aji.models import Salary, job_from_dict


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "greenhouse.json"


def example_job():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return parse_feed("greenhouse", "acmeexample", "Acme Example", payload, "2026-10-13T12:00:00Z")[0]


class JobContractTests(unittest.TestCase):
    def test_normalized_job_matches_versioned_contract(self):
        job = example_job().to_dict()
        schema = json.loads((ROOT / "schemas" / "job.schema.json").read_text(encoding="utf-8"))

        self.assertEqual(job["schema_version"], "1.1")
        self.assertEqual(set(job), set(schema["required"]))
        self.assertFalse(schema["additionalProperties"])
        self.assertIn("unknown", schema["properties"]["mexico_eligibility"]["enum"])
        self.assertEqual(job["travel_requirement"], "unknown")
        self.assertEqual(job["rotating_shifts_requirement"], "unknown")
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

    def test_dynamodb_job_roundtrip_strips_collection_metadata(self):
        original = replace(example_job(), salary=Salary("USD", "year", 100000.0, 150000.0))
        item = original.to_dict()
        item["salary"]["minimum"] = Decimal("100000")
        item["salary"]["maximum"] = Decimal("150000")
        item["collection_run_id"] = "fixture-run"
        item["expires_at"] = 123456789
        self.assertEqual(job_from_dict(item), original)

    def test_older_public_job_defaults_new_requirement_fields_to_unknown(self):
        original = example_job()
        legacy_item = original.to_dict()
        legacy_item["schema_version"] = "1.0"
        legacy_item.pop("travel_requirement", None)
        legacy_item.pop("rotating_shifts_requirement", None)

        self.assertEqual(job_from_dict(legacy_item), original)
        legacy_item["travel_requirement"] = "not_required"
        self.assertEqual(job_from_dict(legacy_item).travel_requirement, "unknown")

    def test_current_public_job_requires_condition_fields(self):
        item = example_job().to_dict()
        item.pop("travel_requirement")
        with self.assertRaises(ValueError):
            job_from_dict(item)

    def test_requirement_status_must_be_a_known_value(self):
        with self.assertRaises(ValueError):
            replace(example_job(), travel_requirement="maybe")


if __name__ == "__main__":
    unittest.main()
