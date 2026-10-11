"""Target URL validation (spec section 15).

A target must be a well-formed, HTTPS URL. HTTP-only targets are rejected. This
module does *not* do SSRF checks -- that is ``security.py`` -- it only validates
the shape of the URL. Keeping the two concerns separate makes both testable.
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse


class InvalidTargetError(ValueError):
    """Raised when a target URL is malformed or not permitted."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


@dataclass(frozen=True)
class ParsedTarget:
    url: str          # normalized URL (no fragment)
    scheme: str
    host: str
    port: int
    path: str


def validate_target_url(raw: str, *, require_https: bool = True) -> ParsedTarget:
    """Validate and normalize a target URL.

    Rejects: empty/malformed input, non-http(s) schemes, http when https is
    required, missing host, and out-of-range ports. Fragments are stripped.
    """
    if not raw or not isinstance(raw, str):
        raise InvalidTargetError("Target URL is empty.")

    raw = raw.strip()
    if len(raw) > 2048:
        raise InvalidTargetError("Target URL is too long.")

    parsed = urlparse(raw)

    if parsed.scheme not in ("http", "https"):
        raise InvalidTargetError(
            f"Unsupported scheme '{parsed.scheme or 'none'}'. Use https://."
        )
    if require_https and parsed.scheme != "https":
        raise InvalidTargetError("Only HTTPS targets are allowed.")

    if not parsed.hostname:
        raise InvalidTargetError("Target URL has no host.")

    # Port: default by scheme, else must be 1-65535.
    try:
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
    except ValueError:
        raise InvalidTargetError("Target URL has an invalid port.") from None
    if not (1 <= port <= 65535):
        raise InvalidTargetError("Target port is out of range.")

    path = parsed.path or "/"

    # Rebuild without fragment; keep query.
    normalized = urlunparse(
        (parsed.scheme, parsed.netloc, path, parsed.params, parsed.query, "")
    )

    return ParsedTarget(
        url=normalized,
        scheme=parsed.scheme,
        host=parsed.hostname,
        port=port,
        path=path,
    )


def same_origin(url_a: str, url_b: str) -> bool:
    """True if two URLs share scheme, host, and port (same-origin)."""
    a, b = urlparse(url_a), urlparse(url_b)
    a_port = a.port or (443 if a.scheme == "https" else 80)
    b_port = b.port or (443 if b.scheme == "https" else 80)
    return (a.scheme, a.hostname, a_port) == (b.scheme, b.hostname, b_port)
