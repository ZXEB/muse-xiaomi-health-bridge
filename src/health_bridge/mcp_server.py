from __future__ import annotations

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations

from .security import RateLimiter, RateLimitMiddleware, TokenAuthMiddleware
from .service import HealthService
from .sync import SyncBusyError

INSTRUCTIONS = """
Read-only mirror of the user's Xiaomi Mi Fitness (小米运动健康) data.

Use these tools whenever the user asks about their sleep, steps, heart rate,
blood oxygen (SpO2), stress, weight, calories or workouts. Dates are local
calendar days (default Asia/Shanghai) and every range is inclusive.

If the user asks to refresh, update, pull or "同步/刷新" the latest data, call
sync_now: it pulls from the Xiaomi cloud into the local mirror (5-30 seconds)
and never writes to the Xiaomi account. After sync_now returns, read the fresh
values again with get_daily_summary or the per-domain tools.
For sleep, call get_sleep: daily totals include naps, and sleep_details separates
sessions. Missing or partial details must not be interpreted as no naps.

The data comes from the Xiaomi cloud and can lag until the phone's Mi Fitness
app syncs; the "notes" field says when something is missing or partial.
"""

READ_ONLY = ToolAnnotations(
    read_only_hint=True,
    destructive_hint=False,
    idempotent_hint=True,
    open_world_hint=False,
)

SYNC_NOW = ToolAnnotations(
    title="Refresh from Xiaomi cloud",
    read_only_hint=False,
    destructive_hint=False,
    idempotent_hint=True,
    open_world_hint=True,
)


def _wrap(fn):
    def _inner(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - surface a readable tool error
            raise RuntimeError(str(exc)) from exc

    return _inner


def create_mcp_app(service: HealthService, token: str | None = None):
    mcp = MCPServer("xiaomi-health", instructions=INSTRUCTIONS)

    @mcp.tool(
        description="Bridge status: time zone, last sync, session health, row counts.",
        annotations=READ_ONLY,
    )
    def health_status() -> dict:
        return _wrap(service.status)()

    @mcp.tool(
        description="Compact health summary for the last N days (1-92), with Markdown.",
        annotations=READ_ONLY,
    )
    def get_daily_summary(days: int = 7) -> dict:
        return _wrap(service.summary)(days)

    @mcp.tool(
        description="Daily metrics between two dates (YYYY-MM-DD, inclusive). "
        "Optionally a comma-separated fields list.",
        annotations=READ_ONLY,
    )
    def get_daily_metrics(
        start: str | None = None,
        end: str | None = None,
        fields: str | None = None,
    ) -> dict:
        return _wrap(service.metrics)(start, end, fields)

    @mcp.tool(
        description="Sleep per day: daily total includes naps; sleep_details separates main sleep, naps and other sessions and indicates completeness. Use this for sleep questions.",
        annotations=READ_ONLY,
    )
    def get_sleep(start: str | None = None, end: str | None = None) -> dict:
        return _wrap(service.domain)("sleep", start, end)

    @mcp.tool(description="Steps and distance per day.", annotations=READ_ONLY)
    def get_steps(start: str | None = None, end: str | None = None) -> dict:
        return _wrap(service.domain)("steps", start, end)

    @mcp.tool(
        description="Heart rate per day: average, minimum, maximum, resting.",
        annotations=READ_ONLY,
    )
    def get_heart_rate_daily(start: str | None = None, end: str | None = None) -> dict:
        return _wrap(service.domain)("heart-rate", start, end)

    @mcp.tool(
        description="Blood oxygen (SpO2) per day: average, minimum, maximum.",
        annotations=READ_ONLY,
    )
    def get_spo2_daily(start: str | None = None, end: str | None = None) -> dict:
        return _wrap(service.domain)("spo2", start, end)

    @mcp.tool(
        description="Stress level per day, with minutes in each stress band.",
        annotations=READ_ONLY,
    )
    def get_stress_daily(start: str | None = None, end: str | None = None) -> dict:
        return _wrap(service.domain)("stress", start, end)

    @mcp.tool(description="Weight and BMI entries per day.", annotations=READ_ONLY)
    def get_weight(start: str | None = None, end: str | None = None) -> dict:
        return _wrap(service.domain)("weight", start, end)

    @mcp.tool(
        description="Calories per day: resting, active, intake, total.",
        annotations=READ_ONLY,
    )
    def get_calories(start: str | None = None, end: str | None = None) -> dict:
        return _wrap(service.domain)("calories", start, end)

    @mcp.tool(
        description="Workouts: start/end, sport, duration, distance, calories, heart rate.",
        annotations=READ_ONLY,
    )
    def get_workouts(start: str | None = None, end: str | None = None) -> dict:
        return _wrap(service.workouts)(start, end)

    @mcp.tool(
        description=(
            "Pull the latest data from the Xiaomi cloud into the local mirror right now. "
            "Use this when the user asks to refresh, update or sync their health data. "
            "It takes 5-30 seconds and never modifies the Xiaomi account. "
            "Returns the sync result, last sync time, row counts and whether the login expired. "
            "If another sync is already running it returns busy=true; ask the user to retry shortly."
        ),
        annotations=SYNC_NOW,
    )
    def sync_now(days: int = 7) -> dict:
        try:
            result = service.sync(days)
        except SyncBusyError as exc:
            return {
                "ok": False,
                "busy": True,
                "message": str(exc),
                "retry_after_seconds": 60,
            }
        except Exception as exc:  # noqa: BLE001 - report a readable tool error
            raise RuntimeError(str(exc)) from exc
        status = service.status()
        return {
            "ok": True,
            "synced": result,
            "last_sync_at": status["last_sync_at"],
            "latest_data_date": status["latest_data_date"],
            "counts": status["counts"],
            "session_expired": status["session_expired"],
            "notes": ["Read get_daily_summary again to see the refreshed values."],
        }

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
