import io
import json
import os
import sys
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aji.connectors import parse_feed
from aji.matcher import SearchPolicy
from aji.publisher_handler import _policy_from_dict, handler, publish_once


class FixedDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 10, 13, 14, 15, tzinfo=tz)


class FakeS3:
    def __init__(self):
        self.objects = {}

    def put_object(self, *, Bucket, Key, Body, ContentType):
        self.objects[(Bucket, Key)] = Body

    def get_object(self, *, Bucket, Key):
        return {"Body": io.BytesIO(self.objects[(Bucket, Key)])}


class FakeTable:
    def __init__(self, job, *, status="COMPLETE", count=1):
        self.job = job
        self.marker = {"job_id": "run#2026-10-13", "status": status,
                       "run_id": "2026-10-13T14:00:00Z", "job_count": count}
        self.queries = []

    def get_item(self, *, Key, ConsistentRead):
        assert Key == {"job_id": "run#2026-10-13"} and ConsistentRead is True
        return {"Item": self.marker}

    def query(self, **kwargs):
        self.queries.append(kwargs)
        assert kwargs["IndexName"] == "collection-run-index"
        assert kwargs["ExpressionAttributeValues"] == {":run_id": self.marker["run_id"]}
        return {"Items": [{**self.job.to_dict(), "collection_run_id": self.marker["run_id"],
                           "record_type": "job", "expires_at": 123456789}]}


def inputs():
    payload = json.loads((Path(__file__).parent / "fixtures" / "ashby.json").read_text("utf-8"))
    job = parse_feed("ashby", "acmeexample", "Acme Example", payload, "2026-10-13T14:00:00Z")[0]
    policy = SearchPolicy("alec", ("python", "data"), ("senior",), ("remote",), None, None, 70)
    return job, policy


