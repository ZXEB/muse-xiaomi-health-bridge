from pathlib import Path


_ADMIN_CSS = (Path(__file__).with_name("assets") / "admin.css").read_text(encoding="utf-8")

ADMIN_HTML = r'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<link rel="icon" type="image/png" sizes="128x128" href="/favicon.png?v=2">
<title>小米健康桥 · 管理后台</title>
<style>
''' + _ADMIN_CSS + r'''
</style>
</head>
<body>

<div id="loginView" class="login-view">
  <div class="login-card">
    <div class="login-brand">
      <img class="logo" src="/favicon.png?v=2" alt="">
      <div><strong>小米健康桥</strong><small>Health Bridge</small></div>
    </div>
    <h1>登录管理后台</h1>
    <form id="loginForm">
      <label for="password">管理密码</label>
      <input id="password" class="input" type="password" autocomplete="current-password" required>
      <button id="btnLogin" class="btn" type="submit">登录</button>
      <div id="loginError" class="error" role="alert"></div>
    </form>
    <p class="login-foot">首次登录使用服务器 <code>/opt/health-bridge/.env</code> 中的 <code>ADMIN_PASSWORD</code>，登录后可在「设置」中修改。</p>
  </div>
</div>

<div id="appView" class="app hidden">
  <header class="app-header">
    <div class="app-header-inner">
      <a class="brand-row" href="#/overview">
        <img class="logo" src="/favicon.png?v=2" alt="">
        <span>小米健康桥</span>
      </a>
      <nav class="site-nav" aria-label="管理后台导航">
        <div class="nav-group nav-primary">
          <a href="#/overview" data-nav="overview"><svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></svg>概览</a>
          <a href="#/sleep" data-nav="sleep"><svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M20.5 14A9 9 0 0 1 10 3.5 9 9 0 1 0 20.5 14Z"/></svg>睡眠</a>
          <a href="#/data" data-nav="data"><svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 6h16M4 12h16M4 18h16"/></svg>数据</a>
        </div>
        <button id="navMore" class="nav-more-toggle" type="button" aria-expanded="false" aria-controls="navTools">
          <svg aria-hidden="true" viewBox="0 0 24 24" fill="currentColor"><circle cx="5" cy="12" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="19" cy="12" r="1.6"/></svg>
          更多
        </button>
        <div id="navTools" class="nav-group nav-tools">
          <div class="mobile-menu-heading">管理</div>
          <a href="#/sync" data-nav="sync"><svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M20 12a8 8 0 1 1-2.3-5.6"/><path d="M20 4v4h-4"/></svg>同步</a>
          <a href="#/xiaomi" data-nav="xiaomi"><svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="8" r="3.4"/><path d="M5 20c1.2-3.5 3.8-5.2 7-5.2s5.8 1.7 7 5.2"/></svg>小米账号</a>
          <a href="#/backups" data-nav="backups"><svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 8h16v11a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V8Z"/><path d="M4 8V6a2 2 0 0 1 2-2h5l2 2h5a2 2 0 0 1 2 2"/></svg>备份</a>
          <a href="#/settings" data-nav="settings"><svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="3"/><path d="M19 12a7 7 0 0 0-.1-1.2l2-1.6-2-3.4-2.4 1a7 7 0 0 0-2-1.2L14 3h-4l-.5 2.6a7 7 0 0 0-2 1.2l-2.4-1-2 3.4 2 1.6a7 7 0 0 0 0 2.4l-2 1.6 2 3.4 2.4-1a7 7 0 0 0 2 1.2L10 21h4l.5-2.6a7 7 0 0 0 2-1.2l2.4 1 2-3.4-2-1.6c.1-.4.1-.8.1-1.2Z"/></svg>设置</a>
          <div class="mobile-menu-actions">
            <button class="btn ghost" type="button" data-admin-action="refresh">刷新数据</button>
            <button class="btn ghost" type="button" data-admin-action="logout">退出登录</button>
          </div>
        </div>
      </nav>
      <div class="top-actions">
        <span id="syncPill" class="pill"><span class="dot warn"></span>加载中</span>
        <button id="btnRefresh" class="icon-btn" type="button" data-admin-action="refresh" title="刷新" aria-label="刷新数据"><svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M20 12a8 8 0 1 1-2.3-5.6"/><path d="M20 4v4h-4"/></svg></button>
        <button id="btnLogout" class="icon-btn" type="button" data-admin-action="logout" title="退出" aria-label="退出登录"><svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3"/><path d="M10 17l-5-5 5-5"/><path d="M5 12h10"/></svg></button>
      </div>
    </div>
  </header>

  <main class="main">
    <header class="page-heading" data-page="overview">
      <h1 id="pageTitle">健康概览</h1>
      <div id="pageCrumb" class="crumb">近 30 天的健康趋势</div>
    </header>

    <section id="page-overview" class="page">
      <div id="overviewBanner" class="banner hidden">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M12 9v4"/><path d="M12 17h.01"/><path d="M10.3 3.9 2.6 17a2 2 0 0 0 1.7 3h15.4a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/></svg>
        <span>小米登录已失效，数据暂停更新。</span>
        <button class="btn sm" onclick="location.hash='#/xiaomi'">重新登录</button>
      </div>

      <div class="grid overview-layout">
        <article class="card feature-panel steps-panel">
          <div class="feature-head">
            <h2>最近步数</h2>
            <div id="statSteps" class="stat">—</div>
            <div id="statStepsSub" class="stat-sub"></div>
          </div>
          <div class="feature-chart">
            <div class="card-head"><h3>近 30 天步数</h3><span id="stepsMeta" class="chart-note"></span></div>
            <div id="chartSteps"></div>
          </div>
        </article>
        <article class="card detail-panel sleep-preview">
          <div class="card-head">
            <h2 class="detail-title"><span class="metric-icon sleep-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M20.5 14A9 9 0 0 1 10 3.5 9 9 0 1 0 20.5 14Z"/></svg></span>主睡眠</h2>
            <a class="btn ghost sm" href="#/sleep">查看睡眠 <span aria-hidden="true">↗</span></a>
          </div>
          <div class="detail-reading">
            <div id="statSleep" class="stat">—</div>
            <div id="statSleepSub" class="stat-sub"></div>
          </div>
          <div class="chart-caption">近 30 天分期 · 小时</div>
          <div id="chartSleep"></div>
          <div class="legend"><span><i style="background:var(--deep)"></i>深睡</span><span><i style="background:var(--light)"></i>浅睡</span><span><i style="background:var(--rem)"></i>REM</span><span><i style="background:var(--awake)"></i>清醒</span></div>
        </article>
        <article class="card detail-panel heart-preview">
          <div class="card-head">
            <h2 class="detail-title"><span class="metric-icon heart-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M20 13c5-7-4-13-8-6-4-7-13-1-8 6l8 8Z"/><path d="M3 12h5l2-3 3 6 2-3h6"/></svg></span>静息心率</h2>
          </div>
          <div class="detail-reading">
            <div id="statHr" class="stat">—</div>
            <div id="statHrSub" class="stat-sub"></div>
          </div>
          <div class="chart-caption"><span>近 30 天 · bpm</span><span id="hrMeta"></span></div>
          <div id="chartHr"></div>
        </article>
        <article class="card activity-panel">
          <div class="card-head"><h2>运动记录</h2><a class="btn ghost sm" href="#/data">查看数据 <span aria-hidden="true">↗</span></a></div>
          <div class="activity-body">
            <div class="activity-summary">
              <span class="metric-icon workout-glyph" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="m7 4-3 3 13 13 3-3ZM4 14l6 6M14 4l6 6M2 17l5 5M17 2l5 5"/></svg></span>
              <h3>近 7 天运动</h3>
              <div id="statWorkouts" class="stat">—</div><div id="statWorkoutsSub" class="stat-sub"></div>
            </div>
            <div id="recentWorkouts"></div>
          </div>
        </article>
      </div>
    </section>

    <section id="page-sleep" class="page hidden">
      <div class="sleep-filters">
        <span id="sleepPeriod" class="sleep-period"></span>
        <div class="seg" id="sleepRange" role="group" aria-label="时间范围">
          <button data-days="7" aria-pressed="false">7 天</button>
          <button data-days="30" class="active" aria-pressed="true">30 天</button>
          <button data-days="90" aria-pressed="false">90 天</button>
        </div>
      </div>
      <p id="sleepStatus" class="sleep-subtitle" role="status"></p>
      <div id="sleepResults" class="hidden">
        <div class="grid sleep-layout">
          <article class="card feature-panel sleep-feature">
            <div class="card-head">
              <div><h2>每日睡眠时长</h2><span class="card-kicker">小时</span></div>
              <div class="legend"><span><i style="background:var(--main-sleep)"></i>主睡眠</span><span><i style="background:var(--nap)"></i>小睡</span></div>
            </div>
            <div id="sleepDurationChart"></div>
          </article>
          <article class="card sleep-summary">
            <div class="sleep-total">
              <h2>总时长（含小睡）</h2>
              <div id="sleepCombinedTotal" class="stat">—</div>
              <div id="sleepCombinedMeta" class="stat-sub"></div>
            </div>
            <div class="sleep-metric">
              <h3>主睡眠时长</h3><div id="sleepMainTotal" class="stat">—</div><div id="sleepMainMeta" class="stat-sub"></div>
            </div>
            <div class="sleep-metric">
              <h3>小睡时长</h3><div id="sleepNapTotal" class="stat">—</div><div id="sleepNapMeta" class="stat-sub"></div>
            </div>
          </article>
        </div>
        <div class="grid sleep-records sleep-section">
          <div class="card">
            <div class="card-head"><h2>每日记录</h2></div>
            <div id="sleepDailyTable" class="table-wrap"></div>
            <p id="sleepCoverage" class="sleep-subtitle"></p>
          </div>
          <div class="card">
            <div class="card-head"><h2>小睡明细</h2></div>
            <div id="sleepNapTable" class="table-wrap"></div>
          </div>
        </div>
      </div>
    </section>

    <section id="page-data" class="page hidden">
      <form id="dataFilters" class="card data-filters">
        <label class="filter-field">指标<select id="dataDomain" class="input"></select></label>
        <div class="filter-field">
          <span id="dataRangeLabel">快捷范围</span>
          <div class="seg" id="dataRangeSeg" role="group" aria-labelledby="dataRangeLabel">
            <button type="button" data-range="7" class="active" aria-pressed="true">7 天</button>
            <button type="button" data-range="30" aria-pressed="false">30 天</button>
            <button type="button" data-range="90" aria-pressed="false">90 天</button>
            <button type="button" data-range="365" aria-pressed="false">365 天</button>
          </div>
        </div>
        <label class="filter-field">开始日期<input id="dataFrom" class="input" type="date"></label>
        <label class="filter-field">结束日期<input id="dataTo" class="input" type="date"></label>
        <button id="btnLoadData" class="btn" type="submit">查询</button>
      </form>
      <div class="card">
        <div class="card-head">
          <div><h2>查询结果</h2><div id="dataNotes" class="card-kicker"></div></div>
          <button id="btnExport" class="btn ghost">导出 CSV</button>
        </div>
        <div id="dataTable" class="table-wrap"></div>
      </div>
    </section>

    <section id="page-sync" class="page hidden">
      <div class="card" style="margin-bottom:14px">
        <div class="card-head"><h3>手动同步</h3><span id="syncTime" class="muted" style="font-size:12px"></span></div>
        <div class="toolbar" style="margin-bottom:0">
          <div class="seg" id="syncSeg">
            <button data-days="7">7 天</button>
            <button data-days="30">30 天</button>
            <button data-days="90">90 天</button>
            <button data-days="365">365 天</button>
          </div>
          <span id="syncState" class="muted" style="font-size:12.5px"></span>
        </div>
        <div id="syncResult" class="muted" style="font-size:12px;margin-top:10px"></div>
        <div id="autoSyncInfo" class="muted" style="font-size:12px;margin-top:4px"></div>
      </div>

      <div class="card" style="margin-bottom:14px">
        <div class="card-head"><h3>自动同步设置</h3><span id="scheduleHint" class="muted" style="font-size:12px"></span></div>
        <div class="toolbar" style="margin-bottom:0">
          <select id="schedMode" class="input">
            <option value="daily">每天定时</option>
            <option value="interval">固定间隔</option>
          </select>
          <span id="schedDailyWrap" class="toolbar" style="margin:0;gap:6px">
            <input id="schedHour" class="input" type="number" min="0" max="23" style="width:78px">
            <span class="muted">:</span>
            <input id="schedMinute" class="input" type="number" min="0" max="59" style="width:78px">
          </span>
          <span id="schedIntervalWrap" class="toolbar hidden" style="margin:0;gap:6px">
            <input id="schedInterval" class="input" type="number" min="5" max="1440" step="5" style="width:100px">
            <span class="muted">分钟一次</span>
          </span>
          <select id="schedDays" class="input">
            <option value="3">每次回看 3 天</option>
            <option value="7">每次回看 7 天</option>
            <option value="14">每次回看 14 天</option>
            <option value="30">每次回看 30 天</option>
          </select>
          <button id="btnSaveSchedule" class="btn">保存</button>
        </div>
        <div id="schedMsg" class="muted" style="font-size:12px;margin-top:9px"></div>
      </div>

      <div class="card">
        <div class="card-head"><h3>各数据域状态</h3></div>
        <div id="domainTable" class="table-wrap"></div>
      </div>
    </section>

    <section id="page-xiaomi" class="page hidden">
      <div class="grid cols-2" style="margin-bottom:14px">
        <div class="card">
          <h3>当前会话</h3>
          <div class="kv">
            <div class="k">状态</div><div class="v" id="xmSession">—</div>
            <div class="k">最后同步</div><div class="v" id="xmLastSync">—</div>
            <div class="k">数据范围</div><div class="v" id="xmRange">—</div>
            <div class="k">数据行数</div><div class="v" id="xmRows">—</div>
          </div>
        </div>
        <div class="card">
          <h3>扫码登录</h3>
          <p class="muted" style="font-size:13px;margin:0 0 12px">用手机「小米运动健康」扫描二维码，或在手机浏览器打开登录链接并确认。登录后 session 会自动保存，服务端自动续期。</p>
          <div class="toolbar" style="margin:0">
            <button id="btnXiaomiLogin" class="btn">获取二维码</button>
            <button id="btnXiaomiReset" class="btn ghost">重置状态</button>
          </div>
          <div id="xmState" class="muted" style="font-size:12.5px;margin-top:10px"></div>
        </div>
      </div>

      <div id="qrPanel" class="card hidden">
        <div class="qr-panel">
          <img id="qrImage" class="qr-img" alt="登录二维码">
          <div class="qr-side">
            <div class="card-head"><h3>等待手机确认</h3><span id="qrBadge" class="pill">已生成</span></div>
            <ol class="steps">
              <li>打开手机「小米运动健康」App（或系统扫码）</li>
              <li>扫描左侧二维码，或打开下面链接并登录小米账号</li>
              <li>在手机上确认登录，等待本页状态变为「成功」</li>
            </ol>
            <div class="muted" style="font-size:12px;margin-top:8px">登录链接（约几分钟内有效）：</div>
            <div id="qrLink" class="qr-link mono"></div>
            <div id="qrNotification" class="muted" style="font-size:12px;margin-top:8px"></div>
          </div>
        </div>
      </div>
    </section>

    <section id="page-backups" class="page hidden">
      <div class="card">
        <div class="card-head">
          <h3>备份</h3>
          <div class="toolbar" style="margin:0">
            <button id="btnBackup" class="btn">立即备份</button>
            <button id="btnBackupRefresh" class="btn ghost">刷新</button>
          </div>
        </div>
        <div class="warn-box">备份包含 SQLite 数据库与小米登录态（等同账号级凭据）。下载后请妥善保管，不要放在公开位置。</div>
        <div id="backupSummary" class="muted" style="font-size:12px;margin-bottom:10px"></div>
        <div id="backupTable" class="table-wrap"></div>
      </div>
    </section>

    <section id="page-settings" class="page hidden">
      <div class="grid cols-2" style="margin-bottom:14px">
        <div class="card">
          <h3>运行配置</h3>
          <div id="settingsKv" class="kv"></div>
        </div>
        <div class="card">
          <div class="card-head"><h3>MCP 接入</h3><span class="pill">Bearer</span></div>
          <div class="copy-row" style="margin-bottom:10px">
            <input id="mcpUrlInput" class="input mono" readonly value="">
            <button class="btn ghost sm" data-copy="mcpUrlInput">复制</button>
          </div>
          <div class="copy-row">
            <input id="tokenInput" class="input mono" readonly value="••••••••••••••••">
            <button id="btnReveal" class="btn ghost sm">显示</button>
            <button class="btn ghost sm" data-copy="tokenInput">复制</button>
          </div>
          <p class="muted" style="font-size:12px;margin:10px 0 0">在 Meta Muse 里让连接器指向上面的 MCP 地址，凭据走 Muse 的安全输入框。</p>
        </div>
      </div>

      <div class="card" style="margin-bottom:14px">
        <h3>修改管理密码</h3>
        <div class="grid cols-3" style="margin-bottom:12px">
          <input id="pwCurrent" class="input" type="password" placeholder="当前密码" autocomplete="off">
          <input id="pwNew" class="input" type="password" placeholder="新密码（至少 8 位）" autocomplete="new-password">
          <input id="pwConfirm" class="input" type="password" placeholder="确认新密码" autocomplete="new-password">
        </div>
        <div class="toolbar" style="margin:0">
          <button id="btnChangePw" class="btn">修改密码</button>
          <span id="pwMsg" class="muted" style="font-size:12.5px"></span>
        </div>
        <p class="muted" style="font-size:12px;margin:10px 0 0">修改后其他浏览器会退出登录，当前页面自动续期。忘记密码时，在服务器执行 <code>docker compose run --rm bridge python -m health_bridge.admin --reset-password</code> 回退到 .env 的密码。</p>
      </div>

      <div class="card" style="margin-bottom:14px">
        <div class="card-head"><h3>Muse 接入提示词</h3><button class="btn ghost sm" id="btnCopyPrompt">复制提示词</button></div>
        <pre id="musePrompt" class="code"></pre>
      </div>

      <div class="card">
        <div class="card-head"><h3>操作审计</h3><button class="btn ghost sm" id="btnAuditRefresh">刷新</button></div>
        <div id="auditTable" class="table-wrap"></div>
      </div>
    </section>
  </main>
