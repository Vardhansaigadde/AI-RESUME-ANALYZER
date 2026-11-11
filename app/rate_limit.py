"""Per-client rate limiting for the analysis endpoints.

A small in-memory sliding-window limiter (one process, no external store),
which is enough for the single free-tier Render instance this API runs on.
Each POST under /api counts against the client's IP; when a client exceeds
`limit` requests within `window_seconds`, it gets HTTP 429 with Retry-After.
The client IP is read by `client_ip`, not from X-Forwarded-For's leftmost
entry: on Render, Cloudflare sits in front of the app and only *appends* to
X-Forwarded-For, so a client could put any IP first and dodge the limit.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
import math
import time

from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

# Forget clients that have been idle this long, to keep memory bounded
_IDLE_PRUNE_SECONDS = 600


def _header(scope: Scope, name: bytes) -> str:
    for key, value in scope.get("headers", []):
        if key == name:
            return value.decode("latin-1").strip()
    return ""


def client_ip(scope: Scope) -> str:
    """The visitor's IP, in a way the visitor can't fake.

    Render puts Cloudflare in front of every service. Cloudflare sets
    CF-Connecting-IP to the address that connected to it (overwriting anything
    the client sent), and appends that address to X-Forwarded-For, after which
    Cloudflare's own edge IP is appended. So the order of trust is:
    CF-Connecting-IP, then the second X-Forwarded-For entry from the right,
    then the socket address (local runs and tests, where there is no proxy).
    """
    if ip := _header(scope, b"cf-connecting-ip"):
        return ip
    forwarded = [part.strip() for part in _header(scope, b"x-forwarded-for").split(",") if part.strip()]
    if len(forwarded) >= 2:
        return forwarded[-2]
    client = scope.get("client")
    return client[0] if client else "unknown"


class RateLimitMiddleware:
    """Limit POST requests under `path_prefix` per client IP.

    Args:
        app: The wrapped ASGI app.
        limit: Requests allowed per window per client. 0 or less disables limiting.
        window_seconds: Length of the sliding window.
        path_prefix: Only requests whose path starts with this are counted.
        clock: Time source (monotonic seconds); injectable for tests.
    """

    def __init__(
        self,
        app: ASGIApp,
        limit: int,
        window_seconds: float = 60.0,
        path_prefix: str = "/api/",
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.app = app
        self.limit = limit
        self.window = window_seconds
        self.path_prefix = path_prefix
        self.clock = clock
        self._hits: dict[str, deque[float]] = {}
        self._last_prune = clock()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            self.limit <= 0
            or scope["type"] != "http"
            or scope.get("method") != "POST"
            or not scope.get("path", "").startswith(self.path_prefix)
        ):
            await self.app(scope, receive, send)
            return

        now = self.clock()
        self._prune(now)
        key = client_ip(scope)
        hits = self._hits.setdefault(key, deque())
        while hits and hits[0] <= now - self.window:
            hits.popleft()

        if len(hits) >= self.limit:
            retry_after = max(1, math.ceil(hits[0] + self.window - now))
            response = JSONResponse(
                status_code=429,
                content={
                    "detail": (f"Too many analyses in a short time. Please wait {retry_after} seconds and try again.")
                },
                headers={"Retry-After": str(retry_after)},
            )
            await response(scope, receive, send)
            return

        hits.append(now)
        await self.app(scope, receive, send)

    def _prune(self, now: float) -> None:
        if now - self._last_prune < _IDLE_PRUNE_SECONDS:
            return
        self._last_prune = now
        stale = [k for k, q in self._hits.items() if not q or q[-1] <= now - _IDLE_PRUNE_SECONDS]
        for k in stale:
            del self._hits[k]
