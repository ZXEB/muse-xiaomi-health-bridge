from __future__ import annotations

from types import SimpleNamespace

from fastapi.testclient import TestClient


def _login(client: TestClient) -> None:
    response = client.post("/admin/api/login", json={"password": "admin-pass"})
    assert response.status_code == 200, response.text


def test_admin_page_is_public(rest_app):
    with TestClient(rest_app) as client:
        response = client.get("/admin")
    assert response.status_code == 200
    assert "小米运动健康" in response.text


def test_admin_status_requires_cookie(rest_app):
    with TestClient(rest_app) as client:
        response = client.get("/admin/api/status")
    assert response.status_code == 401


def test_admin_login_wrong_password(rest_app):
    with TestClient(rest_app) as client:
        response = client.post("/admin/api/login", json={"password": "nope"})
    assert response.status_code == 401


def test_admin_login_and_status(rest_app):
    with TestClient(rest_app) as client:
        _login(client)
        response = client.get("/admin/api/status")
        assert response.status_code == 200
        body = response.json()
        assert "bridge" in body and "overview" in body
        token = client.get("/admin/api/token")
        assert token.status_code == 200
        assert token.json()["token"] == "test-token"


def test_admin_logout(rest_app):
    with TestClient(rest_app) as client:
        _login(client)
        assert client.post("/admin/api/logout").status_code == 200
        assert client.get("/admin/api/status").status_code == 401


def test_xiaomi_login_flow_uses_mocked_qr(rest_app, monkeypatch):
    calls: list[str] = []

    def fake_login_qr(on_qr=None, **kwargs):
        calls.append("login_qr")
        if on_qr is not None:
            on_qr("https://account.example/login", "https://account.example/qr.png")
        return SimpleNamespace(user_id="user-1")

    monkeypatch.setattr("mifit.auth.qr.login_qr", fake_login_qr)
    monkeypatch.setattr("mifit.auth.session.save_session", lambda session: calls.append("saved"))

    with TestClient(rest_app) as client:
        _login(client)
        started = client.post("/admin/api/xiaomi/login")
        assert started.status_code == 200
        state = client.get("/admin/api/xiaomi/login").json()
        assert state["state"] in ("starting", "pending", "success")
        assert state["state"] != "error"
    assert "login_qr" in calls
