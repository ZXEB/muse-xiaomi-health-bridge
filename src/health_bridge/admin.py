from __future__ import annotations

import base64
import csv
import hashlib
import hmac
import io
import json
import re
import secrets
import sqlite3
import tempfile
import threading
import time
import zipfile
from collections import deque
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response

from . import __version__
from .admin_ui import ADMIN_HTML
from .config import Settings
from .db import Database
from .service import DOMAIN_FIELDS, HealthService
from .sync import compute_next_run, read_schedule

COOKIE_NAME = "hb_admin"
COOKIE_TTL_S = 12 * 3600
LOGIN_ATTEMPTS_PER_MIN = 8
CSRF_HEADER = "x-requested-with"


# ---------------------------------------------------------------------------
# auth helpers
# ---------------------------------------------------------------------------


def _secret(settings: Settings) -> bytes:
    # Stable cookie signing key, independent of the admin password, so a password
    # change is handled by the session epoch instead of silently breaking cookies.
    return hashlib.sha256(settings.bridge_token.encode() + b"\0hb-admin-cookie").digest()


def _epoch(service: HealthService) -> str:
    return service.db.get_setting("admin_session_epoch") or "0"


def _sign(settings: Settings, expires_at: int, epoch: str) -> str:
    message = f"{expires_at}:{epoch}".encode()
    signature = hmac.new(_secret(settings), message, hashlib.sha256).hexdigest()
    return f"{expires_at}.{epoch}.{signature}"


def _verify(settings: Settings, service: HealthService, value: str | None) -> bool:
    if not value or not _admin_enabled(service):
        return False
    parts = value.split(".")
    if len(parts) != 3:
        return False
    expires_s, epoch, signature = parts
    try:
        expires_at = int(expires_s)
    except ValueError:
        return False
    if expires_at < time.time():
        return False
    if not hmac.compare_digest(epoch, _epoch(service)):
        return False
    expected = hmac.new(_secret(settings), f"{expires_s}:{epoch}".encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _admin_enabled(service: HealthService) -> bool:
    return bool(service.db.get_setting("admin_password_hash") or service.settings.admin_password)


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    iterations = 210_000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return (
        f"pbkdf2_sha256${iterations}$"
        f"{base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"
    )


def _check_password_hash(password: str, stored: str) -> bool:
    try:
        algorithm, iterations, salt_b64, digest_b64 = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iterations))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


def _check_password(service: HealthService, password: str) -> bool:
    stored = service.db.get_setting("admin_password_hash")
    if stored:
        return _check_password_hash(password, stored)
    env_password = service.settings.admin_password
    return bool(env_password) and hmac.compare_digest(password, env_password)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class LoginAttempts:
    def __init__(self, per_minute: int = LOGIN_ATTEMPTS_PER_MIN):
        self.per_minute = per_minute
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            while hits and now - hits[0] > 60:
                hits.popleft()
            if len(hits) >= self.per_minute:
                return False
            hits.append(now)
            return True


# ---------------------------------------------------------------------------
# QR login
# ---------------------------------------------------------------------------


def _qr_data_url(content: str) -> str:
    import qrcode

    code = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, border=2, box_size=7)
    code.add_data(content)
    code.make(fit=True)
    image = code.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()


