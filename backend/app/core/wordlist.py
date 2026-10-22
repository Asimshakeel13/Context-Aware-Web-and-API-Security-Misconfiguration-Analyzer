"""Controlled wordlist for endpoint probing (spec section 18, strategy 3).

Deliberately small and defensive -- this is NOT a brute-force enumeration list.
It targets well-known sensitive paths a defender would want flagged.
"""
from __future__ import annotations

PROBE_PATHS: tuple[str, ...] = (
    "/admin",
    "/api",
    "/api/v1",
    "/api/v2",
    "/api/users",
    "/login",
    "/.env",
    "/.git/HEAD",
    "/swagger-ui.html",
    "/openapi.json",
    "/graphql",
    "/robots.txt",
    "/backup.zip",
    "/config.json",
    "/actuator/health",
)
