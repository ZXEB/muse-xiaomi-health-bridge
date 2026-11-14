from __future__ import annotations

from functools import lru_cache
from zoneinfo import ZoneInfo

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, read from the environment.

    Env names are the upper-case field names, e.g. BRIDGE_TOKEN, DB_PATH.
    """

    model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)

    bridge_token: str = ""
    db_path: str = "/data/health.db"
    tz: str = "Asia/Shanghai"

    backfill_days: int = 365
    rate_limit_per_min: int = 60
    sync_rate_limit_per_min: int = 6
    max_rows: int = 500
    max_bytes: int = 200_000

    sync_hour: int = 4
    sync_minute: int = 30
    min_request_interval: float = 1.05

    rest_port: int = 8787
    mcp_port: int = 8788
    bind_host: str = "0.0.0.0"

    # Comma-separated Host header values accepted by the MCP transport.
    # Set this to the public host, e.g. "health.example.com,health.example.com:443".
    mcp_allowed_hosts: str = "127.0.0.1:*,localhost:*"

    @property
    def allowed_hosts(self) -> list[str]:
        return [h.strip() for h in self.mcp_allowed_hosts.split(",") if h.strip()]

    @property
    def tzinfo(self) -> ZoneInfo:
        return ZoneInfo(self.tz)


@lru_cache
def get_settings() -> Settings:
    return Settings()
