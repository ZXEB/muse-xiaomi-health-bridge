from __future__ import annotations

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

from .security import RateLimiter, RateLimitMiddleware, TokenAuthMiddleware
from .service import HealthService

INSTRUCTIONS = """
Read-only access to the user's Xiaomi Mi Fitness (小米运动健康) data.

Use these tools whenever the user asks about their sleep, steps, heart rate,
blood oxygen (SpO2), stress, weight, calories or workouts. Dates are local
calendar days (default Asia/Shanghai) and every range is inclusive.

Start with get_daily_summary for a quick overview, then drill down with the
per-domain tools. Data comes from the Xiaomi cloud and can lag by up to a day;
the payload's "notes" field says when something is missing or incomplete.
"""


def _wrap(fn):
    def _inner(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - surface a readable tool error
            raise RuntimeError(str(exc)) from exc

    return _inner


def create_mcp_app(service: HealthService, token: str | None = None):
    mcp = MCPServer("xiaomi-health", instructions=INSTRUCTIONS)

    @mcp.tool(description="Bridge status: time zone, last sync, session health, row counts.")
    def health_status() -> dict:
        return _wrap(service.status)()

    @mcp.tool(description="Compact health summary for the last N days (1-92), with Markdown.")
    def get_daily_summary(days: int = 7) -> dict:
        return _wrap(service.summary)(days)

    @mcp.tool(
        description="Daily metrics between two dates (YYYY-MM-DD, inclusive). "
        "Optionally a comma-separated fields list."
    )
    def get_daily_metrics(
        start: str | None = None,
        end: str | None = None,
        fields: str | None = None,
    ) -> dict:
        return _wrap(service.metrics)(start, end, fields)

    @mcp.tool(description="Sleep per day: total, deep, light, REM, awake minutes, start/end.")
    def get_sleep(start: str | None = None, end: str | None = None) -> dict:
        return _wrap(service.domain)("sleep", start, end)

    @mcp.tool(description="Steps and distance per day.")
    def get_steps(start: str | None = None, end: str | None = None) -> dict:
        return _wrap(service.domain)("steps", start, end)

    @mcp.tool(description="Heart rate per day: average, minimum, maximum, resting.")
    def get_heart_rate_daily(start: str | None = None, end: str | None = None) -> dict:
        return _wrap(service.domain)("heart-rate", start, end)

    @mcp.tool(description="Blood oxygen (SpO2) per day: average, minimum, maximum.")
    def get_spo2_daily(start: str | None = None, end: str | None = None) -> dict:
        return _wrap(service.domain)("spo2", start, end)

    @mcp.tool(description="Stress level per day, with minutes in each stress band.")
    def get_stress_daily(start: str | None = None, end: str | None = None) -> dict:
        return _wrap(service.domain)("stress", start, end)

    @mcp.tool(description="Weight and BMI entries per day.")
    def get_weight(start: str | None = None, end: str | None = None) -> dict:
        return _wrap(service.domain)("weight", start, end)

    @mcp.tool(description="Calories per day: resting, active, intake, total.")
    def get_calories(start: str | None = None, end: str | None = None) -> dict:
        return _wrap(service.domain)("calories", start, end)

    @mcp.tool(description="Workouts: start/end, sport, duration, distance, calories, heart rate.")
    def get_workouts(start: str | None = None, end: str | None = None) -> dict:
        return _wrap(service.workouts)(start, end)

    @mcp.tool(description="Sync the last N days from the Xiaomi cloud now (1-92).")
    def sync_now(days: int = 7) -> dict:
        return _wrap(service.sync)(days)

    app = mcp.streamable_http_app(
        streamable_http_path="/mcp",
        stateless_http=True,
        json_response=True,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=service.settings.allowed_hosts,
        ),
    )
    inner = TokenAuthMiddleware(app, token if token is not None else service.settings.bridge_token)
    limiter = RateLimiter(service.settings.rate_limit_per_min)
    return RateLimitMiddleware(inner, limiter)
