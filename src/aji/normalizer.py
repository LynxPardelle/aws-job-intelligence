"""Pure normalization helpers for untrusted ATS data."""

import html
import ipaddress
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urlsplit


class _TextOnly(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def plain_text(value: str | None) -> str:
    parser = _TextOnly()
    parser.feed(html.unescape(value or ""))
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()


def utc_timestamp(value: str | int | float | None) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        timestamp = datetime.fromtimestamp(value / 1000, timezone.utc)
    else:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            raise ValueError("timestamp requires timezone")
    return timestamp.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def public_https_url(value: str) -> str:
    parts = urlsplit(value)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
        raise ValueError("public HTTPS URL required")
    if parts.port not in (None, 443):
        raise ValueError("nonstandard port rejected")
    hostname = parts.hostname.lower().rstrip(".")
    if hostname == "localhost" or hostname.endswith(".localhost") or "." not in hostname:
        raise ValueError("non-public host rejected")
    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        raise ValueError("IP literal rejected")
    return value


def explicit_seniority(title: str, level: str | None = None) -> str | None:
    text = (level or title).lower()
    for value, pattern in (
        ("junior", r"\b(junior|jr)\b"),
        ("mid", r"\b(mid|intermediate)\b"),
        ("senior", r"\b(senior|sr)\b"),
        ("staff", r"\bstaff\b"),
        ("principal", r"\bprincipal\b"),
    ):
        if re.search(pattern, text):
            return value
    return None


def explicit_modality(value: str | None) -> str:
    normalized = (value or "").strip().lower().replace("-", "")
    return {"remote": "remote", "hybrid": "hybrid", "onsite": "onsite"}.get(normalized, "unknown")
