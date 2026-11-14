from __future__ import annotations

from types import SimpleNamespace

from fastapi.testclient import TestClient

CSRF = {"X-Requested-With": "XMLHttpRequest"}


def _login(client: TestClient) -> None:
    response = client.post("/admin/api/session", json={"password": "admin-pass"})
    assert response.status_code == 200, response.text


def test_admin_page_is_public(rest_app):
    with TestClient(rest_app) as client:
        response = client.get("/admin")
    assert response.status_code == 200
    assert "小米健康桥" in response.text


def test_admin_requires_cookie(rest_app):
    with TestClient(rest_app) as client:
        session = client.get("/admin/api/session")
        assert session.status_code == 200
        assert session.json()["authenticated"] is False
        assert client.get("/admin/api/overview").status_code == 401
        assert client.get("/admin/api/status").status_code == 401


def test_admin_login_wrong_password(rest_app):
    with TestClient(rest_app) as client:
        response = client.post("/admin/api/session", json={"password": "nope"})
    assert response.status_code == 401


def test_admin_login_and_overview(rest_app):
    with TestClient(rest_app) as client:
        _login(client)
        response = client.get("/admin/api/overview")
        assert response.status_code == 200
        body = response.json()
        assert body["version"]
        assert "session" in body and "timeline" in body and "summary" in body
        assert body["timeline"]["days"] == 30
        assert len(body["timeline"]["dates"]) == 30
        session = client.get("/admin/api/session")
        assert session.status_code == 200
        assert session.json()["authenticated"] is True
        audit = client.get("/admin/api/audit").json()["entries"]
        assert any(entry["action"] == "login.ok" for entry in audit)


def test_token_endpoint(rest_app):
    with TestClient(rest_app) as client:
        _login(client)
        response = client.get("/admin/api/token")
        assert response.status_code == 200
        assert response.json()["token"] == "test-token"


def test_logout(rest_app):
    with TestClient(rest_app) as client:
        _login(client)
        assert client.post("/admin/api/logout").status_code == 200
        assert client.get("/admin/api/overview").status_code == 401


def test_csrf_required_for_mutations(rest_app):
    with TestClient(rest_app) as client:
        _login(client)
        assert client.post("/admin/api/sync?days=7").status_code == 403
        assert client.post("/admin/api/backups").status_code == 403


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
        started = client.post("/admin/api/xiaomi/login", headers=CSRF)
        assert started.status_code == 200
        state = client.get("/admin/api/xiaomi/login").json()
        assert state["state"] in ("starting", "pending", "success")
        assert state["state"] != "error"
    assert "login_qr" in calls


def test_metrics_and_csv(service, rest_app):
    from datetime import timedelta

    today = service.today()
    service.db.upsert_daily([{"date": today.isoformat(), "steps": 4321, "hr_resting": 55.0}])
    with TestClient(rest_app) as client:
        _login(client)
        metrics = client.get("/admin/api/metrics?domain=steps&start=" + (today - timedelta(days=1)).isoformat() + "&end=" + today.isoformat())
        assert metrics.status_code == 200
        assert metrics.json()["rows"][0]["steps"] == 4321

        csv_response = client.get("/admin/api/export.csv?domain=steps&start=" + (today - timedelta(days=1)).isoformat() + "&end=" + today.isoformat())
        assert csv_response.status_code == 200
        assert "steps" in csv_response.text
        assert "4321" in csv_response.text


def test_settings_has_no_secrets(rest_app):
    with TestClient(rest_app) as client:
        _login(client)
        body = client.get("/admin/api/settings").json()
        assert body["timezone"] == "Asia/Shanghai"
        assert "test-token" not in str(body)
        assert "admin-pass" not in str(body)


def test_backup_create_list_download_delete(rest_app):
    with TestClient(rest_app) as client:
        _login(client)
        created = client.post("/admin/api/backups", headers=CSRF)
        assert created.status_code == 200
        name = created.json()["name"]
        assert name.startswith("health-backup-") and name.endswith(".zip")

        listing = client.get("/admin/api/backups").json()
        assert any(item["name"] == name for item in listing["backups"])

        download = client.get(f"/admin/api/backups/{name}")
        assert download.status_code == 200
        assert download.content[:2] == b"PK"
        assert "health.db" in str(download.content[:2000]) or len(download.content) > 500

        deleted = client.delete(f"/admin/api/backups/{name}", headers=CSRF)
        assert deleted.status_code == 200
        assert client.get(f"/admin/api/backups/{name}").status_code == 404


def test_backup_name_validation(rest_app):
    with TestClient(rest_app) as client:
        _login(client)
        assert client.get("/admin/api/backups/..%2F..%2Fetc%2Fpasswd").status_code in (400, 404)
