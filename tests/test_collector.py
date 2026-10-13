import json
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aji.connectors import parse_feed
from aji.lambda_handler import collect_once, handler


def sample_jobs():
    payload = json.loads((Path(__file__).parent / "fixtures" / "greenhouse.json").read_text("utf-8"))
    return parse_feed("greenhouse", "acmeexample", "Acme Example", payload, "2026-10-13T14:00:00Z")


class CollectorTests(unittest.TestCase):
    def test_disabled_handler_has_no_external_effect(self):
        with patch.dict(os.environ, {"AJI_ENABLED": "false"}):
            result = handler({"sources": [{"source": "evil"}]}, None)

        self.assertEqual(result, {"status": "DISABLED", "jobs_written": 0})

    def test_collect_once_writes_only_deduplicated_public_jobs(self):
        calls = []
        written = []

        def fetcher(source, board, company, retrieved_at):
            calls.append((source, board, company))
            return sample_jobs() + sample_jobs()

        result = collect_once([{"source": "greenhouse", "board": "acmeexample",
                                "company": "Acme Example", "enabled": True}],
                              "2026-10-13T14:00:00Z", fetcher=fetcher,
                              writer=written.append, max_sources=10)

        self.assertEqual(result, {"status": "OK", "jobs_written": 1, "sources": 1})
        self.assertEqual(calls, [("greenhouse", "acmeexample", "Acme Example")])
        self.assertEqual(written[0]["job_id"], "greenhouse:acmeexample:101")
        self.assertGreater(written[0]["expires_at"], 0)
        self.assertNotIn("candidate_id", written[0])

    def test_invalid_source_stops_before_fetch_or_write(self):
        calls = []
        with self.assertRaises(ValueError):
            collect_once([{"source": "greenhouse", "board": "../../secret",
                           "company": "Acme Example", "enabled": True}],
                         "2026-10-13T14:00:00Z", fetcher=lambda *_: calls.append(1),
                         writer=lambda _: calls.append(2), max_sources=10)
        self.assertEqual(calls, [])

    def test_enabled_handler_uses_only_configured_table_with_fake_aws_client(self):
        writes = []
        fake_table = SimpleNamespace(put_item=lambda **kwargs: writes.append(kwargs))
        fake_boto3 = SimpleNamespace(resource=lambda service: SimpleNamespace(
            Table=lambda name: fake_table if service == "dynamodb" and name == "aji-test" else None))
        environment = {
            "AJI_ENABLED": "true", "AJI_JOBS_TABLE": "aji-test", "AJI_MAX_SOURCES": "10",
            "AJI_SOURCES_JSON": json.dumps([{"source": "greenhouse", "board": "acmeexample",
                                            "company": "Acme Example", "enabled": True}]),
        }
        with patch.dict(os.environ, environment), patch.dict(sys.modules, {"boto3": fake_boto3}), \
                patch("aji.lambda_handler.fetch_jobs", return_value=sample_jobs()):
            result = handler({}, None)

        self.assertEqual(result, {"status": "OK", "jobs_written": 1, "sources": 1})
        self.assertEqual(writes[0]["Item"]["job_id"], "greenhouse:acmeexample:101")
        self.assertNotIn("candidate_id", writes[0]["Item"])


if __name__ == "__main__":
    unittest.main()
