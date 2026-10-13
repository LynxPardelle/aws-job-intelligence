import io
import json
import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aji.aws_batch_io import CandidateBatchStore, publish_candidate_batch
from aji.connectors import parse_feed
from aji.matcher import SearchPolicy


class FakeS3:
    def __init__(self, fail_on=None):
        self.objects = {}
        self.writes = []
        self.fail_on = fail_on

    def put_object(self, *, Bucket, Key, Body, ContentType):
        if self.fail_on and Key.endswith(self.fail_on):
            raise RuntimeError("simulated S3 write failure")
        self.objects[(Bucket, Key)] = Body
        self.writes.append((Key, Body))

    def get_object(self, *, Bucket, Key):
        return {"Body": io.BytesIO(self.objects[(Bucket, Key)])}


class ConditionalFailure(Exception):
    response = {"Error": {"Code": "ConditionalCheckFailedException"}}


class FakeTable:
    def __init__(self):
        self.items = {}

    def put_item(self, *, Item, ConditionExpression):
        assert ConditionExpression == "attribute_not_exists(pk) AND attribute_not_exists(sk)"
        key = Item["pk"], Item["sk"]
        if key in self.items:
            raise ConditionalFailure()
        self.items[key] = Item


def inputs():
    fixture = Path(__file__).parent / "fixtures" / "ashby.json"
    payload = json.loads(fixture.read_text("utf-8"))
    job = parse_feed("ashby", "acmeexample", "Acme Example", payload, "2026-10-13T14:00:00Z")[0]
    job = replace(job, mexico_eligibility="eligible")
    policy = SearchPolicy("alec", ("python", "data"), ("senior",), ("remote",), 75000, "USD", 70)
    return job, policy


class AwsBatchIoTests(unittest.TestCase):
    def test_manifest_is_written_last_and_pull_validates_and_locks(self):
        job, policy = inputs()
        s3 = FakeS3()
        table = FakeTable()
        manifest = publish_candidate_batch([job], policy, "2026-10-13T15:00:00Z", s3, "alec-private")

        self.assertEqual(manifest["status"], "READY")
        self.assertEqual(s3.writes[0][0], "batches/2026-10-13/manifest.json")
        self.assertEqual(json.loads(s3.writes[0][1])["status"], "FAILED")
        self.assertEqual(s3.writes[-1][0], "batches/2026-10-13/manifest.json")
        self.assertEqual(json.loads(s3.writes[-1][1])["status"], "READY")

        store = CandidateBatchStore("alec", "alec-private", s3, table)
        loaded, jobs, matches = store.load("2026-10-13T15:05:00Z")
        self.assertEqual(loaded["job_ids"], [job.job_id])
        self.assertEqual(jobs[0]["job_id"], job.job_id)
        self.assertEqual(matches[0]["decision"], "shortlist")
        self.assertTrue(store.acquire_lock(loaded, "2026-10-13T15:05:00Z"))
        self.assertFalse(store.acquire_lock(loaded, "2026-10-13T15:05:00Z"))

    def test_failed_or_stale_batch_cannot_be_loaded(self):
        job, policy = inputs()
        s3 = FakeS3()
        store = CandidateBatchStore("alec", "alec-private", s3, FakeTable())
        publish_candidate_batch([job], policy, "2026-10-13T15:00:00Z", s3, "alec-private")
        with self.assertRaises(ValueError):
            store.load("2026-10-14T15:05:00Z")
        key = ("alec-private", "batches/2026-10-13/manifest.json")
        manifest = json.loads(s3.objects[key])
        manifest["status"] = "FAILED"
        s3.objects[key] = json.dumps(manifest).encode("utf-8")
        with self.assertRaises(ValueError):
            store.load("2026-10-13T15:05:00Z")

    def test_cross_candidate_manifest_is_rejected(self):
        job, policy = inputs()
        s3 = FakeS3()
        publish_candidate_batch([job], policy, "2026-10-13T15:00:00Z", s3, "alec-private")
        store = CandidateBatchStore("hector", "alec-private", s3, FakeTable())
        with self.assertRaises(ValueError):
            store.load("2026-10-13T15:05:00Z")

    def test_partial_publish_keeps_failed_manifest_visible(self):
        job, policy = inputs()
        s3 = FakeS3(fail_on="matches.json")
        with self.assertRaises(RuntimeError):
            publish_candidate_batch([job], policy, "2026-10-13T15:00:00Z", s3, "alec-private")
        manifest = json.loads(s3.objects[("alec-private", "batches/2026-10-13/manifest.json")])
        self.assertEqual(manifest["status"], "FAILED")
        with self.assertRaises(ValueError):
            CandidateBatchStore("alec", "alec-private", s3, FakeTable()).load("2026-10-13T15:05:00Z")

    def test_stale_public_job_is_not_republished_as_new(self):
        job, policy = inputs()
        job = replace(job, retrieved_at="2026-10-12T14:00:00Z")
        s3 = FakeS3()
        with self.assertRaises(ValueError):
            publish_candidate_batch([job], policy, "2026-10-13T15:00:00Z", s3, "alec-private")
        self.assertEqual(s3.writes, [])


if __name__ == "__main__":
    unittest.main()
