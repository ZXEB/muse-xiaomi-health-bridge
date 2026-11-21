from __future__ import annotations

from pathlib import Path

_ASSETS = Path(__file__).with_name("assets")
_CSS = (_ASSETS / "admin.css").read_text(encoding="utf-8")
_CHARTS_JS = (_ASSETS / "admin_charts.js").read_text(encoding="utf-8")
_APP_JS = (_ASSETS / "admin_app.js").read_text(encoding="utf-8")

_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="color-scheme" content="light" />
  <title>小米健康桥 · 管理控制台</title>
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  <link rel="icon" type="image/png" href="/favicon.png" />
  <style>__CSS__</style>
</head>
<body>
  <!-- Login Stage -->
  <main id="login-stage" class="login-stage hidden">
    <svg class="login-backdrop-wave" viewBox="0 0 1440 900" preserveAspectRatio="none" aria-hidden="true">
      <path d="M0 640 C260 560, 420 740, 720 620 C1020 500, 1220 680, 1440 580" fill="none" stroke="rgba(232,84,32,0.14)" stroke-width="2" />
      <path d="M0 690 C300 620, 480 780, 760 660 C1060 540, 1240 720, 1440 640" fill="none" stroke="rgba(14,165,164,0.12)" stroke-width="1.5" />
    </svg>

    <section class="login-card" aria-labelledby="login-heading">
      <div class="login-brand">
        <div class="brand-mark" aria-hidden="true">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="2 13 6 13 9 5 13 19 16 11 18 13 22 13" />
          </svg>
        </div>
        <div>
          <h1 id="login-heading">小米健康桥</h1>
          <p>Xiaomi Mi Fitness → Meta Muse</p>
        </div>
      </div>

      <p class="login-subtitle">输入管理密码进入本地控制台，管理小米云同步、查看睡眠与体征洞察，或获取 Meta Muse 接入凭据。</p>

      <div class="login-meta-strip">
        <div class="login-meta-chip"><strong>只读镜像</strong><span>不修改账号</span></div>
        <div class="login-meta-chip"><strong>MCP + REST</strong><span>标准远程接入</span></div>
        <div class="login-meta-chip"><strong>本地归档</strong><span>SQLite WAL</span></div>
      </div>

      <form id="login-form" style="display:flex;flex-direction:column;gap:14px">
        <div class="field">
          <label class="field-label" for="login-password">管理密码</label>
          <div class="input-wrap">
            <input id="login-password" class="input input-lg" type="password" autocomplete="current-password" placeholder="请输入 ADMIN_PASSWORD" required />
            <button type="button" id="login-eye" class="input-eye" aria-label="显示或隐藏密码">
              <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
                <path d="M2 12s3.8-6 10-6 10 6 10 6-3.8 6-10 6-10-6-10-6z" />
                <circle cx="12" cy="12" r="2.8" />
              </svg>
            </button>
          </div>
        </div>
        <div id="login-error" class="form-error hidden" role="alert"></div>
        <button type="submit" id="login-submit" class="btn btn-primary btn-full">进入管理控制台</button>
      </form>

      <div class="login-footer">
        忘记管理密码？在服务器执行 <code>python -m health_bridge.admin --reset-password</code> 即可恢复为环境变量密码。
      </div>
    </section>
  </main>

  <!-- Main Shell -->
  <div id="app-shell" class="app-shell hidden">
    <div id="sidebar-backdrop" class="sidebar-backdrop"></div>

    <aside id="sidebar" class="sidebar" aria-label="主导航">
      <div class="sidebar-head">
        <div class="sidebar-brand">
          <div class="brand-mark sm" aria-hidden="true">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="2 13 6 13 9 5 13 19 16 11 18 13 22 13" />
            </svg>
          </div>
          <div class="sidebar-brand-text">
            <div class="sidebar-brand-title">
              <span>小米健康桥</span>
              <span id="sidebar-version" class="version-tag">v0.1</span>
            </div>
            <div class="sidebar-brand-sub">Mi Fitness → Muse</div>
          </div>
        </div>
      </div>

      <div id="sidebar-status" class="sidebar-status-card" role="button" tabindex="0">
        <div class="sidebar-status-top">
          <span class="status-indicator">
            <span id="sidebar-dot" class="pulse-dot ok"></span>
            <span id="sidebar-status-label">正在检查状态…</span>
          </span>
        </div>
        <div id="sidebar-status-meta" class="sidebar-status-meta">
          <span>正在载入…</span>
        </div>
      </div>

      <nav class="sidebar-nav">
        <div class="nav-group-label">健康数据</div>
        <button class="nav-item active" data-view="overview">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="8" height="8" rx="2" /><rect x="13" y="3" width="8" height="5" rx="2" />
            <rect x="13" y="10" width="8" height="11" rx="2" /><rect x="3" y="13" width="8" height="8" rx="2" />
          </svg>
          <span>健康概览</span>
        </button>
        <button class="nav-item" data-view="sleep">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20 14.5A8 8 0 0 1 9.5 4 7.5 7.5 0 1 0 20 14.5z" />
          </svg>
          <span>睡眠分析</span>
        </button>
        <button class="nav-item" data-view="data">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="4" width="18" height="16" rx="2" /><line x1="3" y1="10" x2="21" y2="10" /><line x1="9" y1="10" x2="9" y2="20" />
          </svg>
          <span>数据明细</span>
        </button>

        <div class="nav-group-label">桥接与运维</div>
        <button class="nav-item" data-view="sync">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20 11a8 8 0 0 0-14-5L3 9" /><polyline points="3 4 3 9 8 9" />
            <path d="M4 13a8 8 0 0 0 14 5l3-3" /><polyline points="21 20 21 15 16 15" />
          </svg>
          <span>同步与账号</span>
          <span id="nav-sync-badge" class="nav-badge hidden"></span>
        </button>
        <button class="nav-item" data-view="connect">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 17H6a4 4 0 0 1 0-8h3" /><path d="M15 7h3a4 4 0 0 1 0 8h-3" /><line x1="8" y1="12" x2="16" y2="12" />
          </svg>
          <span>Muse 接入</span>
        </button>
        <button class="nav-item" data-view="system">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="3" />
            <path d="M12 2v3M12 19v3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M2 12h3M19 12h3M4.9 19.1L7 17M17 7l2.1-2.1" />
          </svg>
          <span>备份与系统</span>
        </button>
      </nav>

      <div class="sidebar-foot">
        <div class="sidebar-tz">
          <span>本地时区</span>
          <span id="sidebar-tz-label" class="mono">Asia/Shanghai</span>
        </div>
        <button id="btn-logout" class="btn btn-ghost" style="width:100%;justify-content:flex-start">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10 17l5-5-5-5" /><line x1="15" y1="12" x2="3" y2="12" /><path d="M15 4h4a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-4" />
          </svg>
          <span>退出登录</span>
        </button>
      </div>
    </aside>

    <div class="workspace">
      <header class="topbar">
        <div class="topbar-left">
          <button id="mobile-menu-btn" class="mobile-menu-btn" aria-label="打开导航菜单">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <line x1="4" y1="7" x2="20" y2="7" /><line x1="4" y1="12" x2="20" y2="12" /><line x1="4" y1="17" x2="20" y2="17" />
            </svg>
          </button>
          <div class="page-heading">
            <h1 id="topbar-title" class="page-title">健康概览</h1>
            <p id="topbar-sub" class="page-subtitle">核心体征、多维趋势与 Meta Muse 摘要视角</p>
          </div>
        </div>

        <div class="topbar-right">
          <button id="topbar-sync-pill" class="topbar-pill" type="button">
            <span id="topbar-sync-dot" class="pulse-dot ok"></span>
            <span id="topbar-sync-text">正在检查同步…</span>
          </button>
          <button id="btn-quick-sync" class="btn btn-primary" type="button">立即同步</button>
          <button id="btn-refresh-all" class="btn btn-icon" type="button" title="刷新当前数据" aria-label="刷新当前数据">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 12a9 9 0 1 1-2.6-6.4L21 8" /><polyline points="21 3 21 8 16 8" />
            </svg>
          </button>
        </div>
      </header>

      <main class="content-wrap">
        <div id="view-root" style="display:flex;flex-direction:column;gap:20px"></div>
      </main>
    </div>
  </div>

  <!-- Confirmation Modal -->
  <div id="confirm-modal" class="modal-backdrop hidden" role="dialog" aria-modal="true" aria-labelledby="modal-title">
    <div class="modal-card">
      <h2 id="modal-title" class="modal-title">确认操作</h2>
      <p id="modal-body" class="modal-body"></p>
      <div class="modal-actions">
        <button id="modal-cancel" class="btn" type="button">取消</button>
        <button id="modal-ok" class="btn btn-primary" type="button">确认</button>
      </div>
    </div>
  </div>

  <div id="toast-stack" class="toast-stack" aria-live="polite"></div>

  <script>__CHARTS_JS__</script>
  <script>__APP_JS__</script>
</body>
</html>
"""

ADMIN_HTML = (
    _TEMPLATE.replace("__CSS__", _CSS)
    .replace("__CHARTS_JS__", _CHARTS_JS)
    .replace("__APP_JS__", _APP_JS)
)
