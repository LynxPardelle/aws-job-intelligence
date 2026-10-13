"""Bounded read-only transport for public ATS feeds."""

import json
import time
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .connectors import build_feed_url, parse_feed


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        return None


def _default_open(request: Request, timeout: int):
    return build_opener(_NoRedirect()).open(request, timeout=timeout)


def fetch_jobs(source: str, board: str, company: str, retrieved_at: str, *,
               opener=None, sleeper=None, max_bytes: int = 2_000_000):
    """GET a documented feed; never follow redirects or submit applications."""
    url = build_feed_url(source, board)
    if max_bytes <= 0:
        raise ValueError("max_bytes must be positive")
    open_request = opener or _default_open
    sleep = sleeper or time.sleep
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "AWSJobIntelligence/0.1"}, method="GET")

    for attempt in range(3):
        try:
            with open_request(request, timeout=8) as response:
                body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                raise ValueError("ATS feed exceeds size limit")
            return parse_feed(source, board, company, json.loads(body.decode("utf-8")), retrieved_at)
        except HTTPError as error:
            if error.code not in {429, 500, 502, 503, 504} or attempt == 2:
                raise
        except URLError:
            if attempt == 2:
                raise
        sleep(2 ** attempt)
    raise RuntimeError("unreachable")
