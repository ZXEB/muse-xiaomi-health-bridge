from __future__ import annotations

import json

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
    tools = {tool["name"]: tool for tool in listing.json()["result"]["tools"]}
    assert {
        "health_status",
        "get_daily_summary",
        "get_sleep",
        "get_steps",
        "get_heart_rate_daily",
        "get_workouts",
        "sync_now",
    } <= set(tools)
    # sync_now must be advertised as the non-destructive refresh tool.
    annotations = tools["sync_now"].get("annotations") or {}
    assert annotations.get("readOnlyHint") is False
    assert annotations.get("destructiveHint") is False
    assert (tools["get_steps"].get("annotations") or {}).get("readOnlyHint") is True


def _call_tool(client: TestClient, name: str, arguments: dict) -> dict:
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        },
        headers=HEADERS,
    )
    assert response.status_code == 200, response.text
    body = response.json()["result"]
    assert body.get("isError") is not True, body
    return json.loads(body["content"][0]["text"])


def test_mcp_sync_now_busy(service, mcp_app, monkeypatch):
    from health_bridge.sync import SyncBusyError

    def busy(days):
        raise SyncBusyError("a sync is already running; try again in a minute")

    monkeypatch.setattr(service, "sync", busy)
    with TestClient(mcp_app, base_url="http://127.0.0.1:8788") as client:
        result = _call_tool(client, "sync_now", {"days": 1})
    assert result["ok"] is False
    assert result["busy"] is True
    assert result["retry_after_seconds"] == 60


def test_mcp_sync_now_success(service, mcp_app, monkeypatch):
    monkeypatch.setattr(
        service,
        "sync",
        lambda days: {"from": "2026-11-13", "to": "2026-11-14", "days": 2, "chunks": 1, "errors": []},
    )
    with TestClient(mcp_app, base_url="http://127.0.0.1:8788") as client:
        result = _call_tool(client, "sync_now", {"days": 2})
    assert result["ok"] is True
    assert result["synced"]["days"] == 2
    assert "counts" in result
    assert "last_sync_at" in result
