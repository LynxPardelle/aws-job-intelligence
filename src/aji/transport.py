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
               opener=None, sleeper=None, max_bytes: int = 2_000_000,
               max_pages: int = 1):
    """GET a documented feed; never follow redirects or submit applications."""
    if max_bytes <= 0:
        raise ValueError("max_bytes must be positive")
    if type(max_pages) is not int or not 1 <= max_pages <= 3 or \
            (source != "getonbrd" and max_pages != 1):
        raise ValueError("invalid feed page limit")
    build_feed_url(source, board)
    open_request = opener or _default_open
    sleep = sleeper or time.sleep
    jobs = []
    for page in range(1, max_pages + 1):
        url = build_feed_url(source, board, page=page)
        request = Request(url, headers={"Accept": "application/json", "User-Agent": "AWSJobIntelligence/0.1"}, method="GET")
        for attempt in range(3):
            try:
                with open_request(request, timeout=8) as response:
                    body = response.read(max_bytes + 1)
                if len(body) > max_bytes:
                    raise ValueError("ATS feed exceeds size limit")
                payload = json.loads(body.decode("utf-8"))
                page_jobs = parse_feed(source, board, company, payload, retrieved_at)
                jobs.extend(page_jobs)
                if source != "getonbrd" or len(payload["data"]) < 100:
                    return jobs
                break
            except HTTPError as error:
                if error.code not in {429, 500, 502, 503, 504} or attempt == 2:
                    raise
            except URLError:
                if attempt == 2:
                    raise
            sleep(2 ** attempt)
    return jobs
