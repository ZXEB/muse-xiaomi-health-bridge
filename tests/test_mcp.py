from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import TOKEN

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json, text/event-stream",
}

INITIALIZE = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "pytest", "version": "0.1.0"},
    },
}


def test_mcp_requires_token(mcp_app):
    with TestClient(mcp_app, base_url="http://127.0.0.1:8788") as client:
        response = client.post("/mcp", json=INITIALIZE, headers={"Accept": "application/json"})
    assert response.status_code == 401


def test_mcp_initialize_and_list_tools(mcp_app):
    with TestClient(mcp_app, base_url="http://127.0.0.1:8788") as client:
        init = client.post("/mcp", json=INITIALIZE, headers=HEADERS)
        assert init.status_code == 200, init.text
        result = init.json()["result"]
        assert result["serverInfo"]["name"] == "xiaomi-health"

        listing = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            headers=HEADERS,
        )
    assert listing.status_code == 200, listing.text
    names = {tool["name"] for tool in listing.json()["result"]["tools"]}
    assert {
        "health_status",
        "get_daily_summary",
        "get_sleep",
        "get_steps",
        "get_heart_rate_daily",
        "get_workouts",
        "sync_now",
    } <= names
