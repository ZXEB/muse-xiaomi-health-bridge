from __future__ import annotations

import base64
import hashlib
import hmac
import io
import threading
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from .config import Settings
from .service import HealthService

COOKIE_NAME = "hb_admin"
COOKIE_TTL_S = 12 * 3600
LOGIN_ATTEMPTS_PER_MIN = 8


def _secret(settings: Settings) -> bytes:
    material = f"{settings.admin_password}\0{settings.bridge_token}".encode()
    return hashlib.sha256(material).digest()


def _sign(settings: Settings, expires_at: int) -> str:
    message = str(expires_at).encode()
    signature = hmac.new(_secret(settings), message, hashlib.sha256).hexdigest()
    return f"{expires_at}.{signature}"


def _verify(settings: Settings, value: str | None) -> bool:
    if not value or not settings.admin_password or "." not in value:
        return False
    expires, signature = value.split(".", 1)
    try:
        expires_at = int(expires)
    except ValueError:
        return False
    if expires_at < time.time():
        return False
    expected = hmac.new(_secret(settings), expires.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


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

    def _run(self) -> None:
        try:
            from mifit.auth.qr import login_qr
            from mifit.auth.session import save_session

            def on_qr(login_url: str, qr_payload: str) -> None:
                self._set(state="pending", login_url=login_url, qr=_qr_data_url(login_url))

            session = login_qr(on_qr=on_qr)
            save_session(session)
            self._set(state="success", user_id=session.user_id, finished_at=datetime.now(timezone.utc).isoformat())
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


class SyncManager:
    """Runs a sync in the background and reports its last result."""

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
            with self._lock:
                self._state = {
                    **self._state,
                    "state": "done",
                    "result": result,
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                }
        except Exception as exc:  # noqa: BLE001
            with self._lock:
                self._state = {
                    **self._state,
                    "state": "error",
                    "error": f"{type(exc).__name__}: {exc}",
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                }


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    return (forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown"))


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


def create_admin_router(service: HealthService) -> APIRouter:
    settings = service.settings
    router = APIRouter(prefix="/admin", include_in_schema=False)
    login_manager = XiaomiLoginManager(settings)
    sync_manager = SyncManager(service)
    attempts = LoginAttempts()

    def require(request: Request) -> None:
        if not settings.admin_password:
            raise HTTPException(status_code=503, detail="ADMIN_PASSWORD is not configured")
        if not _verify(settings, request.cookies.get(COOKIE_NAME)):
            raise HTTPException(status_code=401, detail="not authenticated")

    @router.get("", response_class=HTMLResponse)
    @router.get("/", response_class=HTMLResponse)
    def admin_page() -> HTMLResponse:
        return HTMLResponse(ADMIN_HTML)

    @router.post("/api/login")
    def admin_login(request: Request, payload: dict):
        if not settings.admin_password:
            return JSONResponse({"error": "ADMIN_PASSWORD is not configured"}, status_code=503)
        if not attempts.allow(_client_ip(request)):
            return JSONResponse({"error": "too many attempts"}, status_code=429)
        password = str(payload.get("password", ""))
        if not hmac.compare_digest(password, settings.admin_password):
            return JSONResponse({"error": "wrong password"}, status_code=401)
        expires_at = int(time.time()) + COOKIE_TTL_S
        secure = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
        response = JSONResponse({"ok": True})
        response.set_cookie(
            COOKIE_NAME,
            _sign(settings, expires_at),
            max_age=COOKIE_TTL_S,
            httponly=True,
            samesite="lax",
            secure=secure,
            path="/admin",
        )
        return response

    @router.post("/api/logout")
    def admin_logout():
        response = JSONResponse({"ok": True})
        response.delete_cookie(COOKIE_NAME, path="/admin")
        return response

    @router.get("/api/status")
    def admin_status(request: Request):
        require(request)
        status = service.status()
        summary = service.summary(7)
        return {
            "bridge": status,
            "login": login_manager.state(),
            "sync": sync_manager.state(),
            "overview": summary["overview"],
            "markdown": summary["markdown"],
        }

    @router.post("/api/xiaomi/login")
    def xiaomi_login_start(request: Request):
        require(request)
        return login_manager.start()

    @router.get("/api/xiaomi/login")
    def xiaomi_login_state(request: Request):
        require(request)
        return login_manager.state()

    @router.post("/api/sync")
    def sync_start(request: Request, days: int = 7):
        require(request)
        return sync_manager.start(max(1, min(int(days), 366)))

    @router.get("/api/token")
    def bridge_token(request: Request):
        require(request)
        return {"token": settings.bridge_token, "mcp_url": "/mcp"}

    @router.get("/api/healthz")
    def admin_healthz(request: Request):
        require(request)
        return {"ok": True}

    return router


ADMIN_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>小米运动健康 · Muse 数据桥</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body { margin: 0; font-family: -apple-system, "Segoe UI", "Microsoft YaHei", sans-serif; background: #0f1115; color: #e6e8ef; }
  .wrap { max-width: 900px; margin: 0 auto; padding: 24px 16px 64px; }
  h1 { font-size: 20px; font-weight: 600; margin: 0 0 4px; }
  .sub { color: #8b90a0; font-size: 13px; margin-bottom: 20px; }
  .card { background: #171a21; border: 1px solid #262b36; border-radius: 12px; padding: 16px; margin-bottom: 14px; }
  .row { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; }
  .k { color: #8b90a0; font-size: 12px; }
  .v { font-size: 16px; margin-top: 2px; }
  .ok { color: #4ade80; } .bad { color: #f87171; } .warn { color: #fbbf24; }
  button { background: #2563eb; color: #fff; border: 0; border-radius: 9px; padding: 9px 14px; font-size: 14px; cursor: pointer; }
  button.ghost { background: #232936; }
  button:disabled { opacity: .5; cursor: default; }
  input { background: #0f1115; border: 1px solid #2f3644; color: #e6e8ef; border-radius: 9px; padding: 10px 12px; font-size: 15px; width: 100%; }
  pre { background: #0b0d12; border: 1px solid #262b36; border-radius: 10px; padding: 12px; overflow: auto; font-size: 12px; line-height: 1.5; white-space: pre-wrap; }
  img.qr { width: 220px; height: 220px; background: #fff; padding: 8px; border-radius: 10px; }
  .msg { font-size: 13px; margin-top: 8px; }
  .hidden { display: none !important; }
  a { color: #7aa2ff; }
  code { background: #0b0d12; padding: 2px 6px; border-radius: 6px; font-size: 12px; word-break: break-all; }
</style>
</head>
<body>
<div class="wrap">
  <h1>小米运动健康 · Muse 数据桥</h1>
  <div class="sub">只读数据通道 · 管理后台</div>

  <section id="loginBox" class="card hidden">
    <div class="k">管理密码</div>
    <div class="row" style="margin-top:8px">
      <input id="password" type="password" placeholder="ADMIN_PASSWORD" style="flex:1;min-width:200px">
      <button id="btnLogin">进入</button>
    </div>
    <div id="loginMsg" class="msg bad"></div>
  </section>

  <section id="dash" class="hidden">
    <div class="card">
      <div class="row" style="justify-content:space-between">
        <div><div class="k">小米登录状态</div><div id="session" class="v">-</div></div>
        <div><div class="k">最后同步</div><div id="lastSync" class="v">-</div></div>
        <div><div class="k">数据天数</div><div id="counts" class="v">-</div></div>
        <div><div class="k">最新数据</div><div id="latest" class="v">-</div></div>
      </div>
    </div>

    <div class="card">
      <div class="row" style="justify-content:space-between">
        <div><div class="k">小米账号</div><div class="v">扫码登录 / 重新登录</div></div>
        <button id="btnLoginXiaomi">获取二维码</button>
      </div>
      <div id="qrBox" class="hidden" style="margin-top:14px">
        <div class="row" style="align-items:flex-start">
          <img id="qrImg" class="qr" alt="QR">
          <div style="flex:1;min-width:220px">
            <div class="k">用「小米运动健康」App 扫码，或在手机浏览器打开下面的链接并登录小米账号确认。</div>
            <div class="msg"><a id="qrLink" target="_blank" rel="noopener"></a></div>
            <div id="qrState" class="msg warn"></div>
          </div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="k">同步</div>
      <div class="row" style="margin-top:8px">
        <button class="ghost" data-days="7">同步最近 7 天</button>
        <button class="ghost" data-days="30">同步最近 30 天</button>
        <button class="ghost" data-days="365">回填 365 天</button>
        <span id="syncState" class="msg"></span>
      </div>
    </div>

    <div class="card">
      <div class="row" style="justify-content:space-between">
        <div class="k">最近 7 天摘要</div>
        <button class="ghost" id="btnToken">显示 MCP Token</button>
      </div>
      <div id="tokenBox" class="msg hidden" style="margin-top:10px">
        <div class="k">MCP 地址：<code id="mcpUrl">/mcp</code></div>
        <div class="k" style="margin-top:6px">Bearer Token：<code id="tokenVal"></code></div>
      </div>
      <pre id="summary" style="margin-top:12px">加载中…</pre>
    </div>

    <div class="row" style="justify-content:flex-end">
      <button class="ghost" id="btnLogout">退出登录</button>
    </div>
  </section>
</div>

<script>
const $ = (id) => document.getElementById(id);
const api = async (path, options = {}) => {
  const res = await fetch('/admin/api' + path, {
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.detail || body.error || ('HTTP ' + res.status));
  return body;
};
let pollTimer = null;

function showLogin() { $('loginBox').classList.remove('hidden'); $('dash').classList.add('hidden'); }
function showDash() { $('loginBox').classList.add('hidden'); $('dash').classList.remove('hidden'); }

async function login() {
  $('loginMsg').textContent = '';
  try {
    await api('/login', { method: 'POST', body: JSON.stringify({ password: $('password').value }) });
    showDash(); refresh(); poll();
  } catch (e) { $('loginMsg').textContent = e.message; }
}

function fmtMinutes(m) {
  if (m == null) return '-';
  const t = Math.round(m);
  return Math.floor(t / 60) + 'h' + String(t % 60).padStart(2, '0') + 'm';
}

function render(data) {
  const b = data.bridge || {};
  $('session').textContent = b.session_expired ? '需要重新登录' : '正常';
  $('session').className = 'v ' + (b.session_expired ? 'bad' : 'ok');
  $('lastSync').textContent = b.last_sync_at ? new Date(b.last_sync_at).toLocaleString() : '从未';
  $('counts').textContent = (b.counts && b.counts.daily_rows ? b.counts.daily_rows : 0) + ' 天';
  $('latest').textContent = b.latest_data_date || '-';
  $('summary').textContent = data.markdown || '暂无数据';
  $('mcpUrl').textContent = (location.origin) + '/mcp';

  const login = data.login || {};
  if (login.state === 'pending' && login.qr) {
    $('qrBox').classList.remove('hidden');
    $('qrImg').src = login.qr;
    $('qrLink').href = login.login_url || '#';
    $('qrLink').textContent = login.login_url || '';
    $('qrState').textContent = '等待手机确认…';
    $('btnLoginXiaomi').disabled = true;
  } else if (login.state === 'success') {
    $('qrState').textContent = '登录成功，session 已保存。';
    $('btnLoginXiaomi').disabled = false;
  } else if (login.state === 'needs_notification') {
    $('qrState').textContent = login.error || '需要安全确认';
    if (login.notification_url) { $('qrLink').href = login.notification_url; $('qrLink').textContent = login.notification_url; }
    $('btnLoginXiaomi').disabled = false;
  } else if (login.state === 'error') {
    $('qrState').textContent = '登录失败：' + (login.error || '未知错误');
    $('btnLoginXiaomi').disabled = false;
  }

  const sync = data.sync || {};
  if (sync.state === 'running') {
    $('syncState').textContent = '同步中（' + sync.days + ' 天）…';
  } else if (sync.state === 'done') {
    $('syncState').textContent = '同步完成：' + JSON.stringify(sync.result || {});
    setTimeout(refresh, 1500);
  } else if (sync.state === 'error') {
    $('syncState').textContent = '同步失败：' + (sync.error || '');
  }
}

async function refresh() {
  try { render(await api('/status')); }
  catch (e) { if (String(e.message).includes('401')) { showLogin(); } }
}

function poll() {
  clearInterval(pollTimer);
  pollTimer = setInterval(refresh, 2500);
}

async function startXiaomiLogin() {
  $('btnLoginXiaomi').disabled = true;
  try { await api('/xiaomi/login', { method: 'POST', body: '{}' }); poll(); }
  catch (e) { $('qrState').textContent = e.message; $('btnLoginXiaomi').disabled = false; }
}

async function startSync(days) {
  try { await api('/sync?days=' + days, { method: 'POST', body: '{}' }); refresh(); }
  catch (e) { $('syncState').textContent = e.message; }
}

async function showToken() {
  try { const d = await api('/token'); $('tokenVal').textContent = d.token; $('tokenBox').classList.remove('hidden'); }
  catch (e) { $('tokenBox').textContent = e.message; $('tokenBox').classList.remove('hidden'); }
}

document.addEventListener('DOMContentLoaded', async () => {
  $('btnLogin').onclick = login;
  $('password').onkeydown = (e) => { if (e.key === 'Enter') login(); };
  $('btnLoginXiaomi').onclick = startXiaomiLogin;
  document.querySelectorAll('[data-days]').forEach((el) => { el.onclick = () => startSync(el.dataset.days); });
  $('btnToken').onclick = showToken;
  $('btnLogout').onclick = async () => { await api('/logout', { method: 'POST', body: '{}' }); location.reload(); };
  try { await api('/healthz'); showDash(); refresh(); poll(); }
  catch (e) { showLogin(); }
});
</script>
</body>
</html>
"""
