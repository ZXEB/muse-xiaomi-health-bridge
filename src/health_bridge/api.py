from __future__ import annotations

from fastapi import FastAPI, Query
from fastapi.responses import PlainTextResponse, RedirectResponse, Response

from . import __version__
from .admin import create_admin_router
from .security import RateLimiter, RateLimitMiddleware, TokenAuthMiddleware
from .service import HealthService
from .source import AuthExpiredError, UpstreamError

DESCRIPTION = """
Read-only bridge between Xiaomi Mi Fitness (小米运动健康) and Meta Muse.

All `/v1` endpoints require `Authorization: Bearer <BRIDGE_TOKEN>` (or `X-API-Key`).
Dates are local calendar days in the configured time zone (default Asia/Shanghai).
"""

DOMAIN_ROUTES = (
    "sleep",
    "steps",
    "heart-rate",
    "spo2",
    "stress",
    "weight",
    "activity",
    "calories",
)


def _error(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def create_rest_app(service: HealthService, token: str | None = None):
    app = FastAPI(
        title="Xiaomi Health Bridge",
        version=__version__,
        description=DESCRIPTION,
        docs_url="/docs",
        redoc_url=None,
        openapi_url="/openapi.json",
    )

    @app.exception_handler(AuthExpiredError)
    async def _auth_expired(_request, exc: AuthExpiredError):
        return _json(503, _error("auth_expired", str(exc)))

    @app.exception_handler(UpstreamError)
    async def _upstream(_request, exc: UpstreamError):
        return _json(502, _error("upstream_error", str(exc)))

    @app.exception_handler(ValueError)
    async def _bad_request(_request, exc: ValueError):
        return _json(400, _error("bad_request", str(exc)))

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    @app.get("/favicon.svg", include_in_schema=False)
    def favicon():
        return Response(
            content=(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">'
                '<rect width="48" height="48" rx="12" fill="#1b2740"/>'
                '<path d="M14 30V20l6 6 4-9 4 9 6-6v10" fill="none" stroke="#4f8cff" '
                'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>'
                '<circle cx="31" cy="17" r="2.4" fill="#34d399"/></svg>'
            ),
            media_type="image/svg+xml",
            headers={"Cache-Control": "public, max-age=86400"},
        )

    @app.get("/favicon.ico", include_in_schema=False)
    def favicon_ico():
        return RedirectResponse("/favicon.svg", status_code=307)

    @app.get("/v1/status")
    def status():
        return service.status()

    @app.get("/v1/summary")
    def summary(
        days: int = Query(7, ge=1, le=92),
        fmt: str = Query("json", alias="format", pattern="^(json|md)$"),
    ):
        data = service.summary(days)
        if fmt == "md":
            return PlainTextResponse(data["markdown"], media_type="text/markdown; charset=utf-8")
        return data

    @app.get("/v1/metrics")
    def metrics(
        start: str | None = Query(None, alias="from"),
        end: str | None = Query(None, alias="to"),
        fields: str | None = None,
    ):
        return service.metrics(start, end, fields)

    @app.get("/v1/workouts")
    def workouts(
        start: str | None = Query(None, alias="from"),
        end: str | None = Query(None, alias="to"),
    ):
        return service.workouts(start, end)

    def _make_domain_route(domain: str):
        def _route(
            start: str | None = Query(None, alias="from"),
            end: str | None = Query(None, alias="to"),
        ):
            return service.domain(domain, start, end)

        return _route

    for domain in DOMAIN_ROUTES:
        app.add_api_route(
            f"/v1/{domain}",
            _make_domain_route(domain),
            methods=["GET"],
            name=f"get_{domain.replace('-', '_')}",
        )

    @app.post("/v1/sync")
    def sync(days: int = Query(7, ge=1, le=92)):
        return service.sync(days)

    @app.get("/")
    def root():
        return {"name": "xiaomi-health-bridge", "version": __version__, "docs": "/docs", "admin": "/admin"}

    app.include_router(create_admin_router(service))

    inner = TokenAuthMiddleware(
        app,
        token if token is not None else service.settings.bridge_token,
    )
    limiter = RateLimiter(service.settings.rate_limit_per_min)
    return RateLimitMiddleware(inner, limiter)


def _json(status_code: int, payload: dict):
    from fastapi.responses import JSONResponse

    return JSONResponse(payload, status_code=status_code)