class PublisherTests(unittest.TestCase):
    def test_complete_collection_publishes_review_batch_for_unknown_eligibility(self):
        job, policy = inputs()
        s3 = FakeS3()
        result = publish_once("alec", FakeTable(job), s3, "alec-private", policy,
                              "2026-10-13T14:15:00Z")
        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["job_ids"], [job.job_id])
        matches = json.loads(s3.objects[("alec-private", "batches/2026-10-13/matches.json")])
        self.assertEqual(matches[0]["decision"], "review")

    def test_missing_or_incomplete_collection_marks_batch_failed(self):
        job, policy = inputs()
        for status, count in (("STARTED", 1), ("COMPLETE", 2)):
            with self.subTest(status=status, count=count):
                s3 = FakeS3()
                with self.assertRaises(ValueError):
                    publish_once("alec", FakeTable(job, status=status, count=count), s3,
                                 "alec-private", policy, "2026-10-13T14:15:00Z")
                manifest = json.loads(s3.objects[("alec-private", "batches/2026-10-13/manifest.json")])
                self.assertEqual(manifest["status"], "FAILED")

    def test_disabled_handler_does_not_create_aws_client(self):
        with patch.dict(os.environ, {"AJI_PUBLISH_ENABLED": "false"}):
            self.assertEqual(handler({}, None), {"status": "DISABLED"})

    def test_enabled_handler_reads_only_its_candidate_policy_and_publishes(self):
        job, _ = inputs()
        s3 = FakeS3()
        policy = {
            "candidate_id": "alec", "technologies": ["python", "data"],
            "allowed_seniority": ["senior"], "allowed_modalities": ["remote"],
            "shortlist_threshold": 70, "max_jobs_per_day": 10,
        }
        s3.put_object(Bucket="alec-private", Key="config/search-policy.json",
                      Body=json.dumps(policy).encode(), ContentType="application/json")
        table = FakeTable(job)
        resource = SimpleNamespace(Table=lambda name: table)
        boto3 = SimpleNamespace(client=lambda name: s3, resource=lambda name: resource)
        environment = {
            "AJI_PUBLISH_ENABLED": "true", "AJI_CANDIDATE_ID": "alec",
            "AJI_PRIVATE_BUCKET": "alec-private", "AJI_PUBLIC_TABLE": "aji-public-jobs-dev",
        }
        with patch.dict(os.environ, environment), patch.dict(sys.modules, {"boto3": boto3}), \
                patch("aji.publisher_handler.datetime", FixedDatetime):
            result = handler({}, None)
        self.assertEqual(result, {"status": "READY", "jobs_published": 1})
        self.assertEqual(len(table.queries), 1)

    def test_wrong_candidate_policy_fails_closed(self):
        s3 = FakeS3()
        policy = {"candidate_id": "hector"}
        s3.put_object(Bucket="alec-private", Key="config/search-policy.json",
                      Body=json.dumps(policy).encode(), ContentType="application/json")
        boto3 = SimpleNamespace(client=lambda name: s3,
                                resource=lambda name: self.fail("public table should not be read"))
        environment = {
            "AJI_PUBLISH_ENABLED": "true", "AJI_CANDIDATE_ID": "alec",
            "AJI_PRIVATE_BUCKET": "alec-private", "AJI_PUBLIC_TABLE": "aji-public-jobs-dev",
        }
        with patch.dict(os.environ, environment), patch.dict(sys.modules, {"boto3": boto3}), \
                patch("aji.publisher_handler.datetime", FixedDatetime):
            with self.assertRaisesRegex(ValueError, "another candidate"):
                handler({}, None)
        manifest = json.loads(s3.objects[("alec-private", "batches/2026-10-13/manifest.json")])
        self.assertEqual(manifest["status"], "FAILED")

    def test_oversized_private_policy_fails_before_public_query(self):
        s3 = FakeS3()
        s3.put_object(Bucket="alec-private", Key="config/search-policy.json",
                      Body=b" " * 65_537, ContentType="application/json")
        boto3 = SimpleNamespace(client=lambda name: s3,
                                resource=lambda name: self.fail("public table should not be read"))
        environment = {
            "AJI_PUBLISH_ENABLED": "true", "AJI_CANDIDATE_ID": "alec",
            "AJI_PRIVATE_BUCKET": "alec-private", "AJI_PUBLIC_TABLE": "aji-public-jobs-dev",
        }
        with patch.dict(os.environ, environment), patch.dict(sys.modules, {"boto3": boto3}), \
                patch("aji.publisher_handler.datetime", FixedDatetime):
            with self.assertRaisesRegex(ValueError, "policy exceeds size limit"):
                handler({}, None)
        manifest = json.loads(s3.objects[("alec-private", "batches/2026-10-13/manifest.json")])
        self.assertEqual(manifest["status"], "FAILED")

    def test_policy_rejects_unsupported_or_malformed_constraints(self):
        valid = {
            "candidate_id": "alec", "roles": ["Data Engineer"],
            "technologies": ["python"], "allowed_seniority": ["senior"],
            "allowed_modalities": ["remote"], "eligible_countries": ["MX"],
            "excluded_companies": ["Example Corp"], "shortlist_threshold": 70,
            "prepare_threshold": 85, "application_mode": "PREPARE",
        }
        policy, quota = _policy_from_dict(valid, "alec")
        self.assertEqual(policy.roles, ("Data Engineer",))
        self.assertEqual(policy.excluded_companies, ("Example Corp",))
        self.assertEqual(policy.prepare_threshold, 85)
        self.assertEqual(quota, 10)
        net_policy, _ = _policy_from_dict({**valid, "minimum_salary": 6500,
                                           "salary_currency": "MXN", "salary_interval": "month",
                                           "salary_basis": "net"}, "alec")
        self.assertEqual(net_policy.salary_basis, "net")
        conditions_policy, _ = _policy_from_dict({**valid, "travel_accepted": False,
                                                  "rotating_shifts_accepted": False}, "alec")
        self.assertFalse(conditions_policy.travel_accepted)
        self.assertFalse(conditions_policy.rotating_shifts_accepted)
        for overrides in ({"technologies": "python"}, {"eligible_countries": ["US"]},
                          {"application_mode": "AUTO_SUBMIT"}, {"unknown_filter": "anything"},
                          {"prepare_threshold": 50}, {"salary_basis": "after_tax_guess"},
                          {"travel_accepted": "false"}, {"rotating_shifts_accepted": 0}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                _policy_from_dict({**valid, **overrides}, "alec")

    def test_versioned_example_policy_parses_after_setting_candidate(self):
        example = json.loads((Path(__file__).resolve().parents[1] / "config" /
                              "search-policy.example.json").read_text("utf-8"))
        example["candidate_id"] = "alec"
        policy, quota = _policy_from_dict(example, "alec")
        self.assertEqual(policy.prepare_threshold, 85)
        self.assertEqual(quota, 10)


if __name__ == "__main__":
    unittest.main()
