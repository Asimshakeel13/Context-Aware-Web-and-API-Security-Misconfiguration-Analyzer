"""Safe async HTTP engine (spec section 17).

Wraps httpx to collect everything the scanner needs from a response while
enforcing safety limits: timeouts, a response-size cap, a redirect cap with
SSRF re-validation on every hop, and graceful handling of every network error
(a bad target must never crash the scanner).

Redirects are followed *manually* (httpx auto-redirect is off) so each hop's
destination can be SSRF-checked before we connect to it.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import httpx

from app.config import settings
from app.utils.logging import get_logger
from app.utils.security import SSRFError, validate_url_ssrf

logger = get_logger(__name__)


@dataclass
class HttpResult:
    """Everything collected from a single fetch."""

    requested_url: str
    final_url: str
    method: str
    status_code: int | None = None
    headers: dict[str, str] = field(default_factory=dict)
    cookies: list[dict] = field(default_factory=list)
    body: str = ""
    content_type: str | None = None
    content_length: int | None = None
    response_time: float | None = None
    redirect_chain: list[str] = field(default_factory=list)
    set_cookie_headers: list[str] = field(default_factory=list)
    error: str | None = None
    truncated: bool = False

    @property
    def ok(self) -> bool:
        return self.error is None and self.status_code is not None


class HttpEngine:
    """Reusable async HTTP engine backed by one httpx client."""

    def __init__(self, *, allow_private: bool = False) -> None:
        # allow_private is for the test-suite only (reach a local mock server).
        self._allow_private = allow_private
        limits = httpx.Limits(
            max_connections=settings.MAX_CONCURRENT_REQUESTS,
            max_keepalive_connections=settings.MAX_CONCURRENT_REQUESTS,
        )
        self._client = httpx.AsyncClient(
            follow_redirects=False,           # we follow manually + re-check SSRF
            timeout=settings.REQUEST_TIMEOUT,
            limits=limits,
            headers={"User-Agent": settings.USER_AGENT},
            verify=True,
        )

    async def __aenter__(self) -> "HttpEngine":
        return self

    async def __aexit__(self, *exc) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def fetch(self, url: str, method: str = "GET",
                    extra_headers: dict[str, str] | None = None) -> HttpResult:
        """Fetch ``url`` safely, following redirects with SSRF re-checks."""
        result = HttpResult(requested_url=url, final_url=url, method=method)
        start = time.perf_counter()
        current = url
        chain: list[str] = []

        try:
            for _hop in range(settings.MAX_REDIRECTS + 1):
                # SSRF gate on every hop (initial + each redirect target).
                try:
                    validate_url_ssrf(current, allow_private=self._allow_private)
                except SSRFError as exc:
                    result.error = f"SSRF blocked: {exc.reason}"
                    result.response_time = time.perf_counter() - start
                    logger.warning("SSRF blocked %s: %s", current, exc.reason)
                    return result

                resp = await self._request_capped(current, method, extra_headers)
                result.status_code = resp.status_code
                result.final_url = current

                # Redirect handling.
                if resp.status_code in (301, 302, 303, 307, 308):
                    location = resp.headers.get("location")
                    if not location:
                        break
                    nxt = str(httpx.URL(current).join(location))
                    chain.append(nxt)
                    current = nxt
                    # 303 -> subsequent request should be GET.
                    if resp.status_code == 303:
                        method = "GET"
                    continue

                # Terminal response -- capture it.
                self._capture(result, resp)
                break
            else:
                result.error = "Too many redirects."

        except httpx.TimeoutException:
            result.error = "Request timed out."
        except httpx.ConnectError as exc:
            result.error = f"Connection error: {exc}"
        except httpx.TooManyRedirects:
            result.error = "Too many redirects."
        except httpx.HTTPError as exc:
            result.error = f"HTTP error: {exc}"
        except Exception as exc:  # noqa: BLE001 - engine must never propagate
            result.error = f"Unexpected error: {exc}"
            logger.exception("engine unexpected error for %s", url)

        result.redirect_chain = chain
        result.response_time = time.perf_counter() - start
        return result

    async def _request_capped(self, url: str, method: str,
                              extra_headers: dict[str, str] | None = None) -> httpx.Response:
        """Issue a streamed request and read at most MAX_RESPONSE_SIZE bytes."""
        req = self._client.build_request(method, url, headers=extra_headers)
        resp = await self._client.send(req, stream=True)
        try:
            chunks: list[bytes] = []
            total = 0
            truncated = False
            async for chunk in resp.aiter_bytes():
                total += len(chunk)
                if total > settings.MAX_RESPONSE_SIZE:
                    truncated = True
                    break
                chunks.append(chunk)
            resp._cawasma_body = b"".join(chunks)  # type: ignore[attr-defined]
            resp._cawasma_truncated = truncated      # type: ignore[attr-defined]
        finally:
            await resp.aclose()
        return resp

    @staticmethod
    def _capture(result: HttpResult, resp: httpx.Response) -> None:
        body_bytes: bytes = getattr(resp, "_cawasma_body", b"")
        result.truncated = getattr(resp, "_cawasma_truncated", False)
        result.headers = {k: v for k, v in resp.headers.items()}
        result.content_type = resp.headers.get("content-type")
        result.content_length = len(body_bytes)
        result.body = body_bytes.decode("utf-8", errors="replace")
        result.set_cookie_headers = resp.headers.get_list("set-cookie")
        # Cookies (metadata only; value length captured, not the value).
        for name, value in resp.cookies.items():
            result.cookies.append({"name": name, "value_length": len(value or "")})
