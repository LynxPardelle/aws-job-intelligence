import io
import json
import sys
import unittest
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aji.transport import fetch_jobs


class Response:
    def __init__(self, payload):
        self.body = io.BytesIO(payload)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.body.close()

    def read(self, count):
        return self.body.read(count)


class TransportTests(unittest.TestCase):
    def test_fetch_uses_only_get_on_documented_host(self):
        payload = (Path(__file__).parent / "fixtures" / "lever.json").read_bytes()
        requests = []

        def opener(request, timeout):
            requests.append((request.full_url, request.get_method(), timeout))
            return Response(payload)

        jobs = fetch_jobs("lever", "acmeexample", "Acme Example", "2026-10-13T12:00:00Z", opener=opener)

        self.assertEqual(len(jobs), 1)
        self.assertEqual(requests, [("https://api.lever.co/v0/postings/acmeexample?mode=json", "GET", 8)])

    def test_retries_rate_limit_but_not_bad_board(self):
        payload = (Path(__file__).parent / "fixtures" / "greenhouse.json").read_bytes()
        attempts = []
        sleeps = []

        def opener(request, timeout):
            attempts.append(request.full_url)
            if len(attempts) < 3:
                raise HTTPError(request.full_url, 429, "rate limited", Message(), None)
            return Response(payload)

        jobs = fetch_jobs("greenhouse", "acmeexample", "Acme Example", "2026-10-13T12:00:00Z",
                          opener=opener, sleeper=sleeps.append)

        self.assertEqual(len(jobs), 1)
        self.assertEqual(len(attempts), 3)
        self.assertEqual(sleeps, [1, 2])
        with self.assertRaises(ValueError):
            fetch_jobs("greenhouse", "../../secrets", "Acme Example", "2026-10-13T12:00:00Z", opener=opener)
        self.assertEqual(len(attempts), 3)

    def test_rejects_oversized_feed(self):
        def opener(request, timeout):
            return Response(b"x" * 129)

        with self.assertRaises(ValueError):
            fetch_jobs("lever", "acmeexample", "Acme Example", "2026-10-13T12:00:00Z",
                       opener=opener, max_bytes=128)


if __name__ == "__main__":
    unittest.main()
