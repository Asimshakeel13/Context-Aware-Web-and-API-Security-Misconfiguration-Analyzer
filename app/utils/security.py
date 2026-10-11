"""SSRF protection (spec section 16).

The scanner fetches user-supplied URLs, so it must never be tricked into
reaching internal infrastructure. We resolve the hostname to its actual IP(s)
and reject any that are private, loopback, link-local (this covers cloud
metadata at 169.254.169.254), reserved, or multicast -- for both IPv4 and IPv6.

Because DNS can resolve differently between the check and the connection
(DNS rebinding), callers should validate again on every redirect hop, which the
HTTP engine does.
"""
from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlparse


class SSRFError(Exception):
    """Raised when a target resolves to a disallowed address."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


@dataclass(frozen=True)
class ResolvedTarget:
    host: str
    ips: tuple[str, ...]


def _ip_is_disallowed(ip: ipaddress._BaseAddress) -> str | None:
    """Return a reason string if the IP must be blocked, else None."""
    if ip.is_loopback:
        return "loopback address"
    if ip.is_private:
        return "private address"
    if ip.is_link_local:
        return "link-local address (includes cloud metadata)"
    if ip.is_reserved:
        return "reserved address"
    if ip.is_multicast:
        return "multicast address"
    if ip.is_unspecified:
        return "unspecified address (0.0.0.0/::)"
    return None


def validate_ip(ip_str: str) -> None:
    """Raise SSRFError if a single IP string is disallowed."""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        raise SSRFError(f"Not a valid IP address: {ip_str}") from None
    reason = _ip_is_disallowed(ip)
    if reason:
        raise SSRFError(f"Blocked {ip_str}: {reason}.")


def resolve_and_validate(host: str, port: int = 443, *, allow_private: bool = False
                         ) -> ResolvedTarget:
    """Resolve ``host`` and validate every resulting IP.

    ``allow_private`` is used ONLY by the test-suite to reach a local mock
    server; production callers always leave it False.
    """
    if not host:
        raise SSRFError("Empty host.")

    # A hostname that is itself a literal internal name.
    lowered = host.lower()
    if lowered in {"localhost", "localhost.localdomain"} and not allow_private:
        raise SSRFError("Blocked hostname 'localhost'.")

    try:
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise SSRFError(f"DNS resolution failed for {host}: {exc}") from None

    ips = tuple({info[4][0] for info in infos})
    if not ips:
        raise SSRFError(f"No addresses resolved for {host}.")

    if not allow_private:
        for ip in ips:
            validate_ip(ip)

    return ResolvedTarget(host=host, ips=ips)


def validate_url_ssrf(url: str, *, allow_private: bool = False) -> ResolvedTarget:
    """Parse a URL and run the SSRF resolution check on its host."""
    parsed = urlparse(url)
    if not parsed.hostname:
        raise SSRFError("URL has no host.")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return resolve_and_validate(parsed.hostname, port, allow_private=allow_private)
