(function () {
  "use strict";

  const C = window.HBCharts;
  const esc = C.escapeHtml;
  const fmtMin = C.fmtMin;
  const fmtNum = C.fmtNum;

  const DOMAIN_META = {
    steps: { label: "步数", sub: "steps" },
    sleep: { label: "睡眠", sub: "sleep" },
    heart_rate_daily: { label: "心率", sub: "heart_rate_daily" },
    spo2_daily: { label: "血氧", sub: "spo2_daily" },
    stress_daily: { label: "压力", sub: "stress_daily" },
    consumption: { label: "热量消耗", sub: "consumption" },
    activity_daily: { label: "日常活动", sub: "activity_daily" },
    weight: { label: "体重体脂", sub: "weight" },
    workouts: { label: "运动记录", sub: "workouts" },
  };

  const EXPLORER_DOMAINS = [
    { id: "all", label: "全部指标" },
    { id: "steps", label: "步数" },
    { id: "sleep", label: "睡眠" },
    { id: "heart-rate", label: "心率" },
    { id: "spo2", label: "血氧" },
    { id: "stress", label: "压力" },
    { id: "weight", label: "体重" },
    { id: "activity", label: "活动" },
    { id: "calories", label: "热量" },
    { id: "workouts", label: "运动记录" },
  ];

  const COLUMN_LABELS = {
    date: "日期",
    steps: "步数",
    distance_m: "距离",
    step_calories: "步行热量",
    active_kcal: "活动消耗",
    resting_kcal: "静息代谢",
    intake_kcal: "摄入热量",
    total_kcal: "总消耗",
    hr_avg: "平均心率",
    hr_min: "最低心率",
    hr_max: "最高心率",
    hr_resting: "静息心率",
    sleep_total_min: "睡眠合计",
    sleep_deep_min: "深睡",
    sleep_light_min: "浅睡",
    sleep_rem_min: "REM",
    sleep_awake_min: "清醒",
    sleep_start: "入睡时间",
    sleep_end: "醒来时间",
    spo2_avg: "平均血氧",
    spo2_min: "最低血氧",
    spo2_max: "最高血氧",
    stress_avg: "平均压力",
    stress_max: "最高压力",
    stress_relaxed_min: "放松时长",
    stress_mild_min: "轻度压力",
    stress_moderate_min: "中度压力",
    stress_severe_min: "偏高压力",
    activity_count: "活动次数",
    activity_min: "活动时长",
    weight_kg: "体重",
    weight_bmi: "BMI",
    sport: "运动类型",
    start_time: "开始时间",
    end_time: "结束时间",
    duration_s: "时长",
    avg_hr: "平均心率",
    max_hr: "最高心率",
  };

  const MCP_TOOLS = [
    { name: "health_status", desc: "同步状态、会话健康与记录行数", mode: "read" },
    { name: "get_daily_summary", desc: "近 N 天结构化健康摘要与 Markdown", mode: "read" },
    { name: "get_daily_metrics", desc: "按日期区间与字段筛选综合日指标", mode: "read" },
    { name: "get_sleep", desc: "每日睡眠总量、主睡眠阶段与小睡明细", mode: "read" },
    { name: "get_steps", desc: "每日步数、步行距离与消耗热量", mode: "read" },
    { name: "get_heart_rate_daily", desc: "每日平均、最低、最高与静息心率", mode: "read" },
    { name: "get_spo2_daily", desc: "每日平均、最低与最高血氧饱和度", mode: "read" },
    { name: "get_stress_daily", desc: "每日压力均值及各等级持续分钟数", mode: "read" },
    { name: "get_weight", desc: "体重与 BMI 测量记录", mode: "read" },
    { name: "get_calories", desc: "静息、活动、摄入与总热量数据", mode: "read" },
    { name: "get_workouts", desc: "单次运动类型、时长、距离与心率", mode: "read" },
    { name: "sync_now", desc: "立即从小米云端增量拉取最新数据", mode: "sync" },
  ];

  const VIEW_META = {
    overview: { title: "健康概览", sub: "核心体征、多维趋势与 Meta Muse 摘要视角" },
    sleep: { title: "睡眠分析", sub: "主睡眠阶段构成、小睡拆分与逐日剖面" },
    data: { title: "数据明细", sub: "全数据域按日检索与 CSV 导出" },
    sync: { title: "同步与账号", sub: "小米账号扫码授权、手动同步与定时计划" },
    connect: { title: "Muse 接入", sub: "远程 MCP / OpenAPI 端点、凭据与接入指引" },
    system: { title: "备份与系统", sub: "数据快照、运行参数、密码安全与审计日志" },
  };

  const state = {
    authed: false,
    view: "overview",
    overview: null,
    trendMetric: "steps",
    trendDays: 30,
    timeline: null,
    summaryDays: 7,
    summaryData: null,
    summaryRawMode: false,
    sleepDays: 30,
    sleepData: null,
    sleepSelectedDate: null,
    sleepUserPicked: false,
    explorer: {
      domain: "all",
      start: "",
      end: "",
      userDates: false,
      query: "",
      data: null,
      loading: false,
    },
    tokenData: null,
    tokenVisible: false,
    connectSnippetTab: "muse",
    backupsData: null,
    settingsData: null,
    auditData: null,
    auditFilter: "all",
    syncPollTimer: null,
    qrPollTimer: null,
    modalResolver: null,
  };

  // --- Utilities ---

  async function api(path, opts) {
    const cfg = opts || {};
    const method = (cfg.method || "GET").toUpperCase();
    const headers = Object.assign({}, cfg.headers || {});
    if (method !== "GET" && method !== "HEAD") {
      headers["X-Requested-With"] = "XMLHttpRequest";
    }
    let body = cfg.body;
    if (body !== undefined && typeof body !== "string") {
      headers["Content-Type"] = "application/json";
      body = JSON.stringify(body);
    }
    const res = await fetch(path, {
      method,
      headers,
      body,
      credentials: "same-origin",
      cache: "no-store",
    });
    const text = await res.text();
    let json = null;
    try {
      json = text ? JSON.parse(text) : null;
    } catch (_) {
      json = null;
    }
    if (res.status === 401 && !cfg.allowUnauth) {
      handleSessionLost();
      throw new Error("登录状态已失效，请重新登录");
    }
    if (!res.ok) {
      const msg = (json && (json.error || json.detail)) || `请求失败 (${res.status})`;
      const err = new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
      err.status = res.status;
      throw err;
    }
    return json;
  }

  function toast(message, kind) {
    const stack = document.getElementById("toast-stack");
    if (!stack) return;
    const el = document.createElement("div");
    el.className = `toast ${kind || "info"}`;
    el.textContent = message;
    stack.appendChild(el);
    setTimeout(() => {
      el.style.opacity = "0";
      el.style.transition = "opacity 0.2s ease";
      setTimeout(() => el.remove(), 220);
    }, 3200);
  }

  function confirmAction(title, body, confirmLabel, danger) {
    return new Promise((resolve) => {
      const modal = document.getElementById("confirm-modal");
      document.getElementById("modal-title").textContent = title;
      document.getElementById("modal-body").textContent = body;
      const okBtn = document.getElementById("modal-ok");
      okBtn.textContent = confirmLabel || "确认";
      okBtn.className = danger ? "btn btn-danger" : "btn btn-primary";
      state.modalResolver = resolve;
      modal.classList.remove("hidden");
    });
  }

  function closeModal(result) {
    const modal = document.getElementById("confirm-modal");
    modal.classList.add("hidden");
    if (state.modalResolver) {
      const fn = state.modalResolver;
      state.modalResolver = null;
      fn(Boolean(result));
    }
  }

  async function copyText(text, label) {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const ta = document.createElement("textarea");
        ta.value = text;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        ta.remove();
      }
      toast(`已复制${label || "内容"}`, "ok");
    } catch (_) {
      toast("复制失败，请手动选中复制", "danger");
    }
  }

  function fmtRelative(iso) {
    if (!iso) return "尚未同步";
    const dt = new Date(iso);
    if (Number.isNaN(dt.getTime())) return iso;
    const diffSec = Math.round((Date.now() - dt.getTime()) / 1000);
    if (diffSec < 0) {
      const ahead = Math.abs(diffSec);
      if (ahead < 60) return `${ahead} 秒后`;
      if (ahead < 3600) return `${Math.round(ahead / 60)} 分钟后`;
      if (ahead < 86400) return `${Math.round(ahead / 3600)} 小时后`;
      return `${Math.round(ahead / 86400)} 天后`;
    }
    if (diffSec < 45) return "刚刚";
    if (diffSec < 3600) return `${Math.round(diffSec / 60)} 分钟前`;
    if (diffSec < 86400) return `${Math.round(diffSec / 3600)} 小时前`;
    return `${Math.round(diffSec / 86400)} 天前`;
  }

  function fmtDateTime(iso) {
    if (!iso) return "—";
    const dt = new Date(iso);
    if (Number.isNaN(dt.getTime())) return iso;
    const y = dt.getFullYear();
    const m = String(dt.getMonth() + 1).padStart(2, "0");
    const d = String(dt.getDate()).padStart(2, "0");
    const hh = String(dt.getHours()).padStart(2, "0");
    const mm = String(dt.getMinutes()).padStart(2, "0");
    return `${y}-${m}-${d} ${hh}:${mm}`;
  }

  function fmtClock(iso) {
    if (!iso) return "—";
    const m = String(iso).match(/T(\d{2}:\d{2})/);
    return m ? m[1] : String(iso).slice(11, 16) || iso;
  }

  function fmtBytes(bytes) {
    const n = Number(bytes) || 0;
    if (n < 1024) return `${n} B`;
    if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
    if (n < 1024 * 1024 * 1024) return `${(n / (1024 * 1024)).toFixed(2)} MB`;
    return `${(n / (1024 * 1024 * 1024)).toFixed(2)} GB`;
  }

  function isoOffsetDays(baseIso, deltaDays) {
    const base = baseIso ? new Date(baseIso + "T00:00:00") : new Date();
    base.setDate(base.getDate() + deltaDays);
    const y = base.getFullYear();
    const m = String(base.getMonth() + 1).padStart(2, "0");
    const d = String(base.getDate()).padStart(2, "0");
    return `${y}-${m}-${d}`;
  }

  function sportLabel(raw) {
    const s = String(raw || "").trim();
    const map = {
      "Outdoor run": "户外跑步",
      "Indoor run": "室内跑步",
      "Treadmill": "跑步机",
      "Outdoor walk": "户外健走",
      "Walking": "健走",
      "Outdoor cycling": "户外骑行",
      "Indoor cycling": "室内单车",
      "Cycling": "骑行",
      "Pool swim": "泳池游泳",
      "Swimming": "游泳",
      "Hiking": "徒步登山",
      "Strength training": "力量训练",
      "Freestyle": "自由训练",
      "Yoga": "瑜伽",
      "Badminton": "羽毛球",
    };
    return map[s] || s || "运动记录";
  }

  function renderSimpleMarkdown(md) {
    if (!md) return "<p>暂无摘要内容。</p>";
    const lines = String(md).split(/\r?\n/);
    let html = "";
    let inList = false;
    lines.forEach((raw) => {
      const line = raw.trim();
      if (!line) {
        if (inList) {
          html += "</ul>";
          inList = false;
        }
        return;
      }
      if (line.startsWith("# ")) {
        if (inList) { html += "</ul>"; inList = false; }
        html += `<h1>${esc(line.slice(2))}</h1>`;
      } else if (line.startsWith("## ")) {
        if (inList) { html += "</ul>"; inList = false; }
        html += `<h2>${esc(line.slice(3))}</h2>`;
      } else if (line.startsWith("- ")) {
        if (!inList) { html += "<ul>"; inList = true; }
        const friendly = line
          .slice(2)
          .replace(/\d{4}-\d{2}-\d{2}T(\d{2}:\d{2}):\d{2}[+-]\d{2}:\d{2}/g, "$1");
        html += `<li>${esc(friendly)}</li>`;
      } else if (line.startsWith("|")) {
        // Compact daily table inside markdown is redundant with interactive charts; show clean monospace row
        if (inList) { html += "</ul>"; inList = false; }
        if (/^\|\s*---/.test(line)) return;
        const cells = line.split("|").slice(1, -1).map((c) => c.trim());
        html += `<div style="display:grid;grid-template-columns:1.4fr repeat(${Math.max(1, cells.length - 1)},1fr);gap:6px;padding:4px 0;border-bottom:1px solid rgba(21,24,30,0.06);font-size:12px" class="num">${cells
          .map((c, idx) => `<span style="${idx === 0 ? "color:var(--ink-secondary);font-weight:600" : "text-align:right"}">${esc(c)}</span>`)
          .join("")}</div>`;
      } else {
        if (inList) { html += "</ul>"; inList = false; }
        html += `<p style="margin:6px 0">${esc(line)}</p>`;
      }
    });
    if (inList) html += "</ul>";
    return html;
  }

  // --- Shell & Auth ---

  function showLogin() {
    state.authed = false;
    stopPolls();
    document.getElementById("login-stage").classList.remove("hidden");
    document.getElementById("app-shell").classList.add("hidden");
    const pwd = document.getElementById("login-password");
    if (pwd) setTimeout(() => pwd.focus(), 40);
  }

  function showApp() {
    state.authed = true;
    document.getElementById("login-stage").classList.add("hidden");
    document.getElementById("app-shell").classList.remove("hidden");
  }

  function handleSessionLost() {
    if (state.authed) {
      toast("登录会话已过期，请重新输入管理密码", "info");
    }
    showLogin();
  }

  function stopPolls() {
    if (state.syncPollTimer) {
      clearInterval(state.syncPollTimer);
      state.syncPollTimer = null;
    }
    if (state.qrPollTimer) {
      clearInterval(state.qrPollTimer);
      state.qrPollTimer = null;
    }
  }

  function currentRouteFromHash() {
    const raw = (window.location.hash || "").replace(/^#/, "").trim();
    return VIEW_META[raw] ? raw : "overview";
  }

  function navigate(view) {
    if (!VIEW_META[view]) view = "overview";
    state.view = view;
    if (window.location.hash !== `#${view}`) {
      history.replaceState(null, "", `#${view}`);
    }
    document.querySelectorAll(".nav-item[data-view]").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.view === view);
    });
    const meta = VIEW_META[view];
    document.getElementById("topbar-title").textContent = meta.title;
    document.getElementById("topbar-sub").textContent = meta.sub;
    closeMobileSidebar();
    renderCurrentView();
    ensureViewData(view);
  }

  function closeMobileSidebar() {
    document.getElementById("sidebar").classList.remove("open");
    document.getElementById("sidebar-backdrop").classList.remove("open");
  }

  async function loadOverview(silent) {
    try {
      const ov = await api("/admin/api/overview");
      state.overview = ov;

      const extra = [];
      if (state.trendDays === 30) {
        state.timeline = ov.timeline;
      } else {
        extra.push(
          api(`/admin/api/timeline?days=${state.trendDays}`).then((d) => {
            state.timeline = d;
          })
        );
      }
      if (state.summaryDays === 7) {
        state.summaryData = ov.summary;
      } else {
        extra.push(
          api(`/admin/api/summary?days=${state.summaryDays}`).then((d) => {
            state.summaryData = d;
          })
        );
      }
      if (state.sleepDays === 30) {
        state.sleepData = ov.sleep;
      } else {
        extra.push(
          api(`/admin/api/sleep?days=${state.sleepDays}`).then((d) => {
            state.sleepData = d;
          })
        );
      }
      if (extra.length) {
        await Promise.all(extra);
      }
      pickDefaultSleepDate();

      if (ov.bridge && ov.bridge.today && (!state.explorer.end || !state.explorer.userDates)) {
        state.explorer.end = ov.bridge.today;
        state.explorer.start = isoOffsetDays(ov.bridge.today, -13);
      }
      updateChrome();
      if (ov.sync && ov.sync.state === "running") startSyncPoll();
      if (ov.login && (ov.login.state === "starting" || ov.login.state === "pending")) startQrPoll();
      renderCurrentView();
      if (!silent) toast("数据已刷新", "ok");
    } catch (err) {
      if (state.authed) toast(err.message || "加载概览失败", "danger");
    }
  }

  function pickDefaultSleepDate() {
    const days = (state.sleepData && state.sleepData.days) || [];
    if (!days.length) {
      state.sleepSelectedDate = null;
      return;
    }
    if (state.sleepUserPicked && state.sleepSelectedDate && days.some((d) => d.date === state.sleepSelectedDate)) {
      return;
    }
    state.sleepSelectedDate = days[days.length - 1].date;
  }

  async function ensureViewData(view) {
    if (!state.overview) return;
    if (view === "data" && !state.explorer.data && !state.explorer.loading) {
      await loadExplorer();
    } else if (view === "connect" && !state.tokenData) {
      try {
        state.tokenData = await api("/admin/api/token");
        renderCurrentView();
      } catch (err) {
        toast(err.message, "danger");
      }
    } else if (view === "system") {
      try {
        const [backups, settings, audit] = await Promise.all([
          api("/admin/api/backups"),
          api("/admin/api/settings"),
          api("/admin/api/audit?limit=80"),
        ]);
        state.backupsData = backups;
        state.settingsData = settings;
        state.auditData = audit;
        renderCurrentView();
      } catch (err) {
        toast(err.message, "danger");
      }
    }
  }

  function updateChrome() {
    const ov = state.overview;
    if (!ov) return;
    const expired = Boolean(ov.session && ov.session.expired);
    const syncing = Boolean(ov.sync && ov.sync.state === "running");
    const domains = (ov.bridge && ov.bridge.domains) || {};
    const domainErrs = Object.values(domains).filter((d) => d && d.last_error).length;

    const verEl = document.getElementById("sidebar-version");
    if (verEl) verEl.textContent = `v${ov.version || "0.1"}`;
    const tzEl = document.getElementById("sidebar-tz-label");
    if (tzEl) tzEl.textContent = ov.timezone || "Asia/Shanghai";

    const card = document.getElementById("sidebar-status");
    const dot = document.getElementById("sidebar-dot");
    const label = document.getElementById("sidebar-status-label");
    const meta = document.getElementById("sidebar-status-meta");
    if (card && dot && label && meta) {
      card.classList.toggle("is-warn", expired || domainErrs > 0);
      if (syncing) {
        dot.className = "pulse-dot busy";
        label.textContent = "正在同步小米云…";
      } else if (expired) {
        dot.className = "pulse-dot danger";
        label.textContent = "小米会话已过期";
      } else if (domainErrs > 0) {
        dot.className = "pulse-dot warn";
        label.textContent = `部分域异常 (${domainErrs})`;
      } else {
        dot.className = "pulse-dot ok";
        label.textContent = "小米云桥接正常";
      }
      const lastDate = (ov.session && ov.session.last_date) || "暂无数据";
      const rows = (ov.session && ov.session.daily_rows) || 0;
      const wRows = (ov.session && ov.session.workout_rows) || 0;
      meta.innerHTML = `<span>最新数据：${esc(lastDate)}</span><span class="num">已存 ${rows} 天 · ${wRows} 次运动</span>`;
    }

    const syncBadge = document.getElementById("nav-sync-badge");
    if (syncBadge) {
      if (syncing) {
        syncBadge.textContent = "同步中";
        syncBadge.className = "nav-badge";
        syncBadge.classList.remove("hidden");
      } else if (expired) {
        syncBadge.textContent = "需扫码";
        syncBadge.className = "nav-badge warn";
        syncBadge.classList.remove("hidden");
      } else {
        syncBadge.classList.add("hidden");
      }
    }

    const pillDot = document.getElementById("topbar-sync-dot");
    const pillText = document.getElementById("topbar-sync-text");
    if (pillDot && pillText) {
      if (syncing) {
        pillDot.className = "pulse-dot busy";
        pillText.textContent = `同步近 ${ov.sync.days || 7} 天中…`;
      } else if (expired) {
        pillDot.className = "pulse-dot danger";
        pillText.textContent = "登录已过期 · 点此扫码";
      } else {
        pillDot.className = "pulse-dot ok";
        pillText.textContent = `上次同步：${fmtRelative(ov.session && ov.session.last_sync_at)}`;
      }
    }

    const quickBtn = document.getElementById("btn-quick-sync");
    if (quickBtn) {
      quickBtn.disabled = syncing;
      quickBtn.innerHTML = syncing
        ? `<span class="spinner"></span>同步中`
        : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 0 1-15 6.7L3 16"/><path d="M3 12a9 9 0 0 1 15-6.7L21 8"/><polyline points="21 3 21 8 16 8"/><polyline points="3 21 3 16 8 16"/></svg>立即同步`;
    }
  }

  // --- Polling ---

  function startSyncPoll() {
    if (state.syncPollTimer) return;
    state.syncPollTimer = setInterval(async () => {
      try {
        const s = await api("/admin/api/sync");
        if (state.overview) state.overview.sync = s;
        updateChrome();
        if (state.view === "sync") renderCurrentView();
        if (s.state !== "running") {
          clearInterval(state.syncPollTimer);
          state.syncPollTimer = null;
          if (s.state === "done") {
            const errCnt = (s.result && s.result.errors && s.result.errors.length) || 0;
            toast(errCnt ? `同步完成，但有 ${errCnt} 个域提示异常` : "同步完成，数据已更新", errCnt ? "info" : "ok");
            state.sleepUserPicked = false;
            state.explorer.data = null;
            await loadOverview(true);
            await ensureViewData(state.view);
          } else if (s.state === "error") {
            toast(`同步失败：${s.error || "未知错误"}`, "danger");
            await loadOverview(true);
          }
        }
      } catch (_) {
        clearInterval(state.syncPollTimer);
        state.syncPollTimer = null;
      }
    }, 1800);
  }

  function startQrPoll() {
    if (state.qrPollTimer) return;
    state.qrPollTimer = setInterval(async () => {
      try {
        const st = await api("/admin/api/xiaomi/login");
        if (state.overview) state.overview.login = st;
        if (state.view === "sync") renderCurrentView();
        if (st.state !== "starting" && st.state !== "pending") {
          clearInterval(state.qrPollTimer);
          state.qrPollTimer = null;
          if (st.state === "success") {
            toast("小米账号扫码登录成功！", "ok");
            await loadOverview(true);
          }
        }
      } catch (_) {
        clearInterval(state.qrPollTimer);
        state.qrPollTimer = null;
      }
    }, 1500);
  }

  async function triggerSync(days) {
    try {
      const res = await api(`/admin/api/sync?days=${encodeURIComponent(days)}`, { method: "POST" });
      if (state.overview) state.overview.sync = res;
      updateChrome();
      if (state.view === "sync") renderCurrentView();
      toast(`已启动近 ${days} 天增量同步`, "info");
      startSyncPoll();
    } catch (err) {
      toast(err.message || "启动同步失败", "danger");
    }
  }

  // --- View Render Dispatcher ---

  function renderCurrentView() {
    const root = document.getElementById("view-root");
    if (!root) return;
    if (!state.overview) {
      root.innerHTML = `<div class="card"><div class="empty-state"><span class="spinner spinner-lg"></span><strong>正在载入健康数据…</strong></div></div>`;
      return;
    }
    if (state.view === "overview") renderOverview(root);
    else if (state.view === "sleep") renderSleepView(root);
    else if (state.view === "data") renderExplorerView(root);
    else if (state.view === "sync") renderSyncView(root);
    else if (state.view === "connect") renderConnectView(root);
    else if (state.view === "system") renderSystemView(root);
  }

  // =========================================================================
  // 1. Overview View
  // =========================================================================

  function renderOverview(root) {
    const ov = state.overview;
    const sum = (ov.summary && ov.summary.overview) || {};
    const tl = state.timeline || ov.timeline || {};
    const series = tl.series || {};
    const last7 = (arr) => (arr || []).slice(-7);

    const expired = Boolean(ov.session && ov.session.expired);
    const domainErrs = Object.values((ov.bridge && ov.bridge.domains) || {}).filter((d) => d && d.last_error);

    let alertHtml = "";
    if (expired) {
      alertHtml = `<div class="alert-banner danger">
        <div class="alert-banner-left">
          <span class="pulse-dot danger"></span>
          <div>
            <div class="alert-banner-title">小米云端登录会话已失效</div>
            <div class="alert-banner-text">本地历史数据仍可供 Meta Muse 读取，但需重新扫码以恢复自动同步。</div>
          </div>
        </div>
        <button class="btn btn-primary btn-sm" data-goto="sync">前往扫码登录</button>
      </div>`;
    } else if (domainErrs.length) {
      alertHtml = `<div class="alert-banner">
        <div class="alert-banner-left">
          <span class="pulse-dot warn"></span>
          <div>
            <div class="alert-banner-title">有 ${domainErrs.length} 个数据域在最近一次同步时发生错误</div>
            <div class="alert-banner-text">${esc(domainErrs[0].domain)}：${esc(domainErrs[0].last_error)}</div>
          </div>
        </div>
        <button class="btn btn-sm" data-goto="sync">查看详情</button>
      </div>`;
    }

    // 7-day average sleep stage split for donut ring
    const recentMetrics = (ov.summary && ov.summary.daily) || [];
    const avgOf = (key) => {
      const vals = recentMetrics.map((r) => r[key]).filter((v) => v != null);
      return vals.length ? vals.reduce((a, b) => a + Number(b), 0) / vals.length : 0;
    };
    const avgDeep = sum.sleep_deep_avg_min != null ? sum.sleep_deep_avg_min : avgOf("sleep_deep_min");
    const avgLight = avgOf("sleep_light_min");
    const avgRem = sum.sleep_rem_avg_min != null ? sum.sleep_rem_avg_min : avgOf("sleep_rem_min");
    const stageSum = avgDeep + avgLight + avgRem;
    const pct = (v) => (stageSum > 0 ? `${Math.round((v / stageSum) * 100)}%` : "—");

    const latestSleep = sum.sleep_latest;
    const latestDetail = latestSleep && latestSleep.sleep_details;
    let latestSleepBlock = `<div class="sleep-latest-well"><div class="sleep-latest-head"><span>最近一晚睡眠</span></div><div class="field-hint">暂无睡眠记录</div></div>`;
    if (latestSleep) {
      const spanTxt = latestSleep.start ? `${fmtClock(latestSleep.start)} → ${fmtClock(latestSleep.end)}` : "无起止时刻";
      let napPill = "";
      if (latestDetail && latestDetail.nap_min) {
        napPill = `<span class="badge badge-warn">含小睡 ${esc(fmtMin(latestDetail.nap_min))} (${latestDetail.naps.length}次)</span>`;
      } else if (latestDetail && latestDetail.detail_status === "complete") {
        napPill = `<span class="badge badge-ok">无小睡 · 明细完整</span>`;
      }
      latestSleepBlock = `<div class="sleep-latest-well">
        <div class="sleep-latest-head">
          <span>最近记录 · ${esc(latestSleep.date)}</span>
          <span class="mono">${esc(spanTxt)}</span>
        </div>
        <div class="sleep-latest-main">
          <span class="num">${esc(fmtMin(latestSleep.asleep_min))}</span>
          ${napPill}
        </div>
        <div class="sleep-latest-sub">
          ${latestDetail && latestDetail.main ? `<span>主睡眠 <strong>${esc(fmtMin(latestDetail.main.asleep_min))}</strong></span>` : ""}
          <button class="btn btn-ghost btn-sm" style="margin-left:auto" data-goto="sleep">睡眠分析 →</button>
        </div>
      </div>`;
    }

    // Trend stats bar
    const metricKey = state.trendMetric === "sleep" ? "sleep_total_min" : state.trendMetric;
    const mVals = (series[metricKey] || []).filter((v) => v != null).map(Number);
    const fmtMetricVal = (v) => {
      if (v == null || Number.isNaN(v)) return "—";
      if (state.trendMetric === "sleep") return fmtMin(v);
      if (state.trendMetric === "steps") return `${fmtNum(v, 0)} 步`;
      if (state.trendMetric === "hr_resting") return `${Math.round(v)} bpm`;
      if (state.trendMetric === "spo2_avg") return `${v.toFixed(1)}%`;
      if (state.trendMetric === "stress_avg") return `${Math.round(v)}`;
      return `${fmtNum(v, 0)} kcal`;
    };
    const mAvg = mVals.length ? mVals.reduce((a, b) => a + b, 0) / mVals.length : null;
    const mMax = mVals.length ? Math.max(...mVals) : null;
    const mMin = mVals.length ? Math.min(...mVals) : null;

    // Recent workouts
    const workouts = ov.recent_workouts || [];
    const workoutHtml = workouts.length
      ? `<div class="workout-list">${workouts
          .map((w) => {
            const km = w.distance_m ? `${(Number(w.distance_m) / 1000).toFixed(2)} km` : `${Math.round((w.duration_s || 0) / 60)} 分钟`;
            const subParts = [];
            if (w.distance_m) subParts.push(`${Math.round((w.duration_s || 0) / 60)} 分钟`);
            if (w.active_kcal) subParts.push(`${Math.round(w.active_kcal)} kcal`);
            if (w.avg_hr) subParts.push(`均心率 ${Math.round(w.avg_hr)}`);
            return `<div class="workout-item">
              <div class="workout-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="15" cy="5" r="2"/><path d="M7 21l3-6 4 2 2 4"/><path d="M6 12l4-3 4 2 4-3"/></svg>
              </div>
              <div style="min-width:0">
                <div class="workout-title">${esc(sportLabel(w.sport))}</div>
                <div class="workout-time num">${esc(w.date || "")} ${w.start_time ? esc(fmtClock(w.start_time)) : ""}</div>
              </div>
              <div class="workout-metrics">
                <div>
                  <div class="workout-metric-main">${esc(km)}</div>
                  <div class="workout-metric-sub">${esc(subParts.join(" · ") || "已完成")}</div>
                </div>
              </div>
            </div>`;
          })
          .join("")}</div>`
      : `<div class="empty-state"><strong>近期暂无运动记录</strong><p>小米手环/手表同步运动记录后将显示在这里。</p></div>`;

    const summaryObj = state.summaryData || ov.summary || {};
    const summaryContent = state.summaryRawMode
      ? `<pre class="md-raw">${esc(summaryObj.markdown || "暂无摘要")}</pre>`
      : renderSimpleMarkdown(summaryObj.markdown || "");

    const kpiStepsBest = sum.steps_best ? `最高 ${fmtNum(sum.steps_best.steps, 0)} (${sum.steps_best.date.slice(5)})` : "近 7 日统计";
    const kpiHrRange =
      sum.resting_hr_min != null && sum.resting_hr_max != null
        ? `区间 ${Math.round(sum.resting_hr_min)}–${Math.round(sum.resting_hr_max)} bpm`
        : "近 7 日静息心率";

    root.innerHTML = `
      ${alertHtml}

      <section class="grid-4">
        <article class="kpi-card">
          <div class="kpi-top">
            <span class="kpi-label">7日日均步数</span>
            <span class="kpi-icon steps"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 18h16"/><path d="M6 14v-3"/><path d="M10 14V8"/><path d="M14 14v-5"/><path d="M18 14V6"/></svg></span>
          </div>
          <div class="kpi-mid">
            <div class="kpi-value-block">
              <div class="kpi-value">${sum.steps_avg != null ? fmtNum(Math.round(sum.steps_avg), 0) : "—"}<span class="kpi-unit">步</span></div>
            </div>
            ${C.sparkline(last7(series.steps), { mode: "bars", color: "#e85420" })}
          </div>
          <div class="kpi-foot">
            <span>合计 <strong>${sum.steps_total != null ? fmtNum(sum.steps_total, 0) : "—"}</strong></span>
            <span>${esc(kpiStepsBest)}</span>
          </div>
        </article>

        <article class="kpi-card">
          <div class="kpi-top">
            <span class="kpi-label">7日日均睡眠</span>
            <span class="kpi-icon sleep"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M20 14.5A8 8 0 0 1 9.5 4 7.5 7.5 0 1 0 20 14.5z"/></svg></span>
          </div>
          <div class="kpi-mid">
            <div class="kpi-value-block">
              <div class="kpi-value">${esc(fmtMin(sum.sleep_avg_min))}</div>
            </div>
            ${C.sparkline(last7(series.sleep_total_min), { mode: "bars", color: "#3f51b5" })}
          </div>
          <div class="kpi-foot">
            <span>深睡 <strong>${esc(fmtMin(sum.sleep_deep_avg_min))}</strong></span>
            <span>REM <strong>${esc(fmtMin(sum.sleep_rem_avg_min))}</strong></span>
          </div>
        </article>

        <article class="kpi-card">
          <div class="kpi-top">
            <span class="kpi-label">静息心率</span>
            <span class="kpi-icon hr"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 12 7 12 10 5 14 19 17 12 21 12"/></svg></span>
          </div>
          <div class="kpi-mid">
            <div class="kpi-value-block">
              <div class="kpi-value">${sum.resting_hr_avg != null ? Math.round(sum.resting_hr_avg) : "—"}<span class="kpi-unit">bpm</span></div>
            </div>
            ${C.sparkline(last7(series.hr_resting), { mode: "line", color: "#e11d48" })}
          </div>
          <div class="kpi-foot">
            <span>${esc(kpiHrRange)}</span>
            <span>压力均值 <strong>${sum.stress_avg != null ? Math.round(sum.stress_avg) : "—"}</strong></span>
          </div>
        </article>

        <article class="kpi-card">
          <div class="kpi-top">
            <span class="kpi-label">血氧与体征</span>
            <span class="kpi-icon spo2"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="8"/><path d="M12 8v4l3 2"/></svg></span>
          </div>
          <div class="kpi-mid">
            <div class="kpi-value-block">
              <div class="kpi-value">${sum.spo2_avg != null ? Math.round(sum.spo2_avg) : "—"}<span class="kpi-unit">% SpO₂</span></div>
            </div>
            ${C.sparkline(last7(series.spo2_avg), { mode: "line", color: "#0284c7" })}
          </div>
          <div class="kpi-foot">
            <span>体重 <strong>${sum.weight_latest ? sum.weight_latest.weight_kg.toFixed(1) + " kg" : "—"}</strong></span>
            <span>7日运动 <strong>${sum.workout_count || 0} 次</strong></span>
          </div>
        </article>
      </section>

      <section class="grid-bento-main">
        <article class="card">
          <div class="card-head">
            <div class="card-title-wrap">
              <h2 class="card-title">健康趋势洞察</h2>
              <p class="card-desc">悬停查看逐日指标 · 底部青色圆点标记当日存在运动记录</p>
            </div>
            <div class="seg-group" id="trend-days-group">
              ${[7, 14, 30, 60, 90]
                .map((d) => `<button class="seg-btn ${state.trendDays === d ? "active" : ""}" data-trend-days="${d}">${d}天</button>`)
                .join("")}
            </div>
          </div>

          <div class="chart-controls-row">
            <div class="seg-group" id="trend-metric-group">
              ${[
                { id: "steps", label: "步数" },
                { id: "sleep", label: "睡眠" },
                { id: "hr_resting", label: "静息心率" },
                { id: "spo2_avg", label: "血氧" },
                { id: "stress_avg", label: "压力" },
                { id: "active_kcal", label: "活动消耗" },
              ]
                .map((m) => `<button class="seg-btn ${state.trendMetric === m.id ? "active" : ""}" data-trend-metric="${m.id}">${m.label}</button>`)
                .join("")}
            </div>
            ${
              state.trendMetric === "sleep"
                ? `<div class="chart-legend">
                    <span class="legend-item"><i class="legend-swatch" style="background:var(--sleep-deep)"></i>深睡</span>
                    <span class="legend-item"><i class="legend-swatch" style="background:var(--sleep-light)"></i>浅睡</span>
                    <span class="legend-item"><i class="legend-swatch" style="background:var(--sleep-rem)"></i>REM</span>
                    <span class="legend-item"><i class="legend-swatch" style="background:var(--sleep-awake)"></i>小睡/其他</span>
                  </div>`
                : state.trendMetric === "steps"
                ? `<div class="chart-legend"><span class="legend-item"><i class="legend-swatch" style="background:var(--brand)"></i>每日步数</span><span class="legend-item"><i class="legend-swatch" style="background:#15181e;opacity:.6"></i>7日均线</span></div>`
                : ""
            }
          </div>

          <div class="chart-stage" id="overview-trend-chart"></div>

          <div class="chart-summary-bar">
            <div><div class="chart-stat-label">周期均值</div><div class="chart-stat-val">${esc(fmtMetricVal(mAvg))}</div></div>
            <div><div class="chart-stat-label">周期最高</div><div class="chart-stat-val">${esc(fmtMetricVal(mMax))}</div></div>
            <div><div class="chart-stat-label">周期最低</div><div class="chart-stat-val">${esc(fmtMetricVal(mMin))}</div></div>
            <div><div class="chart-stat-label">有效记录</div><div class="chart-stat-val">${mVals.length} / ${(tl.dates || []).length} 天</div></div>
          </div>
        </article>

        <article class="card">
          <div class="card-head">
            <div class="card-title-wrap">
              <h2 class="card-title">睡眠结构与昨夜</h2>
              <p class="card-desc">近 7 日平均分期占比</p>
            </div>
          </div>
          <div class="sleep-ring-wrap">
            ${C.sleepRing(avgDeep, avgLight, avgRem, sum.sleep_avg_min)}
          </div>
          <div class="sleep-stage-list">
            <div class="sleep-stage-row">
              <span class="sleep-stage-dot" style="background:var(--sleep-deep)"></span>
              <span class="sleep-stage-name">深度睡眠</span>
              <span class="sleep-stage-val">${esc(fmtMin(avgDeep))}</span>
              <span class="sleep-stage-pct">${pct(avgDeep)}</span>
            </div>
            <div class="sleep-stage-row">
              <span class="sleep-stage-dot" style="background:var(--sleep-light)"></span>
              <span class="sleep-stage-name">浅度睡眠</span>
              <span class="sleep-stage-val">${esc(fmtMin(avgLight))}</span>
              <span class="sleep-stage-pct">${pct(avgLight)}</span>
            </div>
            <div class="sleep-stage-row">
              <span class="sleep-stage-dot" style="background:var(--sleep-rem)"></span>
              <span class="sleep-stage-name">快速眼动 REM</span>
              <span class="sleep-stage-val">${esc(fmtMin(avgRem))}</span>
              <span class="sleep-stage-pct">${pct(avgRem)}</span>
            </div>
          </div>
          ${latestSleepBlock}
        </article>
      </section>

      <section class="grid-2">
        <article class="card">
          <div class="card-head">
            <div class="card-title-wrap">
              <h2 class="card-title">最近运动记录</h2>
              <p class="card-desc">最近同步的 5 次训练与活动</p>
            </div>
            <button class="btn btn-ghost btn-sm" id="btn-all-workouts">全部运动 →</button>
          </div>
          ${workoutHtml}
        </article>

        <article class="card">
          <div class="card-head">
            <div class="card-title-wrap">
              <h2 class="card-title">Meta Muse 摘要视角</h2>
              <p class="card-desc">与 <code class="mono">get_daily_summary</code> 返回一致</p>
            </div>
            <div class="card-actions">
              <div class="seg-group">
                ${[7, 14, 30]
                  .map((d) => `<button class="seg-btn ${state.summaryDays === d ? "active" : ""}" data-sum-days="${d}">${d}天</button>`)
                  .join("")}
              </div>
              <button class="btn btn-sm" id="btn-toggle-md">${state.summaryRawMode ? "排版预览" : "原始 MD"}</button>
              <button class="btn btn-soft btn-sm" id="btn-copy-md">复制</button>
            </div>
          </div>
          <div class="md-box">${summaryContent}</div>
        </article>
      </section>
    `;

    C.trendChart(document.getElementById("overview-trend-chart"), {
      timeline: tl,
      metric: state.trendMetric,
    });

    root.querySelectorAll("[data-goto]").forEach((el) => {
      el.addEventListener("click", () => navigate(el.dataset.goto));
    });

    root.querySelectorAll("[data-trend-metric]").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.trendMetric = btn.dataset.trendMetric;
        renderOverview(root);
      });
    });

    root.querySelectorAll("[data-trend-days]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const days = Number(btn.dataset.trendDays);
        if (days === state.trendDays) return;
        state.trendDays = days;
        try {
          state.timeline = await api(`/admin/api/timeline?days=${days}`);
          renderOverview(root);
        } catch (err) {
          toast(err.message, "danger");
        }
      });
    });

    root.querySelectorAll("[data-sum-days]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const days = Number(btn.dataset.sumDays);
        if (days === state.summaryDays) return;
        state.summaryDays = days;
        try {
          state.summaryData = await api(`/admin/api/summary?days=${days}`);
          renderOverview(root);
        } catch (err) {
          toast(err.message, "danger");
        }
      });
    });

    const toggleMd = document.getElementById("btn-toggle-md");
    if (toggleMd) {
      toggleMd.addEventListener("click", () => {
        state.summaryRawMode = !state.summaryRawMode;
        renderOverview(root);
      });
    }

    const copyMd = document.getElementById("btn-copy-md");
    if (copyMd) {
      copyMd.addEventListener("click", () => copyText(summaryObj.markdown || "", "Markdown 摘要"));
    }

    const allWorkouts = document.getElementById("btn-all-workouts");
    if (allWorkouts) {
      allWorkouts.addEventListener("click", () => {
        state.explorer.domain = "workouts";
        state.explorer.data = null;
        navigate("data");
      });
    }
  }

  // =========================================================================
  // 2. Sleep Lab View
  // =========================================================================

  function renderSleepView(root) {
    const payload = state.sleepData || (state.overview && state.overview.sleep) || { dates: [], days: [] };
    const days = payload.days || [];
    const byDate = {};
    days.forEach((d) => {
      byDate[d.date] = d;
    });

    const totals = days.map((d) => d.total_min).filter((v) => v != null);
    const mains = days.filter((d) => d.main).map((d) => d.main.asleep_min);
    const deeps = days.filter((d) => d.main && d.main.deep_min != null).map((d) => d.main.deep_min);
    const napDays = days.filter((d) => d.nap_min && d.nap_min > 0);
    const avg = (arr) => (arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : null);

    const avgTotal = avg(totals);
    const avgMain = avg(mains);
    const avgDeep = avg(deeps);
    const deepShare = avgMain && avgDeep ? `${Math.round((avgDeep / avgMain) * 100)}%` : "—";
    const avgNap = avg(napDays.map((d) => d.nap_min));

    const selDate = state.sleepSelectedDate || (days.length ? days[days.length - 1].date : null);
    const sel = selDate ? byDate[selDate] : null;

    let inspectorHtml = `<div class="empty-state"><strong>点击图表或右侧列表查看单日睡眠剖面</strong><p>支持查看主睡眠各阶段占比与独立小睡记录。</p></div>`;
    if (sel) {
      const statusBadge =
        sel.detail_status === "complete"
          ? `<span class="badge badge-ok">明细完整</span>`
          : sel.detail_status === "partial"
          ? `<span class="badge badge-warn">明细部分缺失</span>`
          : `<span class="badge badge-neutral">仅总量（无分段明细）</span>`;

      const main = sel.main;
      let mainHtml = `<div class="sleep-session-card"><div class="sleep-session-top"><strong>主睡眠</strong><span class="field-hint">无分期主睡眠记录</span></div></div>`;
      if (main) {
        const dp = main.deep_min || 0;
        const lt = main.light_min || 0;
        const rm = main.rem_min || 0;
        const aw = main.awake_min || 0;
        const denom = Math.max(1, dp + lt + rm + aw);
        const eff = Math.round(((dp + lt + rm) / denom) * 100);
        mainHtml = `<div class="sleep-session-card">
          <div class="sleep-session-top">
            <strong>夜间主睡眠</strong>
            <span class="mono" style="font-size:12px;color:var(--ink-secondary)">${esc(fmtClock(main.start))} → ${esc(fmtClock(main.end))}</span>
          </div>
          <div style="display:flex;align-items:baseline;justify-content:space-between;gap:8px">
            <div style="font-size:22px;font-weight:700" class="num">${esc(fmtMin(main.asleep_min))}</div>
            <span class="badge badge-indigo num">睡眠效率 ${eff}%</span>
          </div>
          <div class="stage-ribbon">
            <div class="stage-ribbon-seg" style="width:${((dp / denom) * 100).toFixed(1)}%;background:var(--sleep-deep)" title="深睡"></div>
            <div class="stage-ribbon-seg" style="width:${((lt / denom) * 100).toFixed(1)}%;background:var(--sleep-light)" title="浅睡"></div>
            <div class="stage-ribbon-seg" style="width:${((rm / denom) * 100).toFixed(1)}%;background:var(--sleep-rem)" title="REM"></div>
            <div class="stage-ribbon-seg" style="width:${((aw / denom) * 100).toFixed(1)}%;background:var(--sleep-awake)" title="清醒"></div>
          </div>
          <div class="sleep-stage-list" style="margin-top:4px">
            <div class="sleep-stage-row"><span class="sleep-stage-dot" style="background:var(--sleep-deep)"></span><span class="sleep-stage-name">深睡</span><span class="sleep-stage-val">${esc(fmtMin(dp))}</span><span class="sleep-stage-pct">${Math.round((dp / denom) * 100)}%</span></div>
            <div class="sleep-stage-row"><span class="sleep-stage-dot" style="background:var(--sleep-light)"></span><span class="sleep-stage-name">浅睡</span><span class="sleep-stage-val">${esc(fmtMin(lt))}</span><span class="sleep-stage-pct">${Math.round((lt / denom) * 100)}%</span></div>
            <div class="sleep-stage-row"><span class="sleep-stage-dot" style="background:var(--sleep-rem)"></span><span class="sleep-stage-name">REM</span><span class="sleep-stage-val">${esc(fmtMin(rm))}</span><span class="sleep-stage-pct">${Math.round((rm / denom) * 100)}%</span></div>
            <div class="sleep-stage-row"><span class="sleep-stage-dot" style="background:var(--sleep-awake)"></span><span class="sleep-stage-name">夜间清醒</span><span class="sleep-stage-val">${esc(fmtMin(aw))}</span><span class="sleep-stage-pct">${Math.round((aw / denom) * 100)}%</span></div>
          </div>
        </div>`;
      }

      let napHtml = "";
      if (sel.naps && sel.naps.length) {
        napHtml = `<div class="sleep-session-card">
          <div class="sleep-session-top"><strong>日间小睡 (${sel.naps.length} 次)</strong><span class="badge badge-warn">合计 ${esc(fmtMin(sel.nap_min))}</span></div>
          ${sel.naps
            .map(
              (n) => `<div style="display:flex;justify-content:space-between;font-size:12.5px;color:var(--ink-secondary)">
                <span class="mono">${esc(fmtClock(n.start))} → ${esc(fmtClock(n.end))}</span>
                <strong class="num">${esc(fmtMin(n.asleep_min))}</strong>
              </div>`
            )
            .join("")}
        </div>`;
      } else if (sel.detail_status === "complete") {
        napHtml = `<div class="sleep-session-card"><div class="sleep-session-top"><strong>日间小睡</strong><span class="badge badge-ok">当日无小睡</span></div></div>`;
      } else {
        napHtml = `<div class="sleep-session-card"><div class="sleep-session-top"><strong>日间小睡</strong><span class="badge badge-neutral">明细不完整，无法确认</span></div></div>`;
      }

      inspectorHtml = `
        <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:14px">
          <div>
            <div style="font-size:18px;font-weight:700" class="num">${esc(sel.date)} <span style="font-size:13px;font-weight:500;color:var(--ink-muted)">${esc(C.weekdayLabel(sel.date))}</span></div>
            <div class="field-hint">当日总睡眠 <strong style="color:var(--ink-primary)">${esc(fmtMin(sel.total_min))}</strong></div>
          </div>
          ${statusBadge}
        </div>
        <div style="display:flex;flex-direction:column;gap:12px">
          ${mainHtml}
          ${napHtml}
        </div>
      `;
    }

    const tableRows = [...days]
      .reverse()
      .map((d) => {
        const isSel = d.date === selDate;
        const m = d.main;
        const napText = d.nap_min ? fmtMin(d.nap_min) : d.detail_status === "complete" ? "无" : "—";
        const spanText = m && m.start ? `${fmtClock(m.start)}–${fmtClock(m.end)}` : "—";
        return `<tr class="is-clickable ${isSel ? "is-selected" : ""}" data-sleep-date="${esc(d.date)}">
          <td><strong>${esc(d.date)}</strong> <span style="color:var(--ink-muted);font-size:11.5px">${esc(C.weekdayLabel(d.date))}</span></td>
          <td><strong>${esc(fmtMin(d.total_min))}</strong></td>
          <td>${m ? esc(fmtMin(m.asleep_min)) : "—"}</td>
          <td style="color:var(--sleep-deep)">${m ? esc(fmtMin(m.deep_min)) : "—"}</td>
          <td>${d.nap_min ? `<span class="badge badge-warn">${esc(napText)}</span>` : esc(napText)}</td>
          <td class="mono" style="font-size:12px;color:var(--ink-secondary)">${esc(spanText)}</td>
        </tr>`;
      })
      .join("");

    root.innerHTML = `
      <section class="grid-4">
        <article class="kpi-card">
          <div class="kpi-top"><span class="kpi-label">周期日均总睡眠</span><span class="badge badge-indigo">${state.sleepDays} 天</span></div>
          <div class="kpi-value">${esc(fmtMin(avgTotal))}</div>
          <div class="kpi-foot"><span>有效记录</span><strong>${totals.length} 天</strong></div>
        </article>
        <article class="kpi-card">
          <div class="kpi-top"><span class="kpi-label">平均夜间主睡眠</span></div>
          <div class="kpi-value">${esc(fmtMin(avgMain))}</div>
          <div class="kpi-foot"><span>含阶段明细</span><strong>${mains.length} 天</strong></div>
        </article>
        <article class="kpi-card">
          <div class="kpi-top"><span class="kpi-label">平均深睡时长</span></div>
          <div class="kpi-value">${esc(fmtMin(avgDeep))}</div>
          <div class="kpi-foot"><span>占主睡眠比例</span><strong>${esc(deepShare)}</strong></div>
        </article>
        <article class="kpi-card">
          <div class="kpi-top"><span class="kpi-label">日间小睡</span></div>
          <div class="kpi-value">${napDays.length}<span class="kpi-unit">天有记录</span></div>
          <div class="kpi-foot"><span>小睡日均时长</span><strong>${esc(fmtMin(avgNap))}</strong></div>
        </article>
      </section>

      <article class="card">
        <div class="card-head">
          <div class="card-title-wrap">
            <h2 class="card-title">睡眠分期与小睡分布</h2>
            <p class="card-desc">点击任意日期柱条切换下方单日剖面 · 斜纹柱代表仅同步到总量无分期明细</p>
          </div>
          <div class="card-actions">
            <div class="chart-legend">
              <span class="legend-item"><i class="legend-swatch" style="background:var(--sleep-deep)"></i>深睡</span>
              <span class="legend-item"><i class="legend-swatch" style="background:var(--sleep-light)"></i>浅睡</span>
              <span class="legend-item"><i class="legend-swatch" style="background:var(--sleep-rem)"></i>REM</span>
              <span class="legend-item"><i class="legend-swatch" style="background:var(--sleep-nap)"></i>小睡</span>
              <span class="legend-item"><i class="legend-swatch" style="background:var(--sleep-legacy)"></i>仅总量</span>
            </div>
            <div class="seg-group">
              ${[14, 30, 60, 90]
                .map((d) => `<button class="seg-btn ${state.sleepDays === d ? "active" : ""}" data-sleep-days="${d}">${d}天</button>`)
                .join("")}
            </div>
          </div>
        </div>
        <div class="chart-stage tall" id="sleep-lab-chart"></div>
      </article>

      <section class="grid-sleep-detail">
        <article class="card">${inspectorHtml}</article>
        <article class="card">
          <div class="card-head">
            <div class="card-title-wrap">
              <h2 class="card-title">逐日睡眠记录</h2>
              <p class="card-desc">共 ${days.length} 条记录，点击任意行展开剖面</p>
            </div>
          </div>
          ${
            days.length
              ? `<div class="table-scroll" style="max-height:430px">
                  <table class="data-table">
                    <thead><tr><th>日期</th><th>总计</th><th>主睡眠</th><th>深睡</th><th>小睡</th><th>入睡–醒来</th></tr></thead>
                    <tbody>${tableRows}</tbody>
                  </table>
                </div>`
              : `<div class="empty-state"><strong>该时间范围内无睡眠数据</strong></div>`
          }
        </article>
      </section>
    `;

    C.sleepLabChart(document.getElementById("sleep-lab-chart"), payload, selDate, (pickedDate) => {
      if (byDate[pickedDate]) {
        state.sleepSelectedDate = pickedDate;
        state.sleepUserPicked = true;
        renderSleepView(root);
      }
    });

    root.querySelectorAll("[data-sleep-days]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const d = Number(btn.dataset.sleepDays);
        if (d === state.sleepDays) return;
        state.sleepDays = d;
        try {
          state.sleepData = await api(`/admin/api/sleep?days=${d}`);
          pickDefaultSleepDate();
          renderSleepView(root);
        } catch (err) {
          toast(err.message, "danger");
        }
      });
    });

    root.querySelectorAll("[data-sleep-date]").forEach((tr) => {
      tr.addEventListener("click", () => {
        state.sleepSelectedDate = tr.dataset.sleepDate;
        state.sleepUserPicked = true;
        renderSleepView(root);
      });
    });
  }

  // =========================================================================
  // 3. Data Explorer View
  // =========================================================================

  async function loadExplorer() {
    state.explorer.loading = true;
    if (state.view === "data") renderCurrentView();
    try {
      const q = new URLSearchParams({ domain: state.explorer.domain });
      if (state.explorer.start) q.set("start", state.explorer.start);
      if (state.explorer.end) q.set("end", state.explorer.end);
      state.explorer.data = await api(`/admin/api/metrics?${q.toString()}`);
    } catch (err) {
      toast(err.message || "加载数据明细失败", "danger");
    } finally {
      state.explorer.loading = false;
      if (state.view === "data") renderCurrentView();
    }
  }

  function formatCell(col, val) {
    if (val == null || val === "") return `<span style="color:var(--ink-faint)">—</span>`;
    if (col === "steps") {
      const pct = Math.min(100, Math.round((Number(val) / 10000) * 100));
      return `<span class="cell-bar-wrap"><strong>${fmtNum(val, 0)}</strong><span class="cell-bar"><span class="cell-bar-fill" style="width:${pct}%"></span></span></span>`;
    }
    if (col.endsWith("_min") && col !== "hr_min" && col !== "spo2_min") return esc(fmtMin(val));
    if (col === "distance_m") return `${(Number(val) / 1000).toFixed(2)} km`;
    if (col === "duration_s") return `${Math.round(Number(val) / 60)} 分钟`;
    if (col === "weight_kg") return `${Number(val).toFixed(1)} kg`;
    if (col === "weight_bmi") return Number(val).toFixed(1);
    if (col.startsWith("spo2_")) return `${Number(val).toFixed(0)}%`;
    if (col === "stress_avg" || col === "stress_max") {
      const n = Math.round(Number(val));
      const c = n < 30 ? "#0d9488" : n < 55 ? "#d97706" : "#dc2626";
      return `<span class="stress-pill"><span class="stress-dot" style="background:${c}"></span>${n}</span>`;
    }
    if (col.startsWith("hr_") || col === "avg_hr" || col === "max_hr") return `${Math.round(Number(val))} bpm`;
    if (col.endsWith("_kcal") || col === "step_calories") return `${Math.round(Number(val))} kcal`;
    if (col === "sleep_start" || col === "sleep_end" || col === "start_time" || col === "end_time") {
      return `<span class="mono" style="font-size:12px">${esc(fmtClock(val))}</span>`;
    }
    if (col === "sport") return `<span class="badge badge-brand">${esc(sportLabel(val))}</span>`;
    return esc(val);
  }

  function renderExplorerView(root) {
    const ex = state.explorer;
    const payload = ex.data;
    const allRows = (payload && payload.rows) || [];
    const kw = (ex.query || "").trim().toLowerCase();
    const rows = kw
      ? allRows.filter((r) => JSON.stringify(r).toLowerCase().includes(kw))
      : allRows;

    const visibleCols = (() => {
      if (!allRows.length) return [];
      if (ex.domain === "all") {
        return ["date", "steps", "sleep_total_min", "sleep_deep_min", "hr_resting", "spo2_avg", "stress_avg", "active_kcal", "weight_kg"];
      }
      if (ex.domain === "workouts") {
        return ["date", "sport", "start_time", "duration_s", "distance_m", "active_kcal", "avg_hr", "max_hr", "steps"];
      }
      return Object.keys(allRows[0]).filter((k) => k !== "sleep_details" && k !== "raw_json" && k !== "updated_at");
    })();

    const exportParams = new URLSearchParams({ domain: ex.domain });
    if (ex.start) exportParams.set("start", ex.start);
    if (ex.end) exportParams.set("end", ex.end);
    const exportHref = `/admin/api/export.csv?${exportParams.toString()}`;

    const notesHtml =
      payload && payload.notes && payload.notes.length
        ? `<div style="margin-bottom:12px;font-size:12px;color:var(--ink-muted);background:var(--bg-well);padding:9px 12px;border-radius:9px;border:1px solid var(--border-subtle)">${payload.notes.map(esc).join(" · ")}</div>`
        : "";

    let tableBody = "";
    if (ex.loading) {
      tableBody = `<div class="empty-state"><span class="spinner spinner-lg"></span><strong>正在查询数据…</strong></div>`;
    } else if (!rows.length) {
      tableBody = `<div class="empty-state"><strong>所选条件下暂无数据</strong><p>尝试放宽日期区间或切换其他数据域。</p></div>`;
    } else {
      tableBody = `<div class="table-scroll" style="max-height:540px">
        <table class="data-table">
          <thead><tr>${visibleCols.map((c) => `<th>${esc(COLUMN_LABELS[c] || c)}</th>`).join("")}</tr></thead>
          <tbody>${[...rows]
            .reverse()
            .map((r) => `<tr>${visibleCols.map((c) => `<td>${formatCell(c, r[c])}</td>`).join("")}</tr>`)
            .join("")}</tbody>
        </table>
      </div>`;
    }

    root.innerHTML = `
      <article class="card">
        <div class="card-head">
          <div class="card-title-wrap">
            <h2 class="card-title">数据域选择</h2>
            <p class="card-desc">支持按任意单域或综合表检索（单次最多查询 92 天）并直接导出 CSV</p>
          </div>
          <a class="btn btn-primary btn-sm" href="${esc(exportHref)}" download>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 4v11"/><polyline points="7 11 12 16 17 11"/><path d="M4 19h16"/></svg>
            导出 CSV
          </a>
        </div>

        <div class="seg-group" style="margin-bottom:14px">
          ${EXPLORER_DOMAINS.map(
            (d) => `<button class="seg-btn ${ex.domain === d.id ? "active" : ""}" data-ex-domain="${d.id}">${d.label}</button>`
          ).join("")}
        </div>

        <div class="filter-bar" style="margin-bottom:14px">
          <div class="filter-controls">
            <input type="date" class="date-input" id="ex-start" value="${esc(ex.start)}" />
            <span style="color:var(--ink-muted)">至</span>
            <input type="date" class="date-input" id="ex-end" value="${esc(ex.end)}" />
            <button class="btn btn-sm" id="ex-apply">查询</button>
            <div class="seg-group">
              ${[7, 14, 30, 90].map((d) => `<button class="seg-btn" data-ex-quick="${d}">近${d}天</button>`).join("")}
            </div>
          </div>
          <div class="filter-controls">
            <input type="search" class="date-input" style="min-width:170px" id="ex-query" placeholder="筛选日期或运动…" value="${esc(ex.query)}" />
            <span class="badge badge-neutral num">${rows.length} 行</span>
          </div>
        </div>

        ${notesHtml}
        ${tableBody}
      </article>
    `;

    root.querySelectorAll("[data-ex-domain]").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.explorer.domain = btn.dataset.exDomain;
        loadExplorer();
      });
    });

    root.querySelectorAll("[data-ex-quick]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const d = Number(btn.dataset.exQuick);
        const today = (state.overview && state.overview.bridge && state.overview.bridge.today) || isoOffsetDays(null, 0);
        state.explorer.end = today;
        state.explorer.start = isoOffsetDays(today, -(d - 1));
        state.explorer.userDates = false;
        loadExplorer();
      });
    });

    document.getElementById("ex-apply").addEventListener("click", () => {
      state.explorer.start = document.getElementById("ex-start").value;
      state.explorer.end = document.getElementById("ex-end").value;
      state.explorer.userDates = true;
      loadExplorer();
    });

    document.getElementById("ex-query").addEventListener("input", (e) => {
      state.explorer.query = e.target.value;
      renderExplorerView(root);
      const inp = document.getElementById("ex-query");
      if (inp) {
        inp.focus();
        inp.setSelectionRange(inp.value.length, inp.value.length);
      }
    });
  }

  // =========================================================================
  // 4. Sync & Xiaomi Account View
  // =========================================================================

  function renderSyncView(root) {
    const ov = state.overview;
    const login = ov.login || { state: "idle" };
    const sync = ov.sync || { state: "idle" };
    const sched = (ov.config && ov.config.schedule) || { mode: "daily", hour: 4, minute: 30, interval_minutes: 0, days: 7 };
    const expired = Boolean(ov.session && ov.session.expired);
    const domains = (ov.bridge && ov.bridge.domains) || {};

    // QR stage
    let qrInner = "";
    let qrBadge = expired ? `<span class="badge badge-danger">会话已过期</span>` : `<span class="badge badge-ok">会话正常</span>`;
    if (login.state === "starting") {
      qrBadge = `<span class="badge badge-brand">正在请求二维码</span>`;
      qrInner = `<span class="spinner spinner-lg"></span><strong>正在向小米服务器请求登录二维码…</strong><p class="field-hint">通常需要 2–5 秒</p>`;
    } else if (login.state === "pending" && login.qr) {
      qrBadge = `<span class="badge badge-brand">等待手机扫码</span>`;
      qrInner = `
        <div class="qr-frame"><img src="${esc(login.qr)}" alt="小米账号登录二维码" /></div>
        <strong>请使用小米运动健康或小米账号 App 扫码确认</strong>
        <p class="field-hint">扫码并点击确认后，此页面将自动刷新登录状态</p>
        ${login.login_url ? `<a href="${esc(login.login_url)}" target="_blank" rel="noopener" style="font-size:12px">打开备用授权链接 ↗</a>` : ""}
      `;
    } else if (login.state === "needs_notification") {
      qrBadge = `<span class="badge badge-warn">需额外安全验证</span>`;
      qrInner = `
        <strong style="color:#b45309">${esc(login.error || "小米要求额外安全确认")}</strong>
        ${login.notification_url ? `<a class="btn btn-primary btn-sm" href="${esc(login.notification_url)}" target="_blank" rel="noopener">前往完成安全确认 ↗</a>` : ""}
        <p class="field-hint">完成后点击「获取二维码」重新扫码即可</p>
      `;
    } else if (login.state === "success") {
      qrBadge = `<span class="badge badge-ok">扫码登录成功</span>`;
      qrInner = `
        <span class="badge badge-ok" style="font-size:13px;padding:6px 14px">已保存小米会话${login.user_id ? " · UID " + esc(login.user_id) : ""}</span>
        <p class="field-hint">凭据已加密保存至服务器卷，可以立即触发一次同步验证。</p>
        <button class="btn btn-primary btn-sm" data-sync-days="7">立即同步近 7 天</button>
      `;
    } else if (login.state === "error") {
      qrBadge = `<span class="badge badge-danger">登录出错</span>`;
      qrInner = `
        <div class="form-error" style="max-width:100%;text-align:left">${esc(login.error || "登录失败")}</div>
        <button class="btn btn-primary btn-sm" id="btn-qr-retry">重新获取二维码</button>
      `;
    } else {
      qrInner = `
        <div style="width:48px;height:48px;border-radius:14px;background:var(--bg-surface);border:1px solid var(--border-subtle);display:grid;place-items:center;color:var(--brand)">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><path d="M14 14h3v3h-3zM19 19h2v2h-2zM19 14h2v2h-2zM14 19h2v2h-2z"/></svg>
        </div>
        <strong>${expired ? "当前会话已失效，请重新扫码授权" : "当前小米会话有效"}</strong>
        <p class="field-hint">仅用于从小米云读取你自己的健康数据；凭据保存在本地服务器卷中，不经过第三方。</p>
      `;
    }

    const syncRunning = sync.state === "running";
    let syncStatusHtml = `<div class="sync-progress-box">上次全量/增量同步：<strong>${esc(fmtDateTime(ov.session && ov.session.last_sync_at))}</strong>（${esc(fmtRelative(ov.session && ov.session.last_sync_at))}）</div>`;
    if (syncRunning) {
      syncStatusHtml = `<div class="sync-progress-box">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <strong>正在拉取近 ${sync.days || 7} 天小米云数据…</strong>
          <span class="badge badge-brand">运行中</span>
        </div>
        <div class="sync-progress-bar"></div>
        <div class="field-hint" style="margin-top:6px">为了避免触发小米云限流，请求按安全间隔顺序执行，请稍候。</div>
      </div>`;
    } else if (sync.state === "done" && sync.result) {
      const r = sync.result;
      const errCnt = (r.errors && r.errors.length) || 0;
      syncStatusHtml = `<div class="sync-progress-box">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:8px">
          <strong>最近手动同步已完成</strong>
          <span class="badge ${errCnt ? "badge-warn" : "badge-ok"}">${errCnt ? errCnt + " 项警告" : "全部成功"}</span>
        </div>
        <div class="field-hint" style="margin-top:4px">范围 ${esc(r.from)} ~ ${esc(r.to)}（${r.days} 天 · ${r.chunks} 个请求分片）· 完成于 ${esc(fmtDateTime(sync.finished_at))}</div>
        ${errCnt ? `<div class="form-error" style="margin-top:8px">${r.errors.map(esc).join("<br>")}</div>` : ""}
      </div>`;
    } else if (sync.state === "error") {
      syncStatusHtml = `<div class="sync-progress-box"><div class="form-error">${esc(sync.error || "同步失败")}</div></div>`;
    }

    const allDomainKeys = Object.keys(DOMAIN_META);
    const domainTiles = allDomainKeys
      .map((k) => {
        const d = domains[k] || {};
        const info = DOMAIN_META[k];
        const hasErr = Boolean(d.last_error);
        const synced = Boolean(d.last_synced_at);
        return `<div class="domain-tile ${hasErr ? "has-error" : ""}">
          <div class="domain-tile-head">
            <span class="domain-tile-name">${esc(info.label)}</span>
            <span class="badge ${hasErr ? "badge-danger" : synced ? "badge-ok" : "badge-neutral"}">${hasErr ? "异常" : synced ? "正常" : "未同步"}</span>
          </div>
          <div class="domain-tile-meta num">
            <span>最新日期：${esc(d.last_date || "—")}</span>
            <span>${esc(fmtRelative(d.last_synced_at))}</span>
          </div>
          ${hasErr ? `<div class="domain-tile-err">${esc(d.last_error)}</div>` : ""}
        </div>`;
      })
      .join("");

    const mode = sched.mode || "daily";

    root.innerHTML = `
      <section class="grid-2">
        <article class="card">
          <div class="card-head">
            <div class="card-title-wrap">
              <h2 class="card-title">小米账号扫码授权</h2>
              <p class="card-desc">通过官方二维码登录刷新 <code class="mono">mifit</code> 本地会话</p>
            </div>
            ${qrBadge}
          </div>
          <div class="card-actions">
            <button class="btn btn-primary" id="btn-qr-start" ${login.state === "starting" || login.state === "pending" ? "disabled" : ""}>获取登录二维码</button>
            <button class="btn" id="btn-qr-reset" ${login.state === "idle" || login.state === "starting" || login.state === "pending" ? "disabled" : ""}>重置状态</button>
          </div>
          <div class="qr-stage">${qrInner}</div>
        </article>

        <article class="card">
          <div class="card-head">
            <div class="card-title-wrap">
              <h2 class="card-title">手动数据同步</h2>
              <p class="card-desc">立即从小米云端拉取指定天数的数据并写入本地 SQLite</p>
            </div>
            <span class="badge badge-neutral num">已存 ${(ov.session && ov.session.daily_rows) || 0} 天</span>
          </div>

          <div class="sync-preset-grid">
            <button class="sync-preset" data-sync-days="7" ${syncRunning ? "disabled" : ""}>
              <div class="sync-preset-title">近 7 天增量</div>
              <div class="sync-preset-desc">日常推荐 · 约 5–15 秒</div>
            </button>
            <button class="sync-preset" data-sync-days="30" ${syncRunning ? "disabled" : ""}>
              <div class="sync-preset-title">近 30 天回溯</div>
              <div class="sync-preset-desc">补齐月度睡眠与运动明细</div>
            </button>
            <button class="sync-preset" data-sync-days="90" ${syncRunning ? "disabled" : ""}>
              <div class="sync-preset-title">近 90 天季度</div>
              <div class="sync-preset-desc">分片拉取最近一季度记录</div>
            </button>
            <button class="sync-preset" data-sync-days="365" ${syncRunning ? "disabled" : ""}>
              <div class="sync-preset-title">全量回填 365 天</div>
              <div class="sync-preset-desc">首次部署或补全年度数据</div>
            </button>
          </div>

          <div class="sync-custom-row">
            <input type="number" class="input" id="custom-sync-days" min="1" max="366" value="14" style="max-width:120px" />
            <span class="field-hint">天（1–366）</span>
            <button class="btn" id="btn-custom-sync" style="margin-left:auto" ${syncRunning ? "disabled" : ""}>自定义同步</button>
          </div>

          ${syncStatusHtml}
        </article>
      </section>

      <article class="card">
        <div class="card-head">
          <div class="card-title-wrap">
            <h2 class="card-title">自动同步计划</h2>
            <p class="card-desc">保存后由 <code class="mono">sync</code> 守护进程在 30 秒内自动生效，无需重启容器</p>
          </div>
          <div class="seg-group" id="sched-mode-group">
            <button class="seg-btn ${mode === "daily" ? "active" : ""}" data-sched-mode="daily">每日定时</button>
            <button class="seg-btn ${mode === "interval" ? "active" : ""}" data-sched-mode="interval">固定间隔</button>
          </div>
        </div>

        <form id="schedule-form">
          <div class="schedule-grid">
            <div class="field" id="sched-daily-box" style="${mode === "daily" ? "" : "display:none"}">
              <label class="field-label">每日执行时刻（${esc(ov.timezone || "Asia/Shanghai")}）</label>
              <div style="display:flex;gap:8px;align-items:center">
                <input type="number" class="input num" id="sched-hour" min="0" max="23" value="${sched.hour}" />
                <span>:</span>
                <input type="number" class="input num" id="sched-minute" min="0" max="59" value="${sched.minute}" />
              </div>
            </div>

            <div class="field" id="sched-interval-box" style="${mode === "interval" ? "" : "display:none"}">
              <label class="field-label">轮询间隔（5–1440 分钟）</label>
              <input type="number" class="input num" id="sched-interval" min="5" max="1440" value="${sched.interval_minutes || 60}" />
            </div>

            <div class="field">
              <label class="field-label">每次回看天数（1–31 天）</label>
              <input type="number" class="input num" id="sched-days" min="1" max="31" value="${sched.days || 7}" />
            </div>

            <div class="field">
              <button type="submit" class="btn btn-primary" style="height:38px">保存同步计划</button>
            </div>
          </div>
        </form>

        <div class="schedule-status-strip">
          <span>上次自动执行：<strong class="num">${esc(fmtDateTime(sched.last_run_at))}</strong></span>
          <span>下次预计执行：<strong class="num">${esc(fmtDateTime(sched.next_run_at))}</strong>（${esc(fmtRelative(sched.next_run_at))}）</span>
          <span class="field-hint">提示：小米云本身有同步延迟，不建议设置过短间隔以免触发风控</span>
        </div>
      </article>

      <article class="card">
        <div class="card-head">
          <div class="card-title-wrap">
            <h2 class="card-title">各数据域同步状态</h2>
            <p class="card-desc">逐项检查 9 类小米运动健康指标的最近抓取结果</p>
          </div>
        </div>
        <div class="domain-matrix">${domainTiles}</div>
      </article>
    `;

    let activeSchedMode = mode;

    const startQr = async () => {
      try {
        const res = await api("/admin/api/xiaomi/login", { method: "POST" });
        state.overview.login = res;
        renderSyncView(root);
        startQrPoll();
      } catch (err) {
        toast(err.message || "获取二维码失败", "danger");
      }
    };

    const btnQrStart = document.getElementById("btn-qr-start");
    if (btnQrStart) btnQrStart.addEventListener("click", startQr);
    const btnQrRetry = document.getElementById("btn-qr-retry");
    if (btnQrRetry) btnQrRetry.addEventListener("click", startQr);

    const btnQrReset = document.getElementById("btn-qr-reset");
    if (btnQrReset) {
      btnQrReset.addEventListener("click", async () => {
        try {
          state.overview.login = await api("/admin/api/xiaomi/login", { method: "DELETE" });
          renderSyncView(root);
          toast("已重置扫码状态", "ok");
        } catch (err) {
          toast(err.message, "danger");
        }
      });
    }

    root.querySelectorAll("[data-sync-days]").forEach((btn) => {
      btn.addEventListener("click", () => triggerSync(Number(btn.dataset.syncDays)));
    });

    const customBtn = document.getElementById("btn-custom-sync");
    if (customBtn) {
      customBtn.addEventListener("click", () => {
        const v = Number(document.getElementById("custom-sync-days").value);
        if (!v || v < 1 || v > 366) {
          toast("请输入 1 到 366 之间的天数", "danger");
          return;
        }
        triggerSync(v);
      });
    }

    root.querySelectorAll("[data-sched-mode]").forEach((btn) => {
      btn.addEventListener("click", () => {
        activeSchedMode = btn.dataset.schedMode;
        root.querySelectorAll("[data-sched-mode]").forEach((b) => b.classList.toggle("active", b === btn));
        document.getElementById("sched-daily-box").style.display = activeSchedMode === "daily" ? "" : "none";
        document.getElementById("sched-interval-box").style.display = activeSchedMode === "interval" ? "" : "none";
      });
    });

    document.getElementById("schedule-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      try {
        const payload = {
          mode: activeSchedMode,
          hour: Number(document.getElementById("sched-hour").value),
          minute: Number(document.getElementById("sched-minute").value),
          interval_minutes: activeSchedMode === "interval" ? Number(document.getElementById("sched-interval").value) : 0,
          days: Number(document.getElementById("sched-days").value),
        };
        const updated = await api("/admin/api/schedule", { method: "POST", body: payload });
        state.overview.config.schedule = updated;
        renderSyncView(root);
        toast("自动同步计划已保存", "ok");
      } catch (err) {
        toast(err.message || "保存失败", "danger");
      }
    });
  }

  // =========================================================================
  // 5. Muse Connect View
  // =========================================================================

  function renderConnectView(root) {
    const origin = window.location.origin;
    const mcpUrl = `${origin}/mcp`;
    const openApiUrl = `${origin}/openapi.json`;
    const docsUrl = `${origin}/docs`;
    const healthUrl = `${origin}/healthz`;

    const rawToken = (state.tokenData && state.tokenData.token) || "";
    const masked = rawToken
      ? `${rawToken.slice(0, 4)}${"•".repeat(Math.max(12, rawToken.length - 8))}${rawToken.slice(-4)}`
      : "正在加载…";

    const musePrompt = [
      "Build a custom integration to my self-hosted health-data service.",
      `Remote MCP server over streamable HTTP: ${mcpUrl}`,
      "Auth: Authorization: Bearer <token> (I will enter it through the secure credential flow).",
      "Tools: health_status, get_daily_summary, get_daily_metrics, get_sleep, get_steps,",
      "get_heart_rate_daily, get_spo2_daily, get_stress_daily, get_weight, get_calories,",
      "get_workouts, sync_now.",
      "Connect with the official MCP SDK, call get_daily_summary for the last 7 days end to end,",
      "show me the results, set the connector to read-only, and save the integration as a reusable skill.",
    ].join("\n");

    const curlSnippet = [
      "# 验证健康摘要接口（建议在本地终端使用环境变量传入 Token）",
      `curl -s -H "Authorization: Bearer $BRIDGE_TOKEN" "${origin}/v1/summary?days=7&format=md"`,
      "",
      "# 检查同步状态与数据行数",
      `curl -s -H "Authorization: Bearer $BRIDGE_TOKEN" "${origin}/v1/status"`,
    ].join("\n");

    const activeSnippet = state.connectSnippetTab === "muse" ? musePrompt : curlSnippet;

    root.innerHTML = `
      <section class="grid-2">
        <article class="card">
          <div class="card-head">
            <div class="card-title-wrap">
              <h2 class="card-title">服务端点</h2>
              <p class="card-desc">基于当前访问地址自动拼接，可直接填入 Meta Muse 或 HTTP 客户端</p>
            </div>
          </div>
          <div class="endpoint-list">
            ${[
              { label: "远程 MCP（Streamable HTTP）", url: mcpUrl, open: false },
              { label: "OpenAPI 3 规范（自动生成连接器）", url: openApiUrl, open: true },
              { label: "Swagger 交互式接口文档", url: docsUrl, open: true },
              { label: "公开健康检查探针", url: healthUrl, open: true },
            ]
              .map(
                (ep) => `<div class="endpoint-row">
                  <div class="endpoint-info">
                    <div class="endpoint-label">${esc(ep.label)}</div>
                    <div class="endpoint-url">${esc(ep.url)}</div>
                  </div>
                  <div class="card-actions" style="flex-shrink:0">
                    ${ep.open ? `<a class="btn btn-sm" href="${esc(ep.url)}" target="_blank" rel="noopener">打开</a>` : ""}
                    <button class="btn btn-sm" data-copy-val="${esc(ep.url)}" data-copy-lbl="${esc(ep.label)}">复制</button>
                  </div>
                </div>`
              )
              .join("")}
          </div>
        </article>

        <article class="card">
          <div class="card-head">
            <div class="card-title-wrap">
              <h2 class="card-title">Bridge Token 凭据</h2>
              <p class="card-desc">用于 <code class="mono">Authorization: Bearer &lt;token&gt;</code> 或 <code class="mono">X-API-Key</code></p>
            </div>
            <span class="badge badge-ok">Bearer 鉴权</span>
          </div>
          <div class="token-vault">
            <div style="display:flex;align-items:center;justify-content:space-between;font-size:12px;color:#94a3b8">
              <span>BRIDGE_TOKEN</span>
              <span>请勿直接粘贴在 AI 聊天正文里</span>
            </div>
            <div class="token-display">${esc(state.tokenVisible ? rawToken || "未配置 BRIDGE_TOKEN" : masked)}</div>
            <div style="display:flex;gap:8px;flex-wrap:wrap">
              <button class="btn btn-vault btn-sm" id="btn-toggle-token">${state.tokenVisible ? "隐藏 Token" : "显示完整 Token"}</button>
              <button class="btn btn-primary btn-sm" id="btn-copy-token" ${rawToken ? "" : "disabled"}>复制 Token</button>
            </div>
          </div>
          <p class="field-hint" style="margin:12px 0 0;line-height:1.65">
            安全建议：在 Meta Muse 接入时请通过其<strong>安全凭据弹窗</strong>填写 Token；如需轮换，请修改服务器 <code class="mono">.env</code> 中的 <code class="mono">BRIDGE_TOKEN</code> 并重启服务。
          </p>
        </article>
      </section>

      <article class="card">
        <div class="card-head">
          <div class="card-title-wrap">
            <h2 class="card-title">快速接入与验证脚本</h2>
            <p class="card-desc">已自动填入当前服务域名，一键复制即可使用</p>
          </div>
          <div class="card-actions">
            <div class="seg-group">
              <button class="seg-btn ${state.connectSnippetTab === "muse" ? "active" : ""}" data-snip="muse">Meta Muse 提示词</button>
              <button class="seg-btn ${state.connectSnippetTab === "curl" ? "active" : ""}" data-snip="curl">curl 验证命令</button>
            </div>
            <button class="btn btn-soft btn-sm" id="btn-copy-snippet">复制代码</button>
          </div>
        </div>
        <pre class="code-block">${esc(activeSnippet)}</pre>
      </article>

      <article class="card">
        <div class="card-head">
          <div class="card-title-wrap">
            <h2 class="card-title">暴露的 MCP 工具目录</h2>
            <p class="card-desc">共 ${MCP_TOOLS.length} 个工具：11 个严格只读查询 + 1 个可控云端刷新</p>
          </div>
        </div>
        <div class="tool-grid">
          ${MCP_TOOLS.map(
            (t) => `<div class="tool-card">
              <div class="tool-card-head">
                <span class="tool-name">${esc(t.name)}</span>
                <span class="badge ${t.mode === "sync" ? "badge-brand" : "badge-ok"}">${t.mode === "sync" ? "触发同步" : "只读"}</span>
              </div>
              <div class="tool-desc">${esc(t.desc)}</div>
            </div>`
          ).join("")}
        </div>
      </article>
    `;

    root.querySelectorAll("[data-copy-val]").forEach((btn) => {
      btn.addEventListener("click", () => copyText(btn.dataset.copyVal, btn.dataset.copyLbl));
    });

    const toggleTok = document.getElementById("btn-toggle-token");
    if (toggleTok) {
      toggleTok.addEventListener("click", () => {
        state.tokenVisible = !state.tokenVisible;
        renderConnectView(root);
      });
    }

    const copyTok = document.getElementById("btn-copy-token");
    if (copyTok) {
      copyTok.addEventListener("click", () => copyText(rawToken, "Bridge Token"));
    }

    root.querySelectorAll("[data-snip]").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.connectSnippetTab = btn.dataset.snip;
        renderConnectView(root);
      });
    });

    document.getElementById("btn-copy-snippet").addEventListener("click", () => {
      copyText(activeSnippet, state.connectSnippetTab === "muse" ? "Meta Muse 接入提示词" : "curl 命令");
    });
  }

  // =========================================================================
  // 6. Backups & System View
  // =========================================================================

  function auditChipClass(action) {
    if (action.includes("fail")) return "badge-danger";
    if (action.startsWith("login") || action.startsWith("password")) return "badge-indigo";
    if (action.startsWith("sync") || action.startsWith("schedule")) return "badge-brand";
    if (action.startsWith("backup")) return "badge-ok";
    return "badge-neutral";
  }

  function renderSystemView(root) {
    const backups = (state.backupsData && state.backupsData.backups) || [];
    const totalSize = (state.backupsData && state.backupsData.total_size) || 0;
    const cfg = state.settingsData || {};
    const auditEntries = (state.auditData && state.auditData.entries) || [];
    const filteredAudit =
      state.auditFilter === "all"
        ? auditEntries
        : auditEntries.filter((e) => String(e.action || "").startsWith(state.auditFilter));

    const backupTable = backups.length
      ? `<div class="table-scroll">
          <table class="data-table">
            <thead><tr><th>备份文件名</th><th>创建时间</th><th>文件大小</th><th style="text-align:right">操作</th></tr></thead>
            <tbody>${backups
              .map(
                (b) => `<tr>
                  <td class="mono" style="font-size:12.5px"><strong>${esc(b.name)}</strong></td>
                  <td>${esc(fmtDateTime(b.created_at))}</td>
                  <td>${esc(fmtBytes(b.size))}</td>
                  <td style="text-align:right">
                    <a class="btn btn-sm" href="/admin/api/backups/${encodeURIComponent(b.name)}" download>下载</a>
                    <button class="btn btn-danger btn-sm" data-del-backup="${esc(b.name)}" style="margin-left:6px">删除</button>
                  </td>
                </tr>`
              )
              .join("")}</tbody>
          </table>
        </div>`
      : `<div class="empty-state"><strong>暂无备份文件</strong><p>点击右上角「创建快照备份」打包 SQLite 数据库与小米会话。</p></div>`;

    const auditRows = filteredAudit.length
      ? `<div class="table-scroll" style="max-height:360px">
          <table class="data-table">
            <thead><tr><th>时间</th><th>事件</th><th>详情</th><th>来源 IP</th></tr></thead>
            <tbody>${filteredAudit
              .map(
                (a) => `<tr>
                  <td class="mono" style="font-size:12px">${esc(fmtDateTime(a.at))}</td>
                  <td><span class="badge ${auditChipClass(a.action || "")}">${esc(a.action)}</span></td>
                  <td style="white-space:normal;max-width:420px;color:var(--ink-secondary)">${esc(a.detail || "—")}</td>
                  <td class="mono" style="font-size:12px;color:var(--ink-muted)">${esc(a.ip || "—")}</td>
                </tr>`
              )
              .join("")}</tbody>
          </table>
        </div>`
      : `<div class="empty-state"><strong>暂无匹配的审计记录</strong></div>`;

    root.innerHTML = `
      <article class="card">
        <div class="card-head">
          <div class="card-title-wrap">
            <h2 class="card-title">数据与会话备份</h2>
            <p class="card-desc">共 ${backups.length} 份快照 · 合计 ${esc(fmtBytes(totalSize))} · 备份包内含小米登录态，请妥善保管</p>
          </div>
          <button class="btn btn-primary btn-sm" id="btn-create-backup">创建快照备份</button>
        </div>
        ${backupTable}
      </article>

      <section class="grid-2">
        <article class="card">
          <div class="card-head">
            <div class="card-title-wrap">
              <h2 class="card-title">运行参数与诊断</h2>
              <p class="card-desc">只读配置快照（不含敏感凭据）</p>
            </div>
            <span class="badge ${cfg.session_present ? "badge-ok" : "badge-warn"}">${cfg.session_present ? "检测到 session.json" : "未检测到 session.json"}</span>
          </div>
          <div class="spec-list">
            <div class="spec-row"><span class="spec-key">服务版本</span><span class="spec-val mono">v${esc(cfg.version || "—")}</span></div>
            <div class="spec-row"><span class="spec-key">时区设置</span><span class="spec-val mono">${esc(cfg.timezone || "—")}</span></div>
            <div class="spec-row"><span class="spec-key">数据库路径</span><span class="spec-val mono">${esc(cfg.db_path || "—")}</span></div>
            <div class="spec-row"><span class="spec-key">数据库体积</span><span class="spec-val num">${esc(fmtBytes(cfg.db_size))}</span></div>
            <div class="spec-row"><span class="spec-key">首次回填天数</span><span class="spec-val num">${esc(cfg.backfill_days || "—")} 天</span></div>
            <div class="spec-row"><span class="spec-key">API 限流 / 同步限流</span><span class="spec-val num">${esc(cfg.rate_limit_per_min || "—")} / ${esc(cfg.sync_rate_limit_per_min || "—")} 次/分</span></div>
            <div class="spec-row"><span class="spec-key">MCP Allowed Hosts</span><span class="spec-val mono">${esc((cfg.allowed_hosts || []).join(", ") || "—")}</span></div>
            <div class="spec-row"><span class="spec-key">管理密码来源</span><span class="spec-val"><span class="badge badge-neutral">${cfg.password_source === "database" ? "数据库自定义哈希" : ".env 环境变量"}</span></span></div>
          </div>
        </article>

        <article class="card">
          <div class="card-head">
            <div class="card-title-wrap">
              <h2 class="card-title">修改管理密码</h2>
              <p class="card-desc">使用 PBKDF2-SHA256 哈希存入本地数据库，修改后其他浏览器会话将立即失效</p>
            </div>
          </div>
          <form id="password-form" style="display:flex;flex-direction:column;gap:12px">
            <div class="field">
              <label class="field-label" for="pwd-current">当前密码</label>
              <input type="password" id="pwd-current" class="input" autocomplete="current-password" required />
            </div>
            <div class="field">
              <label class="field-label" for="pwd-new">新密码（至少 8 位）</label>
              <input type="password" id="pwd-new" class="input" autocomplete="new-password" minlength="8" required />
            </div>
            <div class="field">
              <label class="field-label" for="pwd-confirm">确认新密码</label>
              <input type="password" id="pwd-confirm" class="input" autocomplete="new-password" minlength="8" required />
            </div>
            <div id="pwd-feedback" class="hidden"></div>
            <button type="submit" class="btn btn-primary" style="align-self:flex-start">保存新密码</button>
          </form>
          <p class="field-hint" style="margin:14px 0 0;line-height:1.6">
            若忘记密码，可在服务器运行：<br>
            <code class="mono">docker compose run --rm bridge python -m health_bridge.admin --reset-password</code>
          </p>
        </article>
      </section>

      <article class="card">
        <div class="card-head">
          <div class="card-title-wrap">
            <h2 class="card-title">管理审计日志</h2>
            <p class="card-desc">记录最近的管理登录、同步触发、计划变更、备份与导出操作</p>
          </div>
          <div class="card-actions">
            <div class="seg-group">
              ${[
                { id: "all", label: "全部" },
                { id: "login", label: "登录" },
                { id: "sync", label: "同步" },
                { id: "backup", label: "备份" },
                { id: "export", label: "导出" },
                { id: "schedule", label: "计划" },
              ]
                .map((f) => `<button class="seg-btn ${state.auditFilter === f.id ? "active" : ""}" data-audit-filter="${f.id}">${f.label}</button>`)
                .join("")}
            </div>
            <button class="btn btn-sm" id="btn-refresh-audit">刷新</button>
          </div>
        </div>
        ${auditRows}
      </article>
    `;

    document.getElementById("btn-create-backup").addEventListener("click", async (e) => {
      const btn = e.currentTarget;
      btn.disabled = true;
      btn.innerHTML = `<span class="spinner"></span>打包中…`;
      try {
        const entry = await api("/admin/api/backups", { method: "POST" });
        toast(`备份已创建：${entry.name}`, "ok");
        state.backupsData = await api("/admin/api/backups");
        state.auditData = await api("/admin/api/audit?limit=80");
        renderSystemView(root);
      } catch (err) {
        toast(err.message || "创建备份失败", "danger");
        btn.disabled = false;
        btn.textContent = "创建快照备份";
      }
    });

    root.querySelectorAll("[data-del-backup]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const name = btn.dataset.delBackup;
        const ok = await confirmAction("删除备份快照", `确定要永久删除备份文件 ${name} 吗？此操作无法撤销。`, "确认删除", true);
        if (!ok) return;
        try {
          await api(`/admin/api/backups/${encodeURIComponent(name)}`, { method: "DELETE" });
          toast(`已删除 ${name}`, "ok");
          state.backupsData = await api("/admin/api/backups");
          state.auditData = await api("/admin/api/audit?limit=80");
          renderSystemView(root);
        } catch (err) {
          toast(err.message || "删除失败", "danger");
        }
      });
    });

    document.getElementById("password-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const cur = document.getElementById("pwd-current").value;
      const next = document.getElementById("pwd-new").value;
      const conf = document.getElementById("pwd-confirm").value;
      const fb = document.getElementById("pwd-feedback");
      if (next.length < 8) {
        fb.className = "form-error";
        fb.textContent = "新密码至少需要 8 个字符";
        return;
      }
      if (next !== conf) {
        fb.className = "form-error";
        fb.textContent = "两次输入的新密码不一致";
        return;
      }
      try {
        await api("/admin/api/password", { method: "POST", body: { current: cur, new: next } });
        fb.className = "form-ok";
        fb.textContent = "密码已更新，其他设备会话已自动注销。";
        e.target.reset();
        state.settingsData = await api("/admin/api/settings");
        toast("管理密码已更新", "ok");
      } catch (err) {
        fb.className = "form-error";
        fb.textContent = err.message || "修改失败";
      }
    });

    root.querySelectorAll("[data-audit-filter]").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.auditFilter = btn.dataset.auditFilter;
        renderSystemView(root);
      });
    });

    document.getElementById("btn-refresh-audit").addEventListener("click", async () => {
      try {
        state.auditData = await api("/admin/api/audit?limit=80");
        renderSystemView(root);
        toast("审计日志已刷新", "ok");
      } catch (err) {
        toast(err.message, "danger");
      }
    });
  }

  // =========================================================================
  // Bootstrap & Global Listeners
  // =========================================================================

  function bindGlobalEvents() {
    // Login form
    const loginForm = document.getElementById("login-form");
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const pwdEl = document.getElementById("login-password");
      const errEl = document.getElementById("login-error");
      const btn = document.getElementById("login-submit");
      errEl.classList.add("hidden");
      btn.disabled = true;
      btn.innerHTML = `<span class="spinner"></span>验证中…`;
      try {
        await api("/admin/api/session", {
          method: "POST",
          body: { password: pwdEl.value },
          allowUnauth: true,
        });
        pwdEl.value = "";
        showApp();
        await loadOverview(true);
        navigate(currentRouteFromHash());
      } catch (err) {
        errEl.textContent =
          err.status === 401
            ? "管理密码不正确，请检查后重试。"
            : err.status === 429
            ? "尝试次数过多，请一分钟后再试。"
            : err.status === 503
            ? "服务端尚未配置 ADMIN_PASSWORD 环境变量。"
            : err.message || "登录失败";
        errEl.classList.remove("hidden");
      } finally {
        btn.disabled = false;
        btn.textContent = "进入管理控制台";
      }
    });

    // Eye toggle on login password
    document.getElementById("login-eye").addEventListener("click", () => {
      const inp = document.getElementById("login-password");
      inp.type = inp.type === "password" ? "text" : "password";
    });

    // Navigation
    document.querySelectorAll(".nav-item[data-view]").forEach((btn) => {
      btn.addEventListener("click", () => navigate(btn.dataset.view));
    });

    document.getElementById("sidebar-status").addEventListener("click", () => navigate("sync"));
    document.getElementById("topbar-sync-pill").addEventListener("click", () => navigate("sync"));

    // Mobile sidebar
    document.getElementById("mobile-menu-btn").addEventListener("click", () => {
      document.getElementById("sidebar").classList.add("open");
      document.getElementById("sidebar-backdrop").classList.add("open");
    });
    document.getElementById("sidebar-backdrop").addEventListener("click", closeMobileSidebar);

    // Quick topbar actions
    document.getElementById("btn-quick-sync").addEventListener("click", () => triggerSync(7));
    document.getElementById("btn-refresh-all").addEventListener("click", async () => {
      state.sleepUserPicked = false;
      state.explorer.data = null;
      await loadOverview(false);
      await ensureViewData(state.view);
    });

    // Logout
    document.getElementById("btn-logout").addEventListener("click", async () => {
      try {
        await api("/admin/api/session", { method: "DELETE", allowUnauth: true });
      } catch (_) {}
      state.overview = null;
      state.tokenData = null;
      toast("已安全退出登录", "ok");
      showLogin();
    });

    // Modal controls
    document.getElementById("modal-cancel").addEventListener("click", () => closeModal(false));
    document.getElementById("modal-ok").addEventListener("click", () => closeModal(true));
    document.getElementById("confirm-modal").addEventListener("click", (e) => {
      if (e.target.id === "confirm-modal") closeModal(false);
    });

    window.addEventListener("hashchange", () => {
      if (state.authed) navigate(currentRouteFromHash());
    });
  }

  async function init() {
    bindGlobalEvents();
    try {
      const sess = await api("/admin/api/session", { allowUnauth: true });
      if (sess && sess.authenticated) {
        showApp();
        await loadOverview(true);
        navigate(currentRouteFromHash());
      } else {
        showLogin();
      }
    } catch (_) {
      showLogin();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