class XiaomiLoginManager:
    """Runs one QR login at a time in a background thread."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._state: dict[str, Any] = {"state": "idle"}

    def _set(self, **changes: Any) -> None:
        with self._lock:
            self._state = {**self._state, **changes, "updated_at": datetime.now(timezone.utc).isoformat()}

    def start(self) -> dict[str, Any]:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return dict(self._state)
            self._state = {
                "state": "starting",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "qr": None,
                "login_url": None,
                "error": None,
                "notification_url": None,
            }
            self._thread = threading.Thread(target=self._run, name="xiaomi-login", daemon=True)
            thread = self._thread
        thread.start()
        return self.state()

    def state(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._state)

    def reset(self) -> dict[str, Any]:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                raise RuntimeError("a login attempt is still running; wait for it to finish")
            self._state = {"state": "idle"}
        return self.state()

    def _run(self) -> None:
        try:
            from mifit.auth.qr import login_qr
            from mifit.auth.session import save_session

            def on_qr(login_url: str, qr_payload: str) -> None:
                self._set(state="pending", login_url=login_url, qr=_qr_data_url(login_url))

            session = login_qr(on_qr=on_qr)
            save_session(session)
            self._set(
                state="success",
                user_id=session.user_id,
                finished_at=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as exc:  # noqa: BLE001 - report to the UI
            from mifit import NotificationRequiredError

            if isinstance(exc, NotificationRequiredError):
                self._set(
                    state="needs_notification",
                    error="小米要求额外安全确认，请在手机上完成后重试。",
                    notification_url=getattr(exc, "notification_url", None),
                )
            else:
                self._set(state="error", error=f"{type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
# background sync
# ---------------------------------------------------------------------------


class SyncManager:
    def __init__(self, service: HealthService):
        self.service = service
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._state: dict[str, Any] = {"state": "idle"}

    def start(self, days: int) -> dict[str, Any]:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return dict(self._state)
            self._state = {
                "state": "running",
                "days": days,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "result": None,
                "error": None,
            }
            self._thread = threading.Thread(target=self._run, args=(days,), name="sync", daemon=True)
            thread = self._thread
        thread.start()
        return self.state()

    def state(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._state)

    def _run(self, days: int) -> None:
        try:
            result = self.service.sync(days)
            state = {
                **self._state,
                "state": "done",
                "result": result,
                "finished_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as exc:  # noqa: BLE001
            state = {
                **self._state,
                "state": "error",
                "error": f"{type(exc).__name__}: {exc}",
                "finished_at": datetime.now(timezone.utc).isoformat(),
            }
        with self._lock:
            self._state = state


# ---------------------------------------------------------------------------
# backups
# ---------------------------------------------------------------------------


class BackupManager:
    NAME_RE = re.compile(r"^health-backup-\d{8}-\d{6}\.zip$")

    def __init__(self, db_path: str, session_dir: Path):
        self.db_path = db_path
        self.session_dir = session_dir
        self.dir = Path(db_path).parent / "backups"

    def list(self) -> list[dict[str, Any]]:
        self.dir.mkdir(parents=True, exist_ok=True)
        entries = []
        for path in sorted(self.dir.glob("*.zip"), reverse=True):
            stat = path.stat()
            entries.append(
                {
                    "name": path.name,
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                }
            )
        return entries

    def total_size(self) -> int:
        return sum(item["size"] for item in self.list())

    def create(self) -> dict[str, Any]:
        self.dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        name = f"health-backup-{stamp}.zip"
        target = self.dir / name
        tmp_db = Path(tempfile.mktemp(suffix=".db", dir=self.dir))
        try:
            source = sqlite3.connect(self.db_path, timeout=30)
            try:
                dest = sqlite3.connect(str(tmp_db))
                try:
                    source.backup(dest)
                finally:
                    dest.close()
            finally:
                source.close()

            manifest = {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "version": __version__,
                "session_included": self.session_dir.exists(),
            }
            with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.write(tmp_db, "health.db")
                if self.session_dir.exists():
                    for file in sorted(self.session_dir.rglob("*")):
                        if file.is_file():
                            archive.write(file, "mifit-session/" + str(file.relative_to(self.session_dir)))
                archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
            target.chmod(0o600)
        finally:
            tmp_db.unlink(missing_ok=True)
        return {"name": name, "size": target.stat().st_size}

    def get(self, name: str) -> Path:
        if not self.NAME_RE.match(name):
            raise HTTPException(status_code=400, detail="invalid backup name")
        path = self.dir / name
        if not path.is_file():
            raise HTTPException(status_code=404, detail="backup not found")
        return path

    def delete(self, name: str) -> None:
        self.get(name).unlink()


# ---------------------------------------------------------------------------
# data helpers
# ---------------------------------------------------------------------------


def _timeline(service: HealthService, days: int = 30) -> dict[str, Any]:
    days = max(7, min(days, 92))
    end = service.today()
    start = end - timedelta(days=days - 1)
    rows = service.db.metrics_between(start.isoformat(), end.isoformat())
    workouts = service.db.workouts_between(start.isoformat(), end.isoformat())
    by_date = {row["date"]: row for row in rows}
    workout_counts: dict[str, int] = {}
    for workout in workouts:
        day = workout.get("date") or ""
        workout_counts[day] = workout_counts.get(day, 0) + 1

    dates = [(start + timedelta(days=i)).isoformat() for i in range(days)]
    keys = (
        "steps",
        "sleep_total_min",
        "sleep_deep_min",
        "sleep_light_min",
        "sleep_rem_min",
        "sleep_awake_min",
        "hr_resting",
        "hr_avg",
        "spo2_avg",
        "stress_avg",
        "active_kcal",
    )
    series: dict[str, list[Any]] = {key: [] for key in keys}
    for day in dates:
        row = by_date.get(day, {})
        for key in keys:
            series[key].append(row.get(key))
    return {
        "from": start.isoformat(),
        "to": end.isoformat(),
        "days": days,
        "dates": dates,
        "series": series,
        "workouts": [workout_counts.get(day, 0) for day in dates],
    }


def _schedule_state(service: HealthService) -> dict[str, Any]:
    schedule = read_schedule(service.db, service.settings)
    now = datetime.now(service.settings.tzinfo)
    last_raw = service.db.get_setting("last_auto_sync_at")
    last_run = datetime.fromisoformat(last_raw) if last_raw else None
    return {
        **schedule,
        "mode": "interval" if schedule["interval_minutes"] else "daily",
        "last_run_at": last_raw,
        "next_run_at": compute_next_run(schedule, now, last_run).isoformat(),
    }


def _parse_schedule(payload: dict[str, Any]) -> dict[str, int]:
    mode = str(payload.get("mode", "daily"))
    if mode not in ("daily", "interval"):
        raise ValueError("mode must be daily or interval")
    try:
        interval = int(payload.get("interval_minutes", 0))
        days = int(payload.get("days", 7))
        hour = int(payload.get("hour", 4))
        minute = int(payload.get("minute", 30))
    except (TypeError, ValueError) as exc:
        raise ValueError("interval/hours/days must be integers") from exc
    if mode == "interval":
        if not 5 <= interval <= 1440:
            raise ValueError("interval must be between 5 and 1440 minutes")
    else:
        interval = 0
    if not 1 <= days <= 31:
        raise ValueError("sync window must be between 1 and 31 days")
    if not 0 <= hour <= 23:
        raise ValueError("hour must be between 0 and 23")
    if not 0 <= minute <= 59:
        raise ValueError("minute must be between 0 and 59")
    return {"interval": interval, "days": days, "hour": hour, "minute": minute}


def _overview(service: HealthService, login_manager: XiaomiLoginManager, sync_manager: SyncManager, backups: BackupManager) -> dict[str, Any]:
    status = service.status()
    summary = service.summary(7)
    timeline = _timeline(service, 30)
    end = service.today()
    recent = service.db.workouts_between((end - timedelta(days=365)).isoformat(), end.isoformat())
    return {
        "now": datetime.now(timezone.utc).isoformat(),
        "timezone": service.settings.tz,
        "version": __version__,
        "bridge": status,
        "session": {
            "expired": status["session_expired"],
            "last_sync_at": status["last_sync_at"],
            "daily_rows": status["counts"]["daily_rows"],
            "workout_rows": status["counts"]["workout_rows"],
            "first_date": service.db.earliest_date(),
            "last_date": status["latest_data_date"],
        },
        "summary": summary,
        "timeline": timeline,
        "sleep": service.sleep_days(30),
        "recent_workouts": recent[-5:][::-1],
        "login": login_manager.state(),
        "sync": sync_manager.state(),
        "backups": {"count": len(backups.list()), "total_size": backups.total_size()},
        "audit": service.db.list_audit(8),
        "config": {
            "schedule": _schedule_state(service),
            "backfill_days": service.settings.backfill_days,
            "timezone": service.settings.tz,
        },
    }


def _csv_response(rows: list[dict[str, Any]], filename: str) -> Response:
    buffer = io.StringIO()
    if rows:
        fields: list[str] = []
        for row in rows:
            for key in row:
                if key not in fields:
                    fields.append(key)
        writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    else:
        buffer.write("no data\n")
    return Response(
        content=buffer.getvalue().encode("utf-8-sig"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# router
# ---------------------------------------------------------------------------


def create_admin_router(service: HealthService) -> APIRouter:
    settings = service.settings
    router = APIRouter(prefix="/admin", include_in_schema=False)
    login_manager = XiaomiLoginManager(settings)
    sync_manager = SyncManager(service)
    backups = BackupManager(settings.db_path, Path.home() / ".mifit")
    attempts = LoginAttempts()

    def require(request: Request) -> None:
        if not _admin_enabled(service):
            raise HTTPException(status_code=503, detail="ADMIN_PASSWORD is not configured")
        if not _verify(settings, service, request.cookies.get(COOKIE_NAME)):
            raise HTTPException(status_code=401, detail="not authenticated")

    def require_csrf(request: Request) -> None:
        if request.headers.get(CSRF_HEADER, "").lower() != "xmlhttprequest":
            raise HTTPException(status_code=403, detail="missing X-Requested-With header")

    def audit(request: Request, action: str, detail: str = "") -> None:
        service.db.add_audit(action, detail, _client_ip(request))

    # -- pages ---------------------------------------------------------
    @router.get("", response_class=HTMLResponse)
    @router.get("/", response_class=HTMLResponse)
    def admin_page() -> HTMLResponse:
        return HTMLResponse(ADMIN_HTML, headers={"Cache-Control": "no-store"})

    # -- session -------------------------------------------------------
    @router.post("/api/session")
    @router.post("/api/login")
    def admin_login(request: Request, payload: dict):
        if not _admin_enabled(service):
            return JSONResponse({"error": "ADMIN_PASSWORD is not configured"}, status_code=503)
        if not attempts.allow(_client_ip(request)):
            return JSONResponse({"error": "too many attempts, slow down"}, status_code=429)
        password = str(payload.get("password", ""))
        if not _check_password(service, password):
            audit(request, "login.fail")
            return JSONResponse({"error": "wrong password"}, status_code=401)
        expires_at = int(time.time()) + COOKIE_TTL_S
        secure = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
        response = JSONResponse({"ok": True})
        response.set_cookie(
            COOKIE_NAME,
            _sign(settings, expires_at, _epoch(service)),
            max_age=COOKIE_TTL_S,
            httponly=True,
            samesite="lax",
            secure=secure,
            path="/admin",
        )
        audit(request, "login.ok")
        return response

    @router.delete("/api/session")
    @router.post("/api/logout")
    def admin_logout(request: Request):
        audit(request, "logout")
        response = JSONResponse({"ok": True})
        response.delete_cookie(COOKIE_NAME, path="/admin")
        return response

    @router.get("/api/session")
    def session_state(request: Request):
        return {"authenticated": _verify(settings, service, request.cookies.get(COOKIE_NAME))}

    @router.post("/api/password")
    def change_password(request: Request, payload: dict):
        require(request)
        require_csrf(request)
        if not attempts.allow("password:" + _client_ip(request)):
            return JSONResponse({"error": "too many attempts, slow down"}, status_code=429)
        current = str(payload.get("current", ""))
        new_password = str(payload.get("new", ""))
        if not _check_password(service, current):
            audit(request, "password.change.fail")
            return JSONResponse({"error": "当前密码不正确"}, status_code=401)
        if len(new_password) < 8:
            return JSONResponse({"error": "新密码至少需要 8 个字符"}, status_code=400)
        if hmac.compare_digest(new_password, current):
            return JSONResponse({"error": "新密码不能与当前密码相同"}, status_code=400)
        service.db.set_setting("admin_password_hash", _hash_password(new_password))
        epoch = str(int(_epoch(service)) + 1)
        service.db.set_setting("admin_session_epoch", epoch)
        audit(request, "password.change", "changed via admin UI")
        expires_at = int(time.time()) + COOKIE_TTL_S
        secure = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
        response = JSONResponse({"ok": True})
        response.set_cookie(
            COOKIE_NAME,
            _sign(settings, expires_at, epoch),
            max_age=COOKIE_TTL_S,
            httponly=True,
            samesite="lax",
            secure=secure,
            path="/admin",
        )
        return response

    # -- overview ------------------------------------------------------
    @router.get("/api/overview")
    def overview(request: Request):
        require(request)
        return _overview(service, login_manager, sync_manager, backups)

    @router.get("/api/status")
    def status_alias(request: Request):
        require(request)
        summary = service.summary(7)
        return {
            "bridge": service.status(),
            "login": login_manager.state(),
            "sync": sync_manager.state(),
            "overview": summary["overview"],
            "markdown": summary["markdown"],
        }

    @router.get("/api/timeline")
    def timeline(request: Request, days: int = 30):
        require(request)
        return _timeline(service, days)

    @router.get("/api/summary")
    def summary(request: Request, days: int = 7):
        require(request)
        return service.summary(days)

    @router.get("/api/sleep")
    def sleep_days(request: Request, days: int = 30):
        require(request)
        return service.sleep_days(days)

    # -- data ----------------------------------------------------------
    @router.get("/api/metrics")
    def metrics(
        request: Request,
        domain: str = "all",
        start: str | None = None,
        end: str | None = None,
    ):
        require(request)
        if domain == "all":
            return service.metrics(start, end)
        if domain == "workouts":
            return service.workouts(start, end)
        return service.domain(domain, start, end)

    @router.get("/api/workouts")
    def workouts(request: Request, start: str | None = None, end: str | None = None):
        require(request)
        return service.workouts(start, end)

    @router.get("/api/export.csv")
    def export_csv(
        request: Request,
        domain: str = "all",
        start: str | None = None,
        end: str | None = None,
    ):
        require(request)
        if domain == "workouts":
            payload = service.workouts(start, end)
            rows = payload["rows"]
        elif domain == "all":
            payload = service.metrics(start, end)
            rows = payload["rows"]
        else:
            payload = service.domain(domain, start, end)
            rows = payload["rows"]
        filename = f"health-{domain}-{payload['from']}-{payload['to']}.csv"
        audit(request, "export.csv", f"{domain} {payload['from']}..{payload['to']}")
        return _csv_response(rows, filename)

    # -- sync ----------------------------------------------------------
    @router.post("/api/sync")
    def sync_start(request: Request, days: int = 7):
        require(request)
        require_csrf(request)
        days = max(1, min(int(days), 366))
        audit(request, "sync.start", f"{days} days")
        return sync_manager.start(days)

    @router.get("/api/sync")
    def sync_state(request: Request):
        require(request)
        return sync_manager.state()

    @router.get("/api/schedule")
    def schedule_get(request: Request):
        require(request)
        return _schedule_state(service)

    @router.post("/api/schedule")
    def schedule_set(request: Request, payload: dict):
        require(request)
        require_csrf(request)
        try:
            parsed = _parse_schedule(payload)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        service.db.set_setting("sync_interval_minutes", str(parsed["interval"]))
        service.db.set_setting("sync_hour", str(parsed["hour"]))
        service.db.set_setting("sync_minute", str(parsed["minute"]))
        service.db.set_setting("sync_days", str(parsed["days"]))
        audit(request, "schedule.update", json.dumps(parsed))
        return _schedule_state(service)

    # -- xiaomi login --------------------------------------------------
    @router.post("/api/xiaomi/login")
    def xiaomi_login_start(request: Request):
        require(request)
        require_csrf(request)
        audit(request, "xiaomi.login.start")
        return login_manager.start()

    @router.get("/api/xiaomi/login")
    def xiaomi_login_state(request: Request):
        require(request)
        return login_manager.state()

    @router.delete("/api/xiaomi/login")
    def xiaomi_login_reset(request: Request):
        require(request)
        require_csrf(request)
        return login_manager.reset()

    # -- backups -------------------------------------------------------
    @router.get("/api/backups")
    def backup_list(request: Request):
        require(request)
        return {"backups": backups.list(), "total_size": backups.total_size()}

    @router.post("/api/backups")
    def backup_create(request: Request):
        require(request)
        require_csrf(request)
        entry = backups.create()
        audit(request, "backup.create", entry["name"])
        return entry

    @router.get("/api/backups/{name}")
    def backup_download(request: Request, name: str):
        require(request)
        path = backups.get(name)
        audit(request, "backup.download", name)
        return FileResponse(path, media_type="application/zip", filename=name)

    @router.delete("/api/backups/{name}")
    def backup_delete(request: Request, name: str):
        require(request)
        require_csrf(request)
        backups.delete(name)
        audit(request, "backup.delete", name)
        return {"ok": True}

    # -- settings / token / audit -------------------------------------
    @router.get("/api/token")
    def bridge_token(request: Request):
        require(request)
        return {"token": settings.bridge_token, "mcp_url": "/mcp"}

    @router.get("/api/settings")
    def bridge_settings(request: Request):
        require(request)
        db_size = Path(settings.db_path).stat().st_size if Path(settings.db_path).exists() else 0
        return {
            "version": __version__,
            "timezone": settings.tz,
            "backfill_days": settings.backfill_days,
            "schedule": _schedule_state(service),
            "rate_limit_per_min": settings.rate_limit_per_min,
            "sync_rate_limit_per_min": settings.sync_rate_limit_per_min,
            "allowed_hosts": settings.allowed_hosts,
            "db_path": settings.db_path,
            "db_size": db_size,
            "session_dir": str(Path.home() / ".mifit"),
            "session_present": (Path.home() / ".mifit" / "session.json").exists(),
            "backup_dir": str(backups.dir),
            "max_rows": settings.max_rows,
            "password_source": "database" if service.db.get_setting("admin_password_hash") else "env",
        }

    @router.get("/api/audit")
    def audit_list(request: Request, limit: int = 50):
        require(request)
        return {"entries": service.db.list_audit(limit)}

    @router.get("/api/healthz")
    def admin_healthz(request: Request):
        require(request)
        return {"ok": True}

    return router


def _main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Health bridge admin helpers")
    parser.add_argument(
        "--reset-password",
        action="store_true",
        help="forget the password stored by the web UI so ADMIN_PASSWORD from the environment applies again",
    )
    args = parser.parse_args(argv)
    if not args.reset_password:
        parser.print_help()
        return 1
    settings = Settings()
    db = Database(settings.db_path)
    db.delete_setting("admin_password_hash")
    db.set_setting("admin_session_epoch", str(int(db.get_setting("admin_session_epoch") or "0") + 1))
    print("Stored admin password cleared; ADMIN_PASSWORD from the environment now applies.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
