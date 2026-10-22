"""Endpoint discovery crawler (spec section 18).

Four strategies, all bounded by same-origin, MAX_CRAWL_DEPTH, and MAX_ENDPOINTS:

  1. HTML extraction   -- <a href>, <form action> (+ method), <script src>
  2. JavaScript scan   -- fetch()/axios/baseURL and /api/... paths in JS
  3. Wordlist probing  -- a small controlled list of sensitive paths
  4. Recursive crawl   -- BFS to depth<=2, visited-set dedup, same origin

The crawler is decoupled from the database: it returns dataclasses that the
service layer persists later.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

from app.config import settings
from app.core.engine import HttpEngine, HttpResult
from app.core.wordlist import PROBE_PATHS
from app.db.models.enums import DiscoveryMethod
from app.utils.logging import get_logger
from app.utils.validators import same_origin

logger = get_logger(__name__)

# JS endpoint-ish patterns (strategy 2).
_JS_PATTERNS = [
    re.compile(r"""fetch\(\s*['"]([^'"]+)['"]"""),
    re.compile(r"""axios\.(?:get|post|put|delete|patch)\(\s*['"]([^'"]+)['"]"""),
    re.compile(r"""baseURL\s*[:=]\s*['"]([^'"]+)['"]"""),
    re.compile(r"""['"](/api/[A-Za-z0-9_\-/]+)['"]"""),
]


@dataclass
class DiscoveredEndpoint:
    url: str
    path: str
    method: str
    discovered_by: DiscoveryMethod
    status_code: int | None = None
    content_type: str | None = None
    response_time: float | None = None


def _normalize(url: str) -> str:
    """Drop fragment; keep scheme/host/path/query for dedup."""
    p = urlparse(url)
    return urlunparse((p.scheme, p.netloc, p.path or "/", p.params, p.query, ""))


class Crawler:
    def __init__(self, engine: HttpEngine) -> None:
        self._engine = engine
        self._seen: set[tuple[str, str]] = set()  # (url, method)
        self._results: list[DiscoveredEndpoint] = []

    def _add(self, url: str, method: str, how: DiscoveryMethod,
             resp: HttpResult | None = None) -> bool:
        key = (_normalize(url), method.upper())
        if key in self._seen:
            return False
        if len(self._results) >= settings.MAX_ENDPOINTS:
            return False
        self._seen.add(key)
        ep = DiscoveredEndpoint(
            url=_normalize(url),
            path=urlparse(url).path or "/",
            method=method.upper(),
            discovered_by=how,
        )
        if resp is not None:
            ep.status_code = resp.status_code
            ep.content_type = resp.content_type
            ep.response_time = resp.response_time
        self._results.append(ep)
        return True

    async def crawl(self, seed_url: str) -> list[DiscoveredEndpoint]:
        """Run all four strategies starting from ``seed_url``."""
        seed = _normalize(seed_url)
        self._add(seed, "GET", DiscoveryMethod.SEED)

        # BFS queue of (url, depth) for strategies 1, 2, 4.
        queue: list[tuple[str, int]] = [(seed, 0)]
        visited: set[str] = set()

        while queue and len(self._results) < settings.MAX_ENDPOINTS:
            url, depth = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)

            resp = await self._engine.fetch(url)
            if not resp.ok:
                continue

            ctype = (resp.content_type or "").lower()
            if "html" in ctype:
                links = self._extract_html(url, resp.body)
                for link, method, how in links:
                    if same_origin(seed, link):
                        added = self._add(link, method, how)
                        if added and depth < settings.MAX_CRAWL_DEPTH:
                            if method == "GET":
                                queue.append((_normalize(link), depth + 1))
            # Strategy 2: JS scan (inline + referenced already added as endpoints)
            if "javascript" in ctype or "html" in ctype:
                for link in self._extract_js(url, resp.body):
                    if same_origin(seed, link):
                        self._add(link, "GET", DiscoveryMethod.JAVASCRIPT)

        # Strategy 3: wordlist probing (bounded).
        await self._probe_wordlist(seed)

        logger.info("crawler discovered %d endpoints", len(self._results))
        return self._results

    def _extract_html(self, base: str, html: str
                      ) -> list[tuple[str, str, DiscoveryMethod]]:
        out: list[tuple[str, str, DiscoveryMethod]] = []
        try:
            soup = BeautifulSoup(html, "html.parser")
        except Exception:  # noqa: BLE001 - malformed HTML must not crash
            return out
        for a in soup.find_all("a", href=True):
            out.append((urljoin(base, a["href"]), "GET", DiscoveryMethod.HTML))
        for form in soup.find_all("form"):
            action = form.get("action") or base
            method = (form.get("method") or "GET").upper()
            out.append((urljoin(base, action), method, DiscoveryMethod.HTML))
        for script in soup.find_all("script", src=True):
            out.append((urljoin(base, script["src"]), "GET", DiscoveryMethod.HTML))
        return out

    def _extract_js(self, base: str, text: str) -> list[str]:
        found: set[str] = set()
        for pattern in _JS_PATTERNS:
            for m in pattern.findall(text):
                if m.startswith(("http://", "https://", "/")):
                    found.add(urljoin(base, m))
        return list(found)

    async def _probe_wordlist(self, seed: str) -> None:
        root = f"{urlparse(seed).scheme}://{urlparse(seed).netloc}"
        for path in PROBE_PATHS:
            if len(self._results) >= settings.MAX_ENDPOINTS:
                break
            url = root + path
            if (_normalize(url), "GET") in self._seen:
                continue
            resp = await self._engine.fetch(url, method="GET")
            # Record only paths that exist (not 404) to avoid noise.
            if resp.ok and resp.status_code not in (404, 410):
                self._add(url, "GET", DiscoveryMethod.WORDLIST, resp)
