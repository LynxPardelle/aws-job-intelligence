"""The live pull reports absent or invalid batches without leaking AWS details."""

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("run_alec_pull", ROOT / "scripts" / "run-alec-pull.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AwsError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.response = {"Error": {"Code": code, "Message": message}}


class PullErrorTests(unittest.TestCase):
    def test_inaccessible_or_missing_batch_has_safe_nonzero_summary(self) -> None:
        error = AwsError("AccessDenied", "arn:aws:s3:::private-bucket secret-value")
        with patch.object(MODULE, "inspect_daily_batch", side_effect=error):
            summary, exit_code = MODULE.read_batch_summary(object(), "2026-10-13T15:00:00Z", False)
        self.assertEqual(exit_code, 2)
        self.assertEqual(summary["status"], "ERROR")
        self.assertEqual(summary["error_code"], "BATCH_UNAVAILABLE_OR_DENIED")
        self.assertEqual(summary["jobs_found"], 0)
        self.assertNotIn("private-bucket", str(summary))
        self.assertNotIn("secret-value", str(summary))

    def test_invalid_or_stale_batch_has_safe_nonzero_summary(self) -> None:
        with patch.object(MODULE, "inspect_daily_batch", side_effect=ValueError("sensitive stale data")):
            summary, exit_code = MODULE.read_batch_summary(object(), "2026-10-13T15:00:00Z", False)
        self.assertEqual(exit_code, 2)
        self.assertEqual(summary["error_code"], "BATCH_INVALID_OR_STALE")
        self.assertNotIn("sensitive stale data", str(summary))


if __name__ == "__main__":
    unittest.main()