</div>

<div id="toasts" aria-live="polite"></div>
<div id="modal" class="modal hidden">
  <div class="modal-card">
    <h3 id="modalTitle">确认操作</h3>
    <p id="modalText"></p>
    <div class="modal-actions">
      <button class="btn ghost" id="modalCancel">取消</button>
      <button class="btn danger" id="modalOk">确认</button>
    </div>
  </div>
</div>

<script>
(function(){
  "use strict";
  var $ = function(s){ return document.querySelector(s); };
  var $$ = function(s){ return Array.prototype.slice.call(document.querySelectorAll(s)); };
  var state = { overview: null, page: "overview", summaryMarkdown: "", token: "", prompt: "", sleepDays: 30, sleepRequest: 0 };

  function esc(s){ return String(s == null ? "" : s).replace(/[&<>"']/g, function(c){ return {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]; }); }
  function fmtNum(v, digits){ if(v == null || v === "") return "—"; var n = Number(v); if(isNaN(n)) return esc(v); return n.toLocaleString("zh-CN", {maximumFractionDigits: digits == null ? 0 : digits}); }
  function fmtFloat(v, d){ if(v == null) return "—"; return Number(v).toFixed(d == null ? 1 : d); }
  function fmtMin(m){ if(m == null) return "—"; var t = Math.round(Number(m)); return Math.floor(t/60) + "h" + String(t%60).padStart(2,"0"); }
  function rel(iso){ if(!iso) return "—"; var d = new Date(iso); var s = (Date.now()-d.getTime())/1000; if(s < 60) return "刚刚"; if(s < 3600) return Math.floor(s/60)+" 分钟前"; if(s < 86400) return Math.floor(s/3600)+" 小时前"; return Math.floor(s/86400)+" 天前"; }
  function isoDate(d){ return d.toISOString().slice(0,10); }
  var SPORT_LABELS = {
    "running":"跑步", "run":"跑步", "outdoor run":"户外跑步", "indoor run":"室内跑步",
    "walking":"步行", "walk":"步行", "hiking":"徒步", "cycling":"骑行", "ride":"骑行",
    "outdoor ride":"户外骑行", "indoor ride":"室内骑行", "swimming":"游泳", "swim":"游泳",
    "workout":"运动", "运动":"运动", "strength":"力量训练", "elliptical":"椭圆机"
  };
  function sportLabel(s){
    var key = String(s || "").toLowerCase();
    return SPORT_LABELS[key] || s || "运动";
  }
  function today(){ var d = new Date(); d.setMinutes(d.getMinutes() - d.getTimezoneOffset()); return d.toISOString().slice(0,10); }
  function daysAgo(n){ var d = new Date(); d.setDate(d.getDate() - n); d.setMinutes(d.getMinutes() - d.getTimezoneOffset()); return d.toISOString().slice(0,10); }

  function toast(msg, kind){
    var el = document.createElement("div");
    el.className = "toast " + (kind || "");
    el.textContent = msg;
    $("#toasts").appendChild(el);
    setTimeout(function(){ el.style.opacity = "0"; el.style.transition = "opacity .25s"; setTimeout(function(){ el.remove(); }, 260); }, 3200);
  }

  function confirmBox(title, text, okLabel){
    return new Promise(function(resolve){
      $("#modalTitle").textContent = title;
      $("#modalText").textContent = text;
      $("#modalOk").textContent = okLabel || "确认";
      $("#modal").classList.remove("hidden");
      function done(v){ $("#modal").classList.add("hidden"); $("#modalOk").onclick = null; $("#modalCancel").onclick = null; resolve(v); }
      $("#modalOk").onclick = function(){ done(true); };
      $("#modalCancel").onclick = function(){ done(false); };
    });
  }

  async function api(path, opts){
    opts = opts || {};
    var headers = { "Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest" };
    var res = await fetch("/admin/api" + path, {
      method: opts.method || "GET",
      credentials: "same-origin",
      headers: headers,
      body: opts.body === undefined ? undefined : JSON.stringify(opts.body)
    });
    var ct = res.headers.get("content-type") || "";
    if(res.status === 401){ showLogin(); throw new Error("登录已过期"); }
    if(!res.ok){
      var b = ct.indexOf("application/json") >= 0 ? await res.json().catch(function(){ return {}; }) : {};
      throw new Error(b.detail || b.error || ("HTTP " + res.status));
    }
    return ct.indexOf("application/json") >= 0 ? res.json() : res;
  }

  /* ---------------- charts ---------------- */
  var PLOT_WIDTH = 600, PLOT_HEIGHT = 140, TICK_COUNT = 4;
  var SLEEP_STAGES = [
    ["deep_min", "深睡", "deep"], ["light_min", "浅睡", "light"],
    ["rem_min", "REM", "rem"], ["awake_min", "清醒", "awake"]
  ];

  function chartFrame(dates, label, marks, min, max, formatTick){
    var ticks = "", grid = "";
    for(var i = 0; i <= TICK_COUNT; i++){
      var y = PLOT_HEIGHT * i / TICK_COUNT;
      ticks += '<span>' + formatTick(max - (max - min) * i / TICK_COUNT) + '</span>';
      grid += '<line class="chart-grid" x1="0" y1="' + y + '" x2="' + PLOT_WIDTH + '" y2="' + y + '"/>';
    }
    var dateIndexes = Array.from(new Set([0, 0.25, 0.5, 0.75, 1].map(function(fraction){
      return Math.round((dates.length - 1) * fraction);
    })));
    var datesHtml = dateIndexes.map(function(index, i){
      var extra = dateIndexes.length === 5 && (i === 1 || i === 3);
      return '<span' + (extra ? ' class="intermediate"' : "") + '>' + esc(dates[index].slice(5).replace("-", "/")) + '</span>';
    }).join("");
    return '<div class="plot-grid"><div class="chart-y" aria-hidden="true">' + ticks + '</div>' +
      '<svg class="chart" role="img" aria-label="' + esc(label) + '" viewBox="0 0 ' + PLOT_WIDTH + ' ' + PLOT_HEIGHT +
      '" preserveAspectRatio="none">' + grid + marks + '</svg><div class="chart-x">' + datesHtml + '</div></div>';
  }

  function chartEmpty(message){
    return '<div class="empty chart-empty">' + esc(message) + '</div>';
  }

  function chartBar(x, y, width, height, color, title, radius){
    return '<rect x="' + x.toFixed(2) + '" y="' + y.toFixed(2) + '" width="' + width.toFixed(2) +
      '" height="' + height.toFixed(2) + '" rx="' + radius + '" fill="var(--' + color + ')"><title>' +
      esc(title) + '</title></rect>';
  }

  function stepsChart(dates, values){
    var recorded = values.filter(function(value){ return value != null; });
    if(!recorded.length){ return chartEmpty("暂无步数记录"); }
    var max = Math.max(4000, Math.ceil(Math.max(...recorded) / 4000) * 4000);
    var slot = PLOT_WIDTH / dates.length;
    var bars = values.map(function(value, index){
      if(value == null){ return ""; }
      var h = value === 0 ? 1 : value / max * PLOT_HEIGHT;
      return chartBar(slot * (index + 0.15), PLOT_HEIGHT - h, slot * 0.7, h, "steps",
        dates[index] + " · " + fmtNum(value) + " 步", 1.25);
    }).join("");
    return chartFrame(dates, "每日步数", bars, 0, max, fmtNum);
  }

  function sleepAxisMax(minutes){
    return Math.max(480, Math.ceil(minutes / 240) * 240);
  }

  function stackedSleep(dates, primaryByDate){
    var max = sleepAxisMax(Math.max(...dates.map(function(day){
      var main = primaryByDate.get(day);
      return SLEEP_STAGES.reduce(function(sum, stage){ return sum + (main?.[stage[0]] || 0); }, 0);
    })));
    var slot = PLOT_WIDTH / dates.length;
    var bars = dates.map(function(day, i){
      var main = primaryByDate.get(day);
      if(!main){ return ""; }
      var y = PLOT_HEIGHT;
      return SLEEP_STAGES.map(function(stage){
        var value = main[stage[0]];
        if(!value){ return ""; }
        var h = value / max * PLOT_HEIGHT;
        y -= h;
        return chartBar(slot * (i + 0.18), y, slot * 0.64, h, stage[2],
          day + " · " + stage[1] + " " + sleepMinutes(value), 0);
      }).join("");
    }).join("");
    return bars ? chartFrame(dates, "每日主睡眠分期", bars, 0, max, function(v){ return v / 60; })
      : chartEmpty("暂无主睡眠分期");
  }

  function heartChart(dates, values){
    var recorded = values.filter(function(value){ return value != null; });
    if(!recorded.length){ return chartEmpty("暂无静息心率记录"); }
    var min = Math.max(0, Math.floor(Math.min(...recorded)) - 1);
    var step = Math.max(2, Math.ceil((Math.max(...recorded) + 1 - min) / TICK_COUNT));
    var max = min + step * TICK_COUNT, slot = PLOT_WIDTH / dates.length;
    var segments = [], current = [];
    values.forEach(function(value, index){
      if(value == null){
        current = [];
        return;
      }
      if(!current.length){ segments.push(current); }
      current.push({
        x: (slot * (index + 0.5)).toFixed(2),
        y: (PLOT_HEIGHT * (max - value) / (max - min)).toFixed(2),
        title: dates[index] + " · " + fmtNum(value, 1) + " bpm"
      });
    });
    var marks = segments.map(function(segment){
      var points = segment.map(function(point){ return point.x + " " + point.y; }).join(" L");
      var area = "M" + segment[0].x + " " + PLOT_HEIGHT + " L" + points +
        " L" + segment[segment.length - 1].x + " " + PLOT_HEIGHT + " Z";
      return '<path d="' + area + '" fill="var(--heart)" opacity=".09"/>' +
        '<path class="chart-line" d="M' + points + '" fill="none" stroke="var(--heart)" stroke-width="2" stroke-linejoin="round"/>' +
        segment.map(function(point){
          return '<ellipse cx="' + point.x + '" cy="' + point.y + '" rx="2.6" ry="2.4" fill="var(--heart)"><title>' +
            esc(point.title) + '</title></ellipse>';
        }).join("");
    }).join("");
    return chartFrame(dates, "每日静息心率", marks, min, max, fmtNum);
  }

  /* ---------------- pages ---------------- */
  var PAGE_META = {
    overview: ["健康概览", "近 30 天的健康趋势"],
    sleep: ["睡眠", "主睡眠与小睡记录"],
    data: ["数据", "按日期与指标浏览，支持导出 CSV"],
    sync: ["同步", "手动同步与各数据域状态"],
    xiaomi: ["小米账号", "扫码登录与会话状态"],
    backups: ["备份", "SQLite 与登录态备份"],
    settings: ["设置", "运行配置、MCP 接入与审计"]
  };

  function showLogin(){ $("#loginView").classList.remove("hidden"); $("#appView").classList.add("hidden"); }
  function showApp(){ $("#loginView").classList.add("hidden"); $("#appView").classList.remove("hidden"); }

  function setStatus(kind, text){
    var pill = $("#syncPill");
    var status = '<span class="dot ' + kind + '"></span>' + esc(text);
    if(pill.innerHTML !== status){ pill.innerHTML = status; }
  }

  function renderOverview(data){
    state.overview = data;
    var s = data.session, o = data.summary.overview, t = data.timeline;
    var daily = data.summary.daily || [];
    var last = daily.length ? daily[daily.length-1] : null;
    var primary = (data.sleep?.days || []).filter(function(row){ return row.main; });
    var latestSleep = primary[primary.length - 1];
    $("#overviewBanner").classList.toggle("hidden", !s.expired);

    $("#statSteps").innerHTML = last?.steps != null ? fmtNum(last.steps) + '<small>步</small>' : "—";
    $("#statStepsSub").textContent = last?.steps != null
      ? last.date + (last.distance_m == null ? "" : " · " + fmtFloat(last.distance_m/1000,2) + " km")
      : "暂无数据";
    $("#statSleep").innerHTML = durationStat(latestSleep?.main.asleep_min);
    $("#statSleepSub").textContent = latestSleep ? (latestSleep.date + " · 深睡 " + sleepMinutes(latestSleep.main.deep_min)) : "暂无主睡眠分段";
    $("#statHr").innerHTML = last && last.hr_resting != null ? fmtNum(last.hr_resting) + '<small>bpm</small>' : "—";
    $("#statHrSub").textContent = last?.hr_resting != null
      ? last.date + (last.hr_avg == null ? "" : " · 日均 " + fmtNum(last.hr_avg))
      : "暂无数据";
    $("#statWorkouts").innerHTML = fmtNum(o.workout_count) + '<small>次</small>';
    $("#statWorkoutsSub").textContent = o.workout_count
      ? (o.workout_distance_m ? ("合计 " + fmtFloat(o.workout_distance_m/1000,1) + " km") : "近 7 天")
      : ((data.recent_workouts && data.recent_workouts.length) ? ("最近一次 " + (data.recent_workouts[0].date || "")) : "暂无运动记录");

    $("#chartSteps").innerHTML = stepsChart(t.dates, t.series.steps);
    var primaryByDate = new Map(primary.map(function(row){ return [row.date, row.main]; }));
    $("#chartSleep").innerHTML = stackedSleep(t.dates, primaryByDate);
    $("#chartHr").innerHTML = heartChart(t.dates, t.series.hr_resting);
    var stepDays = t.series.steps.filter(function(v){ return v != null; });
    $("#stepsMeta").textContent = stepDays.length ? "合计 " + fmtNum(stepDays.reduce(function(a,b){ return a + b; }, 0)) + " 步" : "";
    var hrVals = t.series.hr_resting.filter(function(v){ return v != null; });
    $("#hrMeta").textContent = hrVals.length ? ("均值 " + fmtFloat(hrVals.reduce(function(a,b){ return a+b; },0)/hrVals.length,0) + " bpm") : "";
    if(state.page === "overview"){ $("#pageCrumb").textContent = t.from + " 至 " + t.to; }

    var wl = data.recent_workouts || [];
    if(!wl.length){ $("#recentWorkouts").innerHTML = '<div class="empty">暂无运动记录</div>'; }
    else {
      var icon = $(".activity-summary .workout-glyph").outerHTML;
      $("#recentWorkouts").innerHTML = wl.map(function(w){
        var meta = [w.duration_s ? Math.round(w.duration_s/60)+" 分钟" : "", w.distance_m ? fmtFloat(w.distance_m/1000,2)+" km" : "", w.avg_hr ? fmtNum(w.avg_hr)+" bpm" : ""].filter(Boolean).join(" · ");
        var stamp = w.start_time || w.date || "";
        return '<div class="workout-row"><div class="workout-icon">' + icon +
          '</div><div class="workout-info"><strong>' + esc(sportLabel(w.sport)) + '</strong><small>' + esc(meta) +
          '</small></div><time datetime="' + esc(stamp) + '">' + esc(stamp.slice(0,16).replace("T"," ")) + '</time></div>';
      }).join("");
    }

    var sync = data.sync || {};
    if(sync.state === "running"){ setStatus("warn", "同步中"); }
    else if(s.expired){ setStatus("bad", "需要重新登录"); }
    else if(s.last_sync_at){
      var age = (Date.now() - new Date(s.last_sync_at).getTime()) / 3600000;
      setStatus(age < 36 ? "" : "warn", rel(s.last_sync_at) + "同步");
    }
    else { setStatus("warn", "尚未同步"); }
    if(state.page === "sync"){ renderSync(data); }
    if(state.page === "xiaomi"){ renderXiaomi(data); }
  }

  async function loadOverview(quiet){
    try { renderOverview(await api("/overview")); }
    catch(e){ if(!quiet){ toast(e.message, "bad"); } }
  }

  function renderSync(data){
    var sync = data.sync || {};
    var cfg = data.config || {};
    $("#syncTime").textContent = data.session.last_sync_at ? ("上次同步 " + rel(data.session.last_sync_at)) : "从未同步";
    var el = $("#syncState");
    if(sync.state === "running"){
      el.textContent = "正在同步最近 " + sync.days + " 天…";
      $$("#syncSeg button").forEach(function(b){ b.disabled = true; });
    } else {
      $$("#syncSeg button").forEach(function(b){ b.disabled = false; });
      el.textContent = "";
    }
    var resultEl = $("#syncResult");
    if(sync.state === "done"){
      var r = sync.result || {};
      var errs = (r.errors && r.errors.length) || 0;
      resultEl.innerHTML = '<span class="' + (errs ? "warn" : "ok") + '">' + (errs ? "完成，但有 " + errs + " 个错误" : "同步完成") + '</span>' +
        ' · 范围 ' + esc(r.from || "") + ' ~ ' + esc(r.to || "") + ' · ' + fmtNum(r.days) + ' 天 · ' + fmtNum(r.chunks) + ' 个分块';
      if(errs){ resultEl.innerHTML += '<div class="err" style="margin-top:4px;font-size:11.5px">' + esc((r.errors || []).slice(0, 3).join("；")) + '</div>'; }
    } else if(sync.state === "error"){
      resultEl.innerHTML = '<span class="err">同步失败：' + esc(sync.error || "") + '</span>';
    } else {
      resultEl.textContent = "";
    }
    $("#autoSyncInfo").textContent = (function(){
      var sched = cfg.schedule;
      if(!sched){ return ""; }
      var when = sched.mode === "interval"
        ? ("每 " + sched.interval_minutes + " 分钟")
        : ("每天 " + String(sched.hour).padStart(2,"0") + ":" + String(sched.minute).padStart(2,"0"));
      var next = sched.next_run_at ? ("，下次 " + new Date(sched.next_run_at).toLocaleString()) : "";
      return when + " 自动同步（每次回看 " + sched.days + " 天）" + next;
    })();

    var domains = (data.bridge && data.bridge.domains) || {};
    var names = Object.keys(domains).sort();
    var rows = names.map(function(name){
      var d = domains[name] || {};
      return { domain: name, last_date: d.last_date, last_synced_at: d.last_synced_at, last_error: d.last_error };
    });
    renderTable($("#domainTable"), rows, [
      {key:"domain", label:"数据域"},
      {key:"last_date", label:"同步到"},
      {key:"last_synced_at", label:"时间", fmt:function(v){ return v ? (rel(v) + " · " + new Date(v).toLocaleTimeString()) : "—"; }},
      {key:"last_error", label:"错误", fmt:function(v){ return v ? '<span class="err" title="'+esc(v)+'">'+esc(v)+'</span>' : '<span class="ok">正常</span>'; }, raw:true}
    ], "暂无同步状态");
  }

  function renderXiaomi(data){
    var s = data.session;
    $("#xmSession").innerHTML = s.expired ? '<span class="err">已失效，需要重新登录</span>' : '<span class="ok">正常</span>';
    $("#xmLastSync").textContent = s.last_sync_at ? (rel(s.last_sync_at) + "（" + new Date(s.last_sync_at).toLocaleString() + "）") : "从未";
    $("#xmRange").textContent = (s.first_date || "—") + " ~ " + (s.last_date || "—");
    $("#xmRows").textContent = fmtNum(s.daily_rows) + " 天数据 / " + fmtNum(s.workout_rows) + " 条运动";
    var login = data.login || {};
    var st = $("#xmState");
    if(login.state === "starting"){ st.textContent = "正在向小米请求二维码…"; }
    else if(login.state === "pending"){ st.textContent = "等待手机确认…"; }
    else if(login.state === "success"){ st.textContent = "登录成功，session 已保存。"; toast("小米登录成功", "ok"); }
    else if(login.state === "error"){ st.textContent = "失败：" + (login.error || ""); }
    else if(login.state === "needs_notification"){ st.textContent = login.error || "需要安全确认"; }
    else { st.textContent = ""; }

    if(login.state === "pending" && login.qr){
      $("#qrPanel").classList.remove("hidden");
      $("#qrImage").src = login.qr;
      $("#qrLink").textContent = login.login_url || "";
      $("#qrBadge").textContent = "等待确认";
      $("#btnXiaomiLogin").disabled = true;
    } else {
      $("#qrPanel").classList.add("hidden");
      $("#btnXiaomiLogin").disabled = false;
      if(login.notification_url){ $("#qrNotification").innerHTML = '需要安全确认：<a href="' + esc(login.notification_url) + '" target="_blank" rel="noopener">打开确认链接</a>，完成后重新获取二维码。'; }
      else { $("#qrNotification").textContent = ""; }
    }
  }

  function renderTable(el, rows, columns, emptyText){
    if(!rows || !rows.length){ el.innerHTML = '<div class="empty">' + esc(emptyText || "暂无数据") + '</div>'; return; }
    var html = "<table><thead><tr>" + columns.map(function(c){ return "<th>" + esc(c.label) + "</th>"; }).join("") + "</tr></thead><tbody>";
    rows.forEach(function(row){
      html += "<tr>" + columns.map(function(c){
        var v = row[c.key];
        var out;
        if(c.raw){ out = c.fmt ? c.fmt(v, row) : (v == null ? "—" : esc(v)); }
        else if(v == null || v === ""){ out = '<span class="muted">—</span>'; }
        else { out = esc(c.fmt ? c.fmt(v, row) : v); }
        return "<td>" + out + "</td>";
      }).join("") + "</tr>";
    });
    el.innerHTML = html + "</tbody></table>";
  }

  /* ---------------- sleep page ---------------- */
  function sleepMinutes(v){
    if(v == null){ return "—"; }
    var minutes = Math.round(v);
    if(minutes < 60){ return minutes + " 分钟"; }
    var remainder = minutes % 60;
    return Math.floor(minutes / 60) + " 小时" + (remainder ? " " + remainder + " 分" : "");
  }
  function durationStat(value){
    if(value == null){ return "—"; }
    var minutes = Math.round(value);
    if(minutes < 60){ return minutes + '<small>分钟</small>'; }
    var remainder = minutes % 60;
    return Math.floor(minutes / 60) + '<small>小时</small>' + (remainder ? remainder + '<small>分</small>' : "");
  }
  function sleepTime(session){
    if(!session || !session.start || !session.end){ return "—"; }
    var startDay = session.start.slice(0, 10), endDay = session.end.slice(0, 10);
    var awake = session.end.slice(11, 16), asleep = session.start.slice(11, 16);
    if(startDay !== endDay){ asleep = startDay.slice(5) + " " + asleep; }
    return asleep + " – " + awake;
  }
  function sleepDurationChart(data){
    var byDate = new Map(data.days.map(function(row){ return [row.date, row]; }));
    var max = sleepAxisMax(Math.max(...data.days.map(function(row){
      return Math.max(row.main?.asleep_min || 0, row.nap_min || 0);
    })));
    var slot = PLOT_WIDTH / data.dates.length;
    var bars = data.dates.map(function(day, i){
      var row = byDate.get(day);
      if(!row){ return ""; }
      return [[row.main?.asleep_min, "主睡眠", "main-sleep"], [row.nap_min, "小睡", "nap"]].map(function(bar, j){
        var minutes = bar[0];
        if(!minutes){ return ""; }
        var h = minutes / max * PLOT_HEIGHT;
        return chartBar(slot * (i + 0.14 + j * 0.37), PLOT_HEIGHT - h, slot * 0.35, h, bar[2],
          day + " · " + bar[1] + " " + sleepMinutes(minutes), 1.2);
      }).join("");
    }).join("");
    return bars ? chartFrame(data.dates, "每日主睡眠和小睡时长", bars, 0, max, function(v){ return v / 60; })
      : chartEmpty("暂无可绘制的睡眠分段");
  }
  function renderSleep(data){
    $("#sleepPeriod").textContent = data.from + " 至 " + data.to;
    $("#sleepStatus").textContent = data.days.length ? "" : "这段时间没有已同步的睡眠记录";
    $("#sleepResults").classList.toggle("hidden", !data.days.length);
    if(!data.days.length){ return; }

    var mainDays = data.days.filter(function(row){ return row.main; });
    var mainTotal = mainDays.reduce(function(total, row){ return total + row.main.asleep_min; }, 0);
    var napDays = data.days.filter(function(row){ return row.nap_min != null; });
    var naps = data.days.slice().reverse().flatMap(function(row){
      return row.naps.map(function(nap){ return {date:row.date, time:sleepTime(nap), minutes:nap.asleep_min}; });
    });
    var napTotal = naps.reduce(function(total, nap){ return total + nap.minutes; }, 0);
    var combined = data.days.reduce(function(total, row){ return total + row.total_min; }, 0);
    $("#sleepMainTotal").innerHTML = durationStat(mainDays.length ? mainTotal : null);
    $("#sleepMainMeta").textContent = mainDays.length ? (mainDays.length + " 天有主睡眠 · 平均 " + sleepMinutes(mainTotal / mainDays.length)) : "暂无已识别的主睡眠";
    $("#sleepNapTotal").innerHTML = durationStat(napDays.length ? napTotal : null);
    $("#sleepNapMeta").textContent = napDays.length ? (naps.length + " 次已识别的小睡") : "暂无可区分的小睡分段";
    $("#sleepCombinedTotal").innerHTML = durationStat(combined);
    $("#sleepDurationChart").innerHTML = sleepDurationChart(data);

    var daily = data.days.slice().reverse().map(function(row){
      return {date:row.date, main:row.main?.asleep_min, time:sleepTime(row.main), nap:row.nap_min,
        total:row.total_min, other:row.other.length ? row.other.reduce(function(total, session){ return total + session.asleep_min; }, 0) : null};
    });
    var columns = [{key:"date", label:"日期"}, {key:"main", label:"主睡眠", raw:true, fmt:function(v, row){
      return v == null ? "—" : esc(sleepMinutes(v)) + '<small class="sleep-main-time">' + esc(row.time) + '</small>';
    }}, {key:"nap", label:"小睡", fmt:sleepMinutes}];
    if(daily.some(function(row){ return row.other != null; })){
      columns.push({key:"other", label:"其他睡眠分段", fmt:sleepMinutes});
    }
    columns.push({key:"total", label:"含小睡合计", fmt:sleepMinutes});
    renderTable($("#sleepDailyTable"), daily, columns);
    renderTable($("#sleepNapTable"), naps, [{key:"date", label:"日期"}, {key:"time", label:"时段"},
      {key:"minutes", label:"时长", fmt:sleepMinutes}], "这段时间没有已识别的小睡");
    var missing = data.days.filter(function(row){ return row.detail_status === "missing"; }).length;
    var partial = data.days.filter(function(row){ return row.detail_status === "partial"; }).length;
    $("#sleepCombinedMeta").textContent = "小米按天汇总" + (missing ? (" · 含 " + missing + " 天未拆分记录") : "");
    var notes = ["主睡眠取当天有分期的最长一段，小睡取无分期且少于 3 小时的分段。"];
    if(missing){ notes.push(missing + " 天只有小米汇总，暂无分段。"); }
    if(partial){ notes.push(partial + " 天的分段时长与小米合计存在差异。"); }
    $("#sleepCoverage").textContent = notes.join(" ");
  }
  async function loadSleep(){
    var request = ++state.sleepRequest;
    $("#sleepPeriod").textContent = "";
    $("#sleepStatus").textContent = "正在加载睡眠记录…";
    $("#sleepResults").classList.add("hidden");
    try {
      var data = await api("/sleep?days=" + state.sleepDays);
      if(request === state.sleepRequest){ renderSleep(data); }
    } catch(e){
      if(request === state.sleepRequest){ $("#sleepStatus").textContent = "睡眠记录加载失败，可点击刷新重试。"; }
    }
  }

  /* ---------------- data page ---------------- */
  var DOMAINS = [
    ["all", "全部指标"], ["steps", "步数"], ["sleep", "睡眠"], ["heart-rate", "心率"],
    ["spo2", "血氧"], ["stress", "压力"], ["weight", "体重"], ["activity", "活力"],
    ["calories", "卡路里"], ["workouts", "运动记录"]
  ];
  function initDataPage(){
    if($("#dataDomain").options.length) { return; }
    DOMAINS.forEach(function(d){ var o = document.createElement("option"); o.value = d[0]; o.textContent = d[1]; $("#dataDomain").appendChild(o); });
    $("#dataFrom").value = daysAgo(6);
    $("#dataTo").value = today();
    loadData();
  }
  async function loadData(){
    var domain = $("#dataDomain").value, from = $("#dataFrom").value, to = $("#dataTo").value;
    $("#dataTable").innerHTML = '<div class="empty">加载中…</div>';
    try{
      var res = await api("/metrics?domain=" + encodeURIComponent(domain) + "&start=" + from + "&end=" + to);
      var rows = res.rows || [];
      $("#dataNotes").textContent = (rows.length ? (rows.length + " 行") : "无数据") + (res.notes && res.notes.length ? " · " + res.notes.join("；") : "");
      if(domain === "workouts"){
        renderTable($("#dataTable"), rows, [
          {key:"start_time", label:"开始"}, {key:"sport", label:"类型"},
          {key:"duration_s", label:"时长", fmt:function(v){ return v == null ? "—" : Math.round(v/60) + " 分钟"; }},
          {key:"distance_m", label:"距离", fmt:function(v){ return v == null ? "—" : fmtFloat(v/1000,2) + " km"; }},
          {key:"avg_hr", label:"平均心率"}, {key:"max_hr", label:"最大心率"},
          {key:"active_kcal", label:"活动千卡", fmt:function(v){ return fmtNum(v); }}, {key:"steps", label:"步数", fmt:function(v){ return fmtNum(v); }}
        ], "该时间段没有运动记录");
      } else {
        var keys = rows.length ? Object.keys(rows[0]) : ["date"];
        if(domain === "all"){
          var present = {};
          keys.forEach(function(k){ present[k] = true; });
          keys = ALL_COLUMNS.filter(function(k){ return present[k]; });
          if(!keys.length){ keys = ["date"]; }
        }
        var cols = [{key:"date", label:"日期"}];
        keys.forEach(function(k){
          if(k === "date" || k === "updated_at" || k === "raw_json" || k === "epoch_s"){ return; }
          var label = COLUMN_LABELS[k] || k;
          var fmt;
          if(k.indexOf("sleep_") === 0 && k.indexOf("_min") > 0){ fmt = function(v){ return fmtMin(v); }; }
          else if(k.indexOf("_min") >= 0){ fmt = function(v){ return v == null ? "—" : (Math.round(v) + " 分钟"); }; }
          else if(k.indexOf("_kcal") >= 0 || k === "weight_kg" || k === "weight_bmi" || k === "distance_m"){ fmt = function(v){ return fmtNum(v, 1); }; }
          else if(k.indexOf("_pct") >= 0){ fmt = function(v){ return fmtNum(v, 0) + "%"; }; }
          else { fmt = function(v){ return fmtNum(v, 1); }; }
          cols.push({key:k, label:label, fmt:fmt});
        });
        renderTable($("#dataTable"), rows, cols, "该时间段没有数据");
      }
    } catch(e){ toast(e.message, "bad"); }
  }
  function setDataRange(days){
    $("#dataFrom").value = daysAgo(days - 1);
    $("#dataTo").value = today();
    $$("#dataRangeSeg button").forEach(function(b){
      var active = Number(b.dataset.range) === days;
      b.classList.toggle("active", active);
      b.setAttribute("aria-pressed", String(active));
    });
    loadData();
  }
  var ALL_COLUMNS = ["date","steps","distance_m","sleep_total_min","sleep_deep_min","sleep_rem_min","hr_resting","hr_avg","spo2_avg","stress_avg","weight_kg","active_kcal"];
  var COLUMN_LABELS = {
    steps:"步数", distance_m:"距离(m)", step_calories:"步行千卡", active_kcal:"活动千卡", resting_kcal:"静息千卡",
    intake_kcal:"摄入千卡", total_kcal:"总千卡", hr_avg:"平均心率", hr_min:"最低心率", hr_max:"最高心率", hr_resting:"静息心率",
    sleep_total_min:"睡眠合计（含小睡）", sleep_deep_min:"深睡", sleep_light_min:"浅睡", sleep_rem_min:"REM", sleep_awake_min:"清醒",
    sleep_start:"入睡", sleep_end:"起床", spo2_avg:"血氧均值", spo2_min:"血氧最低", spo2_max:"血氧最高",
    stress_avg:"压力均值", stress_max:"压力最高", stress_relaxed_min:"放松", stress_mild_min:"轻度",
    stress_moderate_min:"中度", stress_severe_min:"重度", activity_count:"活动次数", activity_min:"活动分钟",
    weight_kg:"体重(kg)", weight_bmi:"BMI"
  };

  /* ---------------- sync ---------------- */
  async function loadSchedule(){
    try{
      var s = await api("/schedule");
      $("#schedMode").value = s.mode;
      $("#schedInterval").value = s.interval_minutes || 30;
      $("#schedHour").value = s.hour;
      $("#schedMinute").value = s.minute;
      $("#schedDays").value = String(s.days);
      $("#scheduleHint").textContent = (s.last_run_at ? ("上次自动同步 " + rel(s.last_run_at)) : "尚未自动同步")
        + (s.next_run_at ? (" · 下次 " + new Date(s.next_run_at).toLocaleString()) : "");
      $("#schedMsg").textContent = "";
      toggleSchedule();
    } catch(e){ toast(e.message, "bad"); }
  }
  function toggleSchedule(){
    var interval = $("#schedMode").value === "interval";
    $("#schedDailyWrap").classList.toggle("hidden", interval);
    $("#schedIntervalWrap").classList.toggle("hidden", !interval);
  }
  async function saveSchedule(){
    var body = {
      mode: $("#schedMode").value,
      days: Number($("#schedDays").value),
      hour: Number($("#schedHour").value),
      minute: Number($("#schedMinute").value),
      interval_minutes: Number($("#schedInterval").value)
    };
    try{
      var s = await api("/schedule", {method:"POST", body:body});
      $("#schedMsg").textContent = "已保存，下次自动同步 " + new Date(s.next_run_at).toLocaleString();
      toast("自动同步设置已更新", "ok");
      loadOverview(true); loadSchedule();
    } catch(e){ $("#schedMsg").textContent = e.message; }
  }
  async function startSync(days){
    if(days >= 90){ var ok = await confirmBox("开始同步", "将回填最近 " + days + " 天的数据，可能需要几分钟，期间请勿重复触发。", "开始"); if(!ok){ return; } }
    try{ await api("/sync?days=" + days, {method:"POST", body:{}}); toast("同步已开始", "ok"); loadOverview(); }
    catch(e){ toast(e.message, "bad"); }
  }

  /* ---------------- xiaomi ---------------- */
  async function startXiaomiLogin(){
    $("#btnXiaomiLogin").disabled = true;
    try{ await api("/xiaomi/login", {method:"POST", body:{}}); toast("已请求二维码"); loadOverview(); }
    catch(e){ toast(e.message, "bad"); $("#btnXiaomiLogin").disabled = false; }
  }
  async function resetXiaomiLogin(){
    try{ await api("/xiaomi/login", {method:"DELETE"}); toast("已重置状态"); loadOverview(); }
    catch(e){ toast(e.message, "bad"); }
  }

  function sizeText(v){
    if(v == null) return "—";
    if(v >= 1024*1024) return fmtFloat(v/1024/1024, 2) + " MB";
    return Math.max(1, Math.round(v/1024)) + " KB";
  }

  /* ---------------- backups ---------------- */
  async function loadBackups(){
    try{
      var res = await api("/backups");
      var rows = (res.backups || []).map(function(b){
        return { name:b.name, size:b.size, created_at:b.created_at };
      });
      $("#backupSummary").textContent = "共 " + rows.length + " 个备份，合计 " + sizeText(res.total_size || 0) + "。备份目录在服务器的数据卷内，下载后请离线保存。";
      renderTable($("#backupTable"), rows, [
        {key:"name", label:"文件名"},
        {key:"size", label:"大小", fmt:function(v){ return sizeText(v); }},
        {key:"created_at", label:"创建时间", fmt:function(v){ return new Date(v).toLocaleString(); }},
        {key:"name", label:"操作", raw:true, fmt:function(v){ return '<button class="btn ghost sm" data-dl="'+esc(v)+'">下载</button> <button class="btn ghost sm" data-del="'+esc(v)+'">删除</button>'; }}
      ], "还没有备份");
      $$("[data-dl]").forEach(function(b){ b.onclick = function(){ window.location = "/admin/api/backups/" + encodeURIComponent(b.dataset.dl); }; });
      $$("[data-del]").forEach(function(b){ b.onclick = async function(){
        var ok = await confirmBox("删除备份", "确定删除 " + b.dataset.del + "？此操作不可恢复。", "删除");
        if(!ok){ return; }
        try{ await api("/backups/" + encodeURIComponent(b.dataset.del), {method:"DELETE"}); toast("已删除", "ok"); loadBackups(); }
        catch(e){ toast(e.message, "bad"); }
      }; });
    } catch(e){ toast(e.message, "bad"); }
  }
  async function createBackup(){
    $("#btnBackup").disabled = true;
    try{ var r = await api("/backups", {method:"POST", body:{}}); toast("备份完成：" + r.name, "ok"); loadBackups(); }
    catch(e){ toast(e.message, "bad"); }
    finally{ $("#btnBackup").disabled = false; }
  }

  /* ---------------- settings ---------------- */
  async function loadSettings(){
    try{
      var s = await api("/settings");
      var kv = [
        ["版本", s.version], ["时区", s.timezone],
        ["自动同步", s.schedule ? (s.schedule.mode === "interval" ? ("每 " + s.schedule.interval_minutes + " 分钟") : (String(s.schedule.hour).padStart(2,"0") + ":" + String(s.schedule.minute).padStart(2,"0"))) : "—"],
        ["回填天数", s.backfill_days],
        ["密码来源", s.password_source === "database" ? "后台修改" : ".env"],
        ["REST 限流", s.rate_limit_per_min + " 次/分钟"], ["同步限流", s.sync_rate_limit_per_min + " 次/分钟"],
        ["允许的 Host", (s.allowed_hosts || []).join(", ")],
        ["数据库", s.db_path + "（" + Math.max(1, Math.round(s.db_size/1024)) + " KB）"],
        ["登录态", s.session_present ? "已保存" : "缺失"],
        ["备份目录", s.backup_dir]
      ];
      $("#settingsKv").innerHTML = kv.map(function(p){ return '<div class="k">' + esc(p[0]) + '</div><div class="v">' + esc(p[1]) + '</div>'; }).join("");
      $("#mcpUrlInput").value = location.origin + "/mcp";
      state.prompt = buildPrompt(location.origin + "/mcp");
      $("#musePrompt").textContent = state.prompt;
      loadAudit();
    } catch(e){ toast(e.message, "bad"); }
  }
  function buildPrompt(mcpUrl){
    return "Build a custom integration to my self-hosted health-data service.\n" +
      "Remote MCP server over streamable HTTP: " + mcpUrl + "\n" +
      "Auth: Authorization: Bearer <token>. I will enter the token through the secure credential flow.\n" +
      "Tools: health_status, get_daily_summary, get_daily_metrics, get_sleep, get_steps,\n" +
      "get_heart_rate_daily, get_spo2_daily, get_stress_daily, get_weight, get_calories,\n" +
      "get_workouts, sync_now.\n" +
      "Connect with the official MCP SDK, call get_daily_summary for the last 7 days end to end,\n" +
      "show me the results, set the connector to read-only, and save the integration as a reusable skill.";
  }
  async function changePassword(){
    var current = $("#pwCurrent").value, next = $("#pwNew").value, again = $("#pwConfirm").value;
    var msg = $("#pwMsg");
    msg.textContent = "";
    if(next.length < 8){ msg.textContent = "新密码至少需要 8 个字符"; return; }
    if(next !== again){ msg.textContent = "两次输入的新密码不一致"; return; }
    var ok = await confirmBox("修改管理密码", "修改后其他浏览器会退出登录，当前页面自动续期。确定要修改吗？", "修改密码");
    if(!ok){ return; }
    try{
      await api("/password", {method:"POST", body:{current:current, new:next}});
      $("#pwCurrent").value = ""; $("#pwNew").value = ""; $("#pwConfirm").value = "";
      msg.textContent = "已修改；其他浏览器会话已失效，当前页面自动续期。";
      toast("管理密码已更新", "ok");
      loadSettings();
    } catch(e){ msg.textContent = e.message; }
  }

  async function revealToken(){
    if(state.token){ $("#tokenInput").value = "••••••••••••••••"; state.token = ""; $("#btnReveal").textContent = "显示"; return; }
    try{ var r = await api("/token"); state.token = r.token; $("#tokenInput").value = r.token; $("#btnReveal").textContent = "隐藏"; }
    catch(e){ toast(e.message, "bad"); }
  }
  async function loadAudit(){
    try{
      var res = await api("/audit?limit=50");
      renderTable($("#auditTable"), (res.entries||[]).map(function(e){ return {at:e.at, action:e.action, detail:e.detail, ip:e.ip}; }), [
        {key:"at", label:"时间", fmt:function(v){ return new Date(v).toLocaleString(); }},
        {key:"action", label:"操作"}, {key:"detail", label:"详情"}, {key:"ip", label:"IP"}
      ], "暂无审计记录");
    } catch(e){ toast(e.message, "bad"); }
  }

  /* ---------------- routing ---------------- */
  function setActiveNav(page){
    $$(".site-nav a").forEach(function(a){
      var active = a.dataset.nav === page;
      a.classList.toggle("active", active);
      if(active){ a.setAttribute("aria-current", "page"); }
      else { a.removeAttribute("aria-current"); }
    });
    $("#navMore").classList.toggle("active", !$(".nav-primary a.active"));
  }
  function closeMobileMenu(restoreFocus){
    var toggle = $("#navMore");
    if(toggle.getAttribute("aria-expanded") !== "true"){ return; }
    toggle.setAttribute("aria-expanded", "false");
    if(restoreFocus){ toggle.focus({preventScroll:true}); }
  }
  function bindMobileMenu(){
    var toggle = $("#navMore"), tools = $("#navTools");
    toggle.onclick = function(){
      toggle.setAttribute("aria-expanded", String(toggle.getAttribute("aria-expanded") !== "true"));
    };
    document.addEventListener("click", function(e){
      if(!toggle.contains(e.target) && !tools.contains(e.target)){ closeMobileMenu(); }
    });
    tools.addEventListener("click", function(e){
      if(e.target.closest("a")){ closeMobileMenu(true); }
    });
    document.addEventListener("keydown", function(e){
      if(e.key === "Escape"){ closeMobileMenu(true); }
    });
    window.matchMedia("(max-width: 740px)").addEventListener("change", function(e){
      if(!e.matches){ closeMobileMenu(); }
    });
  }
  function route(){
    closeMobileMenu();
    var raw = location.hash.replace(/^#\//, "");
    var page = Object.hasOwn(PAGE_META, raw) ? raw : "overview";
    if(page !== state.page){ window.scrollTo(0, 0); }
    state.page = page;
    $$(".page").forEach(function(p){ p.classList.add("hidden"); });
    var el = $("#page-" + page); if(el){ el.classList.remove("hidden"); }
    $("#pageTitle").textContent = PAGE_META[page][0];
    $("#pageCrumb").textContent = PAGE_META[page][1];
    $(".page-heading").dataset.page = page;
    setActiveNav(page);
    if(page === "sleep"){ loadSleep(); }
    if(page === "data"){ initDataPage(); }
    if(page === "backups"){ loadBackups(); }
    if(page === "settings"){ loadSettings(); }
    if(page === "sync"){ loadSchedule(); }
    loadOverview(page !== "overview" && page !== "sync" && page !== "xiaomi");
  }

  /* ---------------- boot ---------------- */
  function refreshPage(){
    closeMobileMenu(true);
    if(state.page === "data"){ loadData(); loadOverview(true); }
    else { route(); }
  }
  async function logout(){
    closeMobileMenu(true);
    try{ await api("/logout", {method:"POST", body:{}}); }catch(e){}
    location.reload();
  }
  function bind(){
    bindMobileMenu();
    $("#loginForm").onsubmit = function(e){ e.preventDefault(); login(); };
    $$('[data-admin-action="logout"]').forEach(function(button){ button.onclick = logout; });
    $$('[data-admin-action="refresh"]').forEach(function(button){ button.onclick = refreshPage; });
    $("#dataFilters").onsubmit = function(e){ e.preventDefault(); loadData(); };
    $("#btnExport").onclick = function(){
      var domain = $("#dataDomain").value, from = $("#dataFrom").value, to = $("#dataTo").value;
      window.location = "/admin/api/export.csv?domain=" + encodeURIComponent(domain) + "&start=" + from + "&end=" + to;
    };
    $$("#syncSeg button").forEach(function(b){ b.onclick = function(){ startSync(Number(b.dataset.days)); }; });
    $("#schedMode").onchange = toggleSchedule;
    $("#btnSaveSchedule").onclick = saveSchedule;
    $$("#dataRangeSeg button").forEach(function(b){ b.onclick = function(){ setDataRange(Number(b.dataset.range)); }; });
    $$("#sleepRange button").forEach(function(b){
      b.onclick = function(){
        state.sleepDays = Number(b.dataset.days);
        $$("#sleepRange button").forEach(function(button){
          var active = button === b;
          button.classList.toggle("active", active);
          button.setAttribute("aria-pressed", String(active));
        });
        loadSleep();
      };
    });
    $("#btnXiaomiLogin").onclick = startXiaomiLogin;
    $("#btnXiaomiReset").onclick = resetXiaomiLogin;
    $("#btnBackup").onclick = createBackup;
    $("#btnBackupRefresh").onclick = loadBackups;
    $("#btnReveal").onclick = revealToken;
    $("#btnChangePw").onclick = changePassword;
    $("#btnCopyPrompt").onclick = function(){ copyText(state.prompt, "提示词已复制"); };
    $("#btnAuditRefresh").onclick = loadAudit;
    $$("[data-copy]").forEach(function(b){
      b.onclick = async function(){
        if(b.dataset.copy === "tokenInput" && !state.token){ await revealToken(); }
        copyText($("#" + b.dataset.copy).value, "已复制");
      };
    });
    window.addEventListener("hashchange", route);
  }

  async function copyText(text, msg){
    try{ await navigator.clipboard.writeText(text || ""); toast(msg, "ok"); }
    catch(e){ toast("复制失败，请手动选择", "bad"); }
  }

  async function login(){
    $("#loginError").textContent = "";
    $("#btnLogin").disabled = true;
    try{
      await api("/session", {method:"POST", body:{password: $("#password").value}});
      $("#password").value = "";
      showApp(); route(); startPolling();
    } catch(e){ $("#loginError").textContent = e.message; }
    finally { $("#btnLogin").disabled = false; }
  }

  var pollTimer = null;
  function startPolling(){
    clearInterval(pollTimer);
    pollTimer = setInterval(function(){
      if(state.page === "overview" || state.page === "sync" || state.page === "xiaomi"){ loadOverview(true); }
    }, 10000);
  }

  async function boot(){
    bind();
    try{
      var s = await api("/session");
      if(!s.authenticated){ showLogin(); $("#password").focus(); return; }
      showApp(); route(); startPolling();
    } catch(e){
      showLogin();
      $("#password").focus();
    }
  }
  boot();
})();
</script>
</body>
</html>
'''
