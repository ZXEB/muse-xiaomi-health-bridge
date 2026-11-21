from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from types import SimpleNamespace

from fastapi.testclient import TestClient

from tests.conftest import TOKEN, FakeClient

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


def test_admin_sleep_separates_main_sleep_and_naps(service, rest_app, monkeypatch):
    today = service.today()
    day = today.isoformat()
    nap_day = (today - timedelta(days=1)).isoformat()
    legacy_day = (today - timedelta(days=2)).isoformat()
    record = FakeClient().sleep(day, day).records[0]
    main = record.sessions[0]
    nap = replace(
        main, start_epoch_s=main.end_epoch_s + 3600, end_epoch_s=main.end_epoch_s + 5400,
        asleep_min=25, deep_min=None, light_min=None, rem_min=None, awake_min=None,
    )
    monkeypatch.setattr(FakeClient, "sleep", lambda *_: SimpleNamespace(records=[
        replace(record, asleep_min=355, sessions=[nap, main, nap]),
        replace(record, date=nap_day, asleep_min=25, sessions=[nap]),
    ]))
    service.db.upsert_daily([{"date": legacy_day, "sleep_total_min": 400}])
    service.db.upsert_daily(service.source.sleep(nap_day, day))
    service.db.upsert_daily([{"date": day, "steps": 6000}])

    with TestClient(rest_app) as client:
        assert client.get("/admin/api/sleep?days=7").status_code == 401
        _login(client)
        payload = client.get("/admin/api/sleep?days=7").json()
        overview = client.get("/admin/api/overview").json()
        legacy = client.get(f"/v1/sleep?from={day}&to={day}", headers={"Authorization": f"Bearer {TOKEN}"}).json()

    assert len(payload["dates"]) == 7
    unsplit, nap_only, split = payload["days"]
    assert unsplit["detail_status"] == "missing" and unsplit["total_min"] == 400
    assert unsplit["main"] is None and unsplit["nap_min"] is None
    assert nap_only["main"] is None and nap_only["nap_min"] == 25
    assert split["main"]["asleep_min"] == 330 and split["main"]["deep_min"] == 70
    assert len(split["naps"]) == 1 and split["nap_min"] == 25
    assert split["total_min"] == 355 and split["detail_status"] == "complete"
    assert overview["sleep"]["days"][-1] == split
    assert legacy["rows"][0]["sleep_total_min"] == 355
    assert legacy["rows"][0]["sleep_details"] == split
    summary = service.summary(7)
    assert summary["overview"]["sleep_latest"]["sleep_details"] == split
    assert "小睡 0h25m" in summary["markdown"]


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


def test_password_change(rest_app):
    with TestClient(rest_app) as client:
        _login(client)
        old_cookie = client.cookies.get("hb_admin")

        bad = client.post(
            "/admin/api/password", json={"current": "wrong", "new": "newpass123"}, headers=CSRF
        )
        assert bad.status_code == 401

        short = client.post(
            "/admin/api/password", json={"current": "admin-pass", "new": "short"}, headers=CSRF
        )
        assert short.status_code == 400

        ok = client.post(
            "/admin/api/password", json={"current": "admin-pass", "new": "newpass123"}, headers=CSRF
        )
        assert ok.status_code == 200
        assert client.get("/admin/api/overview").status_code == 200

        client.cookies.clear()
        assert client.post("/admin/api/session", json={"password": "admin-pass"}).status_code == 401
        assert client.post("/admin/api/session", json={"password": "newpass123"}).status_code == 200

    stale = TestClient(rest_app)
    stale.cookies.set("hb_admin", old_cookie, path="/admin")
    assert stale.get("/admin/api/overview").status_code == 401


def test_reset_password_cli(tmp_path, monkeypatch):
    from health_bridge import admin
    from health_bridge.db import Database

    db_path = tmp_path / "health.db"
    db = Database(db_path)
    db.set_setting("admin_password_hash", "pbkdf2_sha256$1$abc$def")
    db.set_setting("admin_session_epoch", "3")

    monkeypatch.setenv("DB_PATH", str(db_path))
    monkeypatch.setenv("BRIDGE_TOKEN", "x")

    assert admin._main(["--reset-password"]) == 0
    assert db.get_setting("admin_password_hash") is None
    assert db.get_setting("admin_session_epoch") == "4"


def test_schedule_defaults_and_update(rest_app):
    with TestClient(rest_app) as client:
        _login(client)
        initial = client.get("/admin/api/schedule").json()
        assert initial["mode"] == "daily"
        assert initial["days"] == 7

        bad = client.post("/admin/api/schedule", json={"mode": "interval", "interval_minutes": 2}, headers=CSRF)
        assert bad.status_code == 400

        updated = client.post(
            "/admin/api/schedule",
            json={"mode": "interval", "interval_minutes": 30, "days": 3, "hour": 6, "minute": 15},
            headers=CSRF,
        )
        assert updated.status_code == 200
        body = updated.json()
        assert body["mode"] == "interval"
        assert body["interval_minutes"] == 30
        assert body["days"] == 3
        assert body["next_run_at"]

        fetched = client.get("/admin/api/schedule").json()
        assert fetched["interval_minutes"] == 30
        assert fetched["days"] == 3

        back = client.post(
            "/admin/api/schedule",
            json={"mode": "daily", "hour": 5, "minute": 10, "days": 7},
            headers=CSRF,
        ).json()
        assert back["mode"] == "daily"
        assert back["interval_minutes"] == 0
        assert back["hour"] == 5
