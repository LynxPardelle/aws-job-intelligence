import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aji.compensation_ledger import (list_compensation, record_advertised_salaries,
                                     record_compensation)


def advertised(candidate="fictional"):
    return {
        "candidate_id": candidate, "job_id": "greenhouse:sample:101",
        "kind": "advertised", "minimum": "6000", "maximum": "8000",
        "currency": "USD", "interval": "month", "basis": "contract",
        "source_type": "employer_posting",
        "source_ref": "https://boards.greenhouse.io/sample/jobs/101",
        "observed_at": "2026-10-20T15:00:00Z",
    }


class CompensationLedgerTests(unittest.TestCase):
    def test_idempotent_observation_keeps_original_amount_and_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "comp.sqlite3"
            self.assertTrue(record_compensation(path, advertised()))
            self.assertFalse(record_compensation(path, advertised()))
            rows = list_compensation(path, "fictional", "greenhouse:sample:101")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["minimum"], "6000")
            self.assertEqual(rows[0]["basis"], "contract")
            self.assertEqual(rows[0]["kind"], "advertised")
            self.assertEqual(rows[0]["source_type"], "employer_posting")

    def test_estimate_and_actual_need_distinct_evidence_and_never_merge(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "comp.sqlite3"
            estimated = {**advertised(), "kind": "estimated_net", "minimum": "90000",
                         "maximum": "110000", "currency": "MXN", "basis": "net",
                         "source_type": "tax_scenario", "source_ref": "private:scenario-1"}
            self.assertTrue(record_compensation(path, estimated))
            with self.assertRaises(ValueError):
                record_compensation(path, {**estimated, "kind": "actual"})
            self.assertEqual([row["kind"] for row in
                              list_compensation(path, "fictional", "greenhouse:sample:101")],
                             ["estimated_net"])

    def test_candidate_isolation_and_incomplete_salary_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "comp.sqlite3"
            record_compensation(path, advertised())
            record_compensation(path, advertised("other"))
            self.assertEqual(len(list_compensation(path, "fictional", "greenhouse:sample:101")), 1)
            self.assertEqual(len(list_compensation(path, "other", "greenhouse:sample:101")), 1)
            with self.assertRaises(ValueError):
                record_compensation(path, {**advertised(), "currency": ""})
            with self.assertRaises(ValueError):
                record_compensation(path, {**advertised(), "source_ref": "http://localhost"})

    def test_daily_public_salary_is_recorded_once_without_becoming_net(self):
        summary = {"status": "READY", "candidate_id": "fictional",
                   "generated_at": "2026-10-20T14:30:00Z", "opportunities": [{
                       "job_id": "greenhouse:sample:101",
                       "source_url": "https://boards.greenhouse.io/sample/jobs/101",
                       "salary": {"minimum": 6000, "maximum": 8000, "currency": "USD",
                                  "interval": "month", "basis": "contract"},
                   }, {"job_id": "greenhouse:sample:102", "source_url":
                       "https://boards.greenhouse.io/sample/jobs/102", "salary": None}]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "comp.sqlite3"
            self.assertEqual(record_advertised_salaries(path, summary), 1)
            self.assertEqual(record_advertised_salaries(path, summary), 0)
            row = list_compensation(path, "fictional", "greenhouse:sample:101")[0]
            self.assertEqual(row["kind"], "advertised")
            self.assertEqual(row["basis"], "contract")
            self.assertEqual(list_compensation(path, "fictional", "greenhouse:sample:102"), [])


if __name__ == "__main__":
    unittest.main()
