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

    def test_getonbrd_uses_https_get_and_stops_on_short_page(self):
        payload = (Path(__file__).parent / "fixtures" / "getonbrd.json").read_bytes()
        requests = []

        def opener(request, timeout):
            requests.append((request.full_url, request.get_method(), timeout))
            return Response(payload)

        jobs = fetch_jobs("getonbrd", "programming", "Get on Board",
                          "2026-10-13T12:00:00Z", opener=opener, max_pages=3)
        self.assertEqual(len(jobs), 2)
        self.assertEqual(requests, [
            ("https://www.getonbrd.com/api/v0/categories/programming/jobs"
             "?per_page=100&expand%5B%5D=company&page=1", "GET", 8)
        ])

    def test_getonbrd_pagination_has_fixed_cap(self):
        sample = json.loads((Path(__file__).parent / "fixtures" / "getonbrd.json").read_text("utf-8"))["data"][0]
        first = []
        for index in range(100):
            item = json.loads(json.dumps(sample))
            item["id"] = f"sample-{index}"
            item["links"]["public_url"] = f"https://www.getonbrd.com/jobs/sample-{index}"
            first.append(item)
        requests = []

        def opener(request, timeout):
            requests.append(request.full_url)
            payload = {"data": first if len(requests) == 1 else []}
            return Response(json.dumps(payload).encode("utf-8"))

        jobs = fetch_jobs("getonbrd", "programming", "Get on Board",
                          "2026-10-13T12:00:00Z", opener=opener, max_pages=2)
        self.assertEqual(len(jobs), 100)
        self.assertEqual(len(requests), 2)
        self.assertTrue(requests[-1].endswith("page=2"))
        with self.assertRaises(ValueError):
            fetch_jobs("getonbrd", "programming", "Get on Board",
                       "2026-10-13T12:00:00Z", opener=opener, max_pages=4)
        self.assertEqual(len(requests), 2)


if __name__ == "__main__":
    unittest.main()
