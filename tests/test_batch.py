import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aji.batch import BatchLock, build_manifest, validate_batch
from aji.connectors import parse_feed


def sample_jobs():
    payload = json.loads((Path(__file__).parent / "fixtures" / "lever.json").read_text(encoding="utf-8"))
    return [job.to_dict() for job in parse_feed("lever", "acmeexample", "Acme Example", payload,
                                                "2026-10-13T14:00:00Z")]


def sample_matches(jobs):
    return [{"job_id": job["job_id"], "candidate_id": "fictional", "score": 0}
            for job in jobs]


def manifest(jobs=None, *, status="READY", generated_at="2026-10-13T14:00:00Z"):
    selected = sample_jobs() if jobs is None else jobs
    return build_manifest("fictional", "batch-20261013", selected,
                          generated_at, "2026-10-13T18:00:00Z",
                          matches=sample_matches(selected), status=status)


class BatchTests(unittest.TestCase):
    def test_ready_manifest_matches_schema_and_validates_for_same_local_day(self):
        jobs = sample_jobs()
        batch = manifest(jobs)
        schema = json.loads((Path(__file__).parents[1] / "schemas" / "batch.schema.json").read_text("utf-8"))

        self.assertEqual(set(batch), set(schema["required"]))
        self.assertEqual(batch["job_ids"], ["lever:acmeexample:lv-1"])
        self.assertTrue(batch["checksum"].startswith("sha256:"))
        validate_batch(batch, jobs, "fictional", "2026-10-13T15:00:00Z",
                       matches=sample_matches(jobs))

    def test_failed_stale_or_wrong_candidate_batch_is_rejected(self):
        jobs = sample_jobs()
        cases = [
            (manifest(jobs, status="FAILED"), "fictional", "2026-10-13T15:00:00Z"),
            (manifest(jobs, generated_at="2026-10-12T14:00:00Z"), "fictional", "2026-10-13T15:00:00Z"),
            (manifest(jobs), "other", "2026-10-13T15:00:00Z"),
            (manifest(jobs), "fictional", "2026-10-13T19:00:00Z"),
        ]

        for batch, candidate, now in cases:
            with self.subTest(candidate=candidate, now=now, status=batch["status"]):
                with self.assertRaises(ValueError):
                    validate_batch(batch, jobs, candidate, now, matches=sample_matches(jobs))

    def test_checksum_detects_modified_job_content(self):
        jobs = sample_jobs()
        batch = manifest(jobs)
        changed = [dict(jobs[0], title="Tampered title")]

        with self.assertRaises(ValueError):
            validate_batch(batch, changed, "fictional", "2026-10-13T15:00:00Z",
                           matches=sample_matches(jobs))

    def test_lock_is_idempotent_per_candidate_and_batch(self):
        locks = BatchLock()

        self.assertTrue(locks.try_acquire("alec", "batch-1"))
        self.assertFalse(locks.try_acquire("alec", "batch-1"))
        self.assertTrue(locks.try_acquire("hector", "batch-1"))


if __name__ == "__main__":
    unittest.main()
