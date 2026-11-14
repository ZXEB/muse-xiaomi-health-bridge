from __future__ import annotations

import asyncio
import logging

import uvicorn

from .api import create_rest_app
from .config import get_settings
from .mcp_server import create_mcp_app
from .service import HealthService

logger = logging.getLogger("health_bridge")


def build(service: HealthService | None = None):
    settings = get_settings()
    if not settings.bridge_token:
        logger.warning("BRIDGE_TOKEN is empty; every request will be rejected with 401")
    service = service or HealthService(settings)
    return settings, create_rest_app(service), create_mcp_app(service)


async def _serve(rest_app, mcp_app, bind_host: str, rest_port: int, mcp_port: int) -> None:
    rest_server = uvicorn.Server(
        uvicorn.Config(rest_app, host=bind_host, port=rest_port, access_log=False, lifespan="on")
    )
    mcp_server = uvicorn.Server(
        uvicorn.Config(mcp_app, host=bind_host, port=mcp_port, access_log=False, lifespan="on")
    )
    # Only one server may own the process signal handlers.
    mcp_server.install_signal_handlers = lambda: None  # type: ignore[method-assign]

    tasks = [
        asyncio.create_task(rest_server.serve(), name="rest"),
        asyncio.create_task(mcp_server.serve(), name="mcp"),
    ]
    try:
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    finally:
        rest_server.should_exit = True
        mcp_server.should_exit = True
        await asyncio.gather(*tasks, return_exceptions=True)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    settings, rest_app, mcp_app = build()
    logger.info(
        "REST on %s:%s, MCP on %s:%s/mcp",
        settings.bind_host,
        settings.rest_port,
        settings.bind_host,
        settings.mcp_port,
    )
    asyncio.run(_serve(rest_app, mcp_app, settings.bind_host, settings.rest_port, settings.mcp_port))


if __name__ == "__main__":
    main()
