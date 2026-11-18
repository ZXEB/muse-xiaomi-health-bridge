from __future__ import annotations

from base64 import b64encode

from fastapi.testclient import TestClient

from health_bridge.api import create_rest_app
from tests.conftest import TOKEN, make_service


def test_healthz_is_public(rest_app):
    with TestClient(rest_app) as client:
        response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_openapi_is_public(rest_app):
    with TestClient(rest_app) as client:
        response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "/v1/summary" in response.json()["paths"]


def test_favicon_is_public(rest_app):
    with TestClient(rest_app) as client:
        png = client.get("/favicon.png")
        svg = client.get("/favicon.svg")
        icon = client.get("/favicon.ico", follow_redirects=False)
    assert png.status_code == 200
    assert png.headers["content-type"] == "image/png"
    assert png.content.startswith(b"\x89PNG\r\n\x1a\n")
    assert svg.status_code == 200
    assert "svg" in svg.headers["content-type"]
    assert b64encode(png.content) in svg.content
    assert icon.status_code in (302, 307)
    assert icon.headers["location"] == "/favicon.svg"


def test_v1_requires_token(rest_app):
    with TestClient(rest_app) as client:
        response = client.get("/v1/status")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_wrong_token_is_rejected(rest_app):
    with TestClient(rest_app) as client:
        response = client.get("/v1/status", headers={"Authorization": "Bearer nope"})
    assert response.status_code == 401


def test_bearer_token_accepted(rest_app):
    with TestClient(rest_app) as client:
        response = client.get("/v1/status", headers={"Authorization": f"Bearer {TOKEN}"})
    assert response.status_code == 200
    assert response.json()["timezone"] == "Asia/Shanghai"


def test_api_key_header_accepted(rest_app):
    with TestClient(rest_app) as client:
        response = client.get("/v1/status", headers={"X-API-Key": TOKEN})
    assert response.status_code == 200


def test_rate_limit(tmp_path):
    service = make_service(tmp_path, rate_limit_per_min=2)
    app = create_rest_app(service, token=TOKEN)
    headers = {"Authorization": f"Bearer {TOKEN}"}
    with TestClient(app) as client:
        assert client.get("/v1/status", headers=headers).status_code == 200
        assert client.get("/v1/status", headers=headers).status_code == 200
        limited = client.get("/v1/status", headers=headers)
    assert limited.status_code == 429
    assert limited.headers["Retry-After"] == "60"
