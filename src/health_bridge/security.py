from __future__ import annotations

import hmac
import json
import threading
import time
from collections import defaultdict, deque

from starlette.datastructures import Headers
from starlette.responses import JSONResponse

PUBLIC_PATHS = frozenset(
    {
        "/healthz",
        "/openapi.json",
        "/docs",
        "/docs/oauth2-redirect",
        "/redoc",
        "/favicon.ico",
        "/favicon.svg",
        "/apple-touch-icon.png",
    }
)


def _error_body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def extract_token(headers: Headers) -> str | None:
    auth = headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth[7:].strip()
    api_key = headers.get("x-api-key")
    return api_key.strip() if api_key else None


def is_public_path(path: str) -> bool:
    return path in PUBLIC_PATHS or path.startswith("/docs") or path == "/admin" or path.startswith("/admin/")


class TokenAuthMiddleware:
    """Require a bearer token (or X-API-Key) on every route except docs."""

    def __init__(self, app, token: str, public_paths: frozenset[str] = PUBLIC_PATHS):
        self.app = app
        self.token = token
        self.public_paths = public_paths

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        path = scope.get("path", "")
        if is_public_path(path):
            return await self.app(scope, receive, send)

        token = extract_token(Headers(scope=scope))
        if not token or not self.token or not hmac.compare_digest(token, self.token):
            response = JSONResponse(
                _error_body("unauthorized", "A valid bearer token is required."),
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )
            return await response(scope, receive, send)

        return await self.app(scope, receive, send)


class RateLimiter:
    """Small in-process sliding-window limiter; plenty for a personal bridge."""

    def __init__(self, per_minute: int):
        self.per_minute = max(1, per_minute)
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        window = 60.0
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > window:
                hits.popleft()
            if len(hits) >= self.per_minute:
                return False
            hits.append(now)
            return True


class RateLimitMiddleware:
    def __init__(self, app, limiter: RateLimiter, key: str = "bridge"):
        self.app = app
        self.limiter = limiter
        self.key = key

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        path = scope.get("path", "")
        if is_public_path(path):
            return await self.app(scope, receive, send)

        if not self.limiter.allow(self.key):
            response = JSONResponse(
                _error_body("rate_limited", "Too many requests; slow down."),
                status_code=429,
                headers={"Retry-After": "60"},
            )
            return await response(scope, receive, send)

        return await self.app(scope, receive, send)
