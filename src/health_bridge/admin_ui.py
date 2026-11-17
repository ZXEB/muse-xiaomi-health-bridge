ADMIN_HTML = r'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<title>小米健康桥 · 管理后台</title>
<style>
  :root{
    --bg:#0a0d13; --panel:#111621; --panel-2:#161c29; --line:#1f2735; --line-2:#283243;
    --text:#e8edf7; --muted:#8a95a8; --muted-2:#5f6b7f;
    --accent:#4f8cff; --accent-2:#7c5cff; --green:#34d399; --red:#f87171; --amber:#fbbf24;
    --radius:14px; --shadow:0 8px 30px rgba(0,0,0,.35);
  }
  *{box-sizing:border-box}
  html,body{height:100%}
  body{margin:0;background:radial-gradient(1200px 600px at 20% -10%,#15203a 0%,transparent 60%),var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;font-size:14px;line-height:1.5}
  a{color:var(--accent);text-decoration:none}
  button{font-family:inherit}
  .hidden{display:none!important}
  .muted{color:var(--muted)}
  .mono{font-family:"SFMono-Regular",Consolas,"Liberation Mono",monospace}

  /* ---------- login ---------- */
  .login-view{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px}
  .login-card{width:100%;max-width:420px;background:linear-gradient(180deg,rgba(255,255,255,.04),transparent),var(--panel);border:1px solid var(--line);border-radius:20px;padding:34px 30px;box-shadow:var(--shadow)}
  .login-brand{display:flex;align-items:center;gap:12px;margin-bottom:22px}
  .login-brand .logo{width:44px;height:44px}
  .login-brand h1{font-size:18px;margin:0;font-weight:650}
  .login-brand p{margin:2px 0 0;color:var(--muted);font-size:12px}
  .login-card h2{font-size:22px;margin:0 0 6px}
  .login-card .hint{color:var(--muted);font-size:13px;margin-bottom:22px}
  .field{display:flex;gap:10px}
  .input,select,input[type=date]{width:100%;background:var(--panel-2);border:1px solid var(--line-2);color:var(--text);border-radius:10px;padding:11px 13px;font-size:14px;outline:none;transition:border-color .15s,box-shadow .15s}
  .input:focus,select:focus,input[type=date]:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(79,140,255,.18)}
  .btn{display:inline-flex;align-items:center;justify-content:center;gap:7px;border:1px solid transparent;background:linear-gradient(180deg,#5b95ff,#3f7bf0);color:#fff;border-radius:10px;padding:10px 16px;font-size:13.5px;font-weight:600;cursor:pointer;transition:transform .05s,filter .15s;white-space:nowrap}
  .btn:hover{filter:brightness(1.08)}
  .btn:active{transform:translateY(1px)}
  .btn[disabled]{opacity:.55;cursor:not-allowed}
  .btn.ghost{background:var(--panel-2);border-color:var(--line-2);color:var(--text);font-weight:500}
  .btn.ghost:hover{border-color:#39465c;filter:none}
  .btn.danger{background:linear-gradient(180deg,#f87171,#dc4c4c)}
  .btn.sm{padding:7px 11px;font-size:12.5px;border-radius:8px}
  .error{color:var(--red);font-size:13px;min-height:20px;margin-top:10px}
  .login-foot{margin-top:26px;padding-top:16px;border-top:1px solid var(--line);color:var(--muted-2);font-size:12px}

  /* ---------- app shell ---------- */
  .app{display:flex;min-height:100vh}
  .sidebar{width:228px;flex:0 0 228px;background:rgba(12,16,24,.72);border-right:1px solid var(--line);padding:18px 14px;display:flex;flex-direction:column;position:sticky;top:0;height:100vh}
  .brand-row{display:flex;align-items:center;gap:11px;padding:6px 8px 18px}
  .brand-row .logo{width:34px;height:34px}
  .brand-row .name{font-weight:650;font-size:14.5px}
  .brand-row .sub{color:var(--muted-2);font-size:11px}
  nav{display:flex;flex-direction:column;gap:3px;margin-top:8px}
  nav a{display:flex;align-items:center;gap:10px;padding:10px 11px;border-radius:9px;color:var(--muted);font-size:13.5px;font-weight:500;border:1px solid transparent}
  nav a svg{width:17px;height:17px;opacity:.85}
  nav a:hover{background:var(--panel);color:var(--text)}
  nav a.active{background:linear-gradient(90deg,rgba(79,140,255,.18),rgba(79,140,255,.06));color:#cfe0ff;border-color:rgba(79,140,255,.28)}
  .sidebar-foot{margin-top:auto;padding:12px 8px 4px;border-top:1px solid var(--line);display:flex;align-items:center;gap:8px;color:var(--muted);font-size:12px}
  .dot{width:8px;height:8px;border-radius:99px;background:var(--green);box-shadow:0 0 0 4px rgba(52,211,153,.12)}
  .dot.bad{background:var(--red);box-shadow:0 0 0 4px rgba(248,113,113,.12)}
  .dot.warn{background:var(--amber);box-shadow:0 0 0 4px rgba(251,191,36,.12)}
  .sidebar-foot .ver{margin-left:auto;color:var(--muted-2);font-size:11px}

  .main{flex:1;min-width:0;padding:22px 28px 60px}
  .topbar{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:22px}
  .topbar h2{font-size:20px;margin:0;font-weight:650}
  .crumb{color:var(--muted-2);font-size:12px;margin-top:3px}
  .top-actions{display:flex;align-items:center;gap:10px}
  .pill{display:inline-flex;align-items:center;gap:7px;background:var(--panel);border:1px solid var(--line);border-radius:99px;padding:6px 12px;font-size:12px;color:var(--muted)}
  .icon-btn{width:36px;height:36px;display:inline-flex;align-items:center;justify-content:center;background:var(--panel);border:1px solid var(--line);border-radius:10px;color:var(--muted);cursor:pointer}
  .icon-btn:hover{color:var(--text);border-color:#39465c}
  .icon-btn svg{width:17px;height:17px}

  /* ---------- cards ---------- */
  .grid{display:grid;gap:14px}
  .cols-4{grid-template-columns:repeat(4,minmax(0,1fr))}
  .cols-2{grid-template-columns:repeat(2,minmax(0,1fr))}
  .cols-3{grid-template-columns:repeat(3,minmax(0,1fr))}
  .card{background:linear-gradient(180deg,rgba(255,255,255,.025),transparent),var(--panel);border:1px solid var(--line);border-radius:var(--radius);padding:18px}
  .card h3{font-size:13px;font-weight:600;color:var(--muted);margin:0 0 12px;letter-spacing:.2px}
  .stat{font-size:26px;font-weight:700;letter-spacing:-.3px}
  .stat small{font-size:12px;color:var(--muted);font-weight:500;margin-left:4px}
  .stat-sub{color:var(--muted);font-size:12px;margin-top:6px}
  .card-head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:10px}
  .card-head h3{margin:0}

  .banner{display:flex;align-items:center;gap:12px;background:linear-gradient(90deg,rgba(248,113,113,.12),rgba(248,113,113,.03));border:1px solid rgba(248,113,113,.35);border-radius:12px;padding:13px 16px;margin-bottom:16px;font-size:13px}
  .banner .btn{margin-left:auto}

  .chart{width:100%;height:150px;display:block}
  .chart-tall{height:170px}
  .axis{display:flex;justify-content:space-between;color:var(--muted-2);font-size:11px;margin-top:6px}
  .legend{display:flex;gap:14px;flex-wrap:wrap;margin-top:9px;font-size:11px;color:var(--muted-2)}
  .legend i{display:inline-block;width:8px;height:8px;border-radius:2px;margin-right:5px;vertical-align:middle}
  .spin{animation:spin 1s linear infinite}
  @keyframes spin{to{transform:rotate(360deg)}}

  /* ---------- tables ---------- */
  .table-wrap{overflow:auto;border:1px solid var(--line);border-radius:12px;max-height:520px}
  table{width:100%;border-collapse:collapse;font-size:12.8px;white-space:nowrap}
  th{position:sticky;top:0;background:#131926;color:var(--muted);font-weight:600;text-align:left;padding:10px 12px;border-bottom:1px solid var(--line);z-index:1}
  td{padding:9px 12px;border-bottom:1px solid rgba(31,39,53,.7);color:#cfd7e6}
  tr:hover td{background:rgba(79,140,255,.05)}
  td.err{color:var(--red);max-width:340px;overflow:hidden;text-overflow:ellipsis}
  td.ok{color:var(--green)}
  .empty{padding:34px;text-align:center;color:var(--muted-2)}

  /* ---------- forms / toolbars ---------- */
  .toolbar{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-bottom:14px}
  .toolbar .input,.toolbar select{width:auto}
  .grow{flex:1}
  .seg{display:inline-flex;background:var(--panel-2);border:1px solid var(--line-2);border-radius:10px;padding:3px;gap:2px}
  .seg button{background:transparent;border:0;color:var(--muted);padding:7px 13px;border-radius:8px;font-size:12.5px;cursor:pointer}
  .seg button:hover{color:var(--text)}
  .seg button.active{background:#26314a;color:#cfe0ff}

  /* ---------- qr ---------- */
  .qr-panel{display:flex;gap:22px;align-items:flex-start;flex-wrap:wrap;margin-top:16px}
  .qr-img{width:200px;height:200px;background:#fff;border-radius:12px;padding:10px}
  .qr-side{min-width:240px;flex:1}
  .qr-link{word-break:break-all;font-size:12px;color:var(--muted)}
  .steps{counter-reset:s;margin:10px 0 0;padding:0;list-style:none}
  .steps li{position:relative;padding-left:28px;margin-bottom:9px;color:var(--muted);font-size:13px}
  .steps li:before{counter-increment:s;content:counter(s);position:absolute;left:0;top:0;width:19px;height:19px;border-radius:99px;background:var(--panel-2);border:1px solid var(--line-2);color:var(--muted);font-size:11px;display:flex;align-items:center;justify-content:center}

  pre.code{background:#0b0f17;border:1px solid var(--line-2);border-radius:10px;padding:13px;overflow:auto;font-size:12px;line-height:1.6;color:#c7d2e5;white-space:pre-wrap;word-break:break-word;margin:0}
  .kv{display:grid;grid-template-columns:180px 1fr;gap:9px 16px;font-size:13px}
  .kv .k{color:var(--muted-2)}
  .kv .v{color:#cfd7e6;word-break:break-all}
  .copy-row{display:flex;gap:8px;align-items:center}
  .copy-row .input{font-size:12.5px}
  .warn-box{background:rgba(251,191,36,.08);border:1px solid rgba(251,191,36,.3);color:#f3d38a;border-radius:10px;padding:11px 14px;font-size:12.5px;margin-bottom:14px}

  /* ---------- toast / modal ---------- */
  #toasts{position:fixed;right:20px;bottom:20px;display:flex;flex-direction:column;gap:10px;z-index:60}
  .toast{background:#182031;border:1px solid var(--line-2);border-left:3px solid var(--accent);border-radius:10px;padding:11px 15px;min-width:220px;max-width:340px;box-shadow:var(--shadow);font-size:13px;animation:in .18s ease}
  .toast.ok{border-left-color:var(--green)}
  .toast.bad{border-left-color:var(--red)}
  @keyframes in{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
  .modal{position:fixed;inset:0;background:rgba(4,7,12,.65);display:flex;align-items:center;justify-content:center;z-index:70;padding:20px}
  .modal-card{background:var(--panel);border:1px solid var(--line-2);border-radius:16px;padding:22px;max-width:420px;width:100%;box-shadow:var(--shadow)}
  .modal-card h3{margin:0 0 8px;font-size:16px}
  .modal-card p{color:var(--muted);font-size:13px;margin:0 0 18px}
  .modal-actions{display:flex;justify-content:flex-end;gap:10px}

  @media (max-width:980px){
    .cols-4{grid-template-columns:repeat(2,minmax(0,1fr))}
    .cols-3,.cols-2{grid-template-columns:1fr}
  }
  @media (max-width:760px){
    .app{display:block}
    .sidebar{position:static;width:auto;height:auto;flex-direction:row;align-items:center;padding:12px;overflow-x:auto}
    .brand-row{padding:0 12px 0 4px}
    nav{flex-direction:row;margin:0}
    nav a{padding:8px 10px}
    .sidebar-foot{display:none}
    .main{padding:16px}
    .cols-4{grid-template-columns:1fr}
  }
  /* Calm, daylight dashboard. All controls retain their existing behavior. */
  :root{color-scheme:light;--bg:#f5f7fa;--panel:#fff;--panel-2:#f7f9fc;--line:#e7ecf2;--line-2:#d9e1eb;--text:#202d40;--muted:#66758b;--muted-2:#7a8799;--accent:#4275e8;--accent-2:#8b74da;--green:#19947c;--red:#d95566;--amber:#b47c18;--radius:18px;--shadow:0 18px 60px rgba(32,53,88,.08)}
  body{background:var(--bg);font-size:14px;-webkit-font-smoothing:antialiased}
  .sidebar{width:220px;flex-basis:220px;background:#fff;padding:28px 16px 18px}
  .brand-row{padding:0 8px 32px;gap:12px}.brand-row .logo{width:38px;height:38px}
  .brand-row .name{font-size:16px;letter-spacing:.3px}.brand-row .sub{margin-top:3px;letter-spacing:1px;font-size:10px}
  nav{gap:7px}nav a{padding:12px 14px;border-radius:12px;color:#718096}nav a svg{width:19px;height:19px}
  nav a:hover{background:#f5f8fd}nav a.active{background:#edf3ff;border-color:transparent;color:#386bdb;box-shadow:inset 3px 0 #4f80eb}
  .sidebar-foot{padding:18px 8px 0}.main{padding:32px 36px 56px;max-width:1720px;margin:0 auto}
  .topbar{padding-bottom:24px;margin-bottom:26px;border-bottom:1px solid var(--line)}.topbar h2{font-size:23px;font-weight:700;letter-spacing:-.5px}.crumb{margin-top:5px}
  .pill{background:#fff;padding:8px 13px}.icon-btn{width:38px;height:38px}.icon-btn:hover{border-color:#a9bee7;background:#f1f5fe}
  .dashboard-intro{display:flex;justify-content:space-between;align-items:center;gap:20px;margin-bottom:24px}
  .eyebrow{font-size:10px;font-weight:700;letter-spacing:2.5px;color:#7187a5;margin-bottom:7px}
  .dashboard-intro h1{font-size:27px;line-height:1.3;letter-spacing:-.7px;margin:0 0 8px}.dashboard-intro p{margin:0;color:var(--muted);font-size:13px}
  .intro-tag{color:#628170;background:#eaf3ed;border:1px solid #dceadf;border-radius:9px;padding:8px 12px;font-size:12px;white-space:nowrap;display:flex;gap:7px;align-items:center}
  .intro-tag svg{width:15px;height:15px}
  .grid{gap:20px}.card{background:#fff;padding:23px;border-color:#e6ebf2;box-shadow:0 3px 12px rgba(35,56,86,.025)}
  .card h3{font-size:13px;letter-spacing:0;color:#637189}.card-head{margin-bottom:22px;min-height:22px}.card-head h3{font-size:14px;color:#35445b}
  .metric-grid{margin-bottom:24px!important}.metric-card{position:relative;overflow:hidden;padding-top:25px;min-height:169px}
  .metric-card h3{padding-right:42px;margin-bottom:17px}.metric-icon{position:absolute;right:20px;top:20px;width:36px;height:36px;border-radius:11px;display:flex;align-items:center;justify-content:center;background:var(--metric-bg);color:var(--metric-color)}
  .metric-icon svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}
  .metric-card:after{content:"";position:absolute;left:23px;right:23px;bottom:0;height:3px;background:var(--metric-bg);border-radius:4px 4px 0 0}
  .metric-steps{--metric-bg:#eaf1ff;--metric-color:#4f80eb}.metric-sleep{--metric-bg:#f0ecfc;--metric-color:#9275d3}.metric-heart{--metric-bg:#fff0ef;--metric-color:#df7e80}.metric-workouts{--metric-bg:#e7f4ef;--metric-color:#39a58b}
  .stat{font-size:32px;line-height:1.25;letter-spacing:-1px;font-variant-numeric:tabular-nums;font-weight:650}.stat small{font-size:12px;letter-spacing:0;margin-left:6px}.stat-sub{margin-top:12px;font-size:11px}
  .trend-grid{margin-bottom:20px!important}.chart{height:180px}.axis{margin-top:12px;font-variant-numeric:tabular-nums}.legend{margin-top:15px;gap:16px;color:var(--muted)}
  .btn{background:#4779e9;box-shadow:0 3px 7px rgba(66,117,232,.12);border-radius:10px}.btn.ghost{box-shadow:none;background:#f8faff}.btn.ghost:hover{border-color:#b5c7e7}.btn.danger{background:#d95566}
  .input,select,input[type=date]{background:#fafbfd}.seg button.active{background:#fff;color:#386bdb;box-shadow:0 1px 5px #dce3ee}
  th{background:#f6f8fc;color:#65748a}td{color:#3f5068;border-bottom-color:#edf0f5}tr:hover td{background:#f6f9ff}.kv .v{color:#3f5068}
  pre.code{background:#f5f7fc;color:#465b78;border-color:#e0e6ef}.warn-box{background:#fff9ec;color:#906b21;border-color:#f0e0b8}
  .toast{background:#fff}.banner{background:#fff1f2;border-color:#f3d5da;color:#b34253}.empty{padding:50px 20px;color:#8491a3;font-size:13px}
  .workout-row{padding:15px 0;border-bottom:1px solid var(--line)}.workout-row:last-child{border-bottom:0}
  .login-view{background:radial-gradient(ellipse at 22% 20%,#e7eefb,transparent 55%),radial-gradient(ellipse at 80% 80%,#e7f3ef,transparent 55%),#f5f7fa}
  .login-card{background:#fff;border-radius:24px;padding:38px;max-width:440px}.login-brand{margin-bottom:32px}.login-card .hint{line-height:1.8}.login-foot{line-height:1.8}
  :focus-visible{outline:3px solid #8eafea;outline-offset:3px}button:focus-visible,a:focus-visible{outline:3px solid #8eafea;outline-offset:3px}
  @media(min-width:1500px){.main{padding:40px 48px 60px}.chart{height:200px}}
  @media(max-width:1150px){.cols-4{grid-template-columns:repeat(2,minmax(0,1fr))}.main{padding:26px 24px}.sidebar{width:190px;flex-basis:190px}.top-actions{gap:7px}}
  @media(max-width:980px){.cols-2,.cols-3{grid-template-columns:1fr}.dashboard-intro h1{font-size:24px}}
  @media(max-width:760px){.sidebar{width:100%;height:auto;position:sticky;top:0;z-index:20;display:block;padding:14px 16px 0;overflow:visible;box-shadow:0 3px 12px rgba(35,56,86,.04)}.brand-row{padding:0 0 12px}.brand-row .logo{width:30px;height:30px}.brand-row .sub{display:none}nav{overflow-x:auto;gap:4px;padding:0 0 10px;scrollbar-width:thin}nav a{padding:9px 12px;flex-shrink:0;font-size:12px;gap:6px}nav a svg{width:15px;height:15px}.main{padding:22px 16px 36px}.topbar{margin-bottom:22px;padding-bottom:18px;gap:8px}.topbar h2{font-size:20px}.top-actions{gap:6px}.pill{font-size:10px;padding:7px 9px;gap:6px}.icon-btn{width:32px;height:32px}.dashboard-intro{align-items:flex-start;margin-bottom:20px}.dashboard-intro h1{font-size:23px}.dashboard-intro p{font-size:12px;max-width:250px}.intro-tag{display:none}.grid{gap:12px}.cols-4{grid-template-columns:repeat(2,minmax(0,1fr))}.card{padding:18px}.metric-card{min-height:158px}.metric-icon{right:14px;top:16px;width:29px;height:29px}.metric-icon svg{width:17px;height:17px}.metric-card h3{font-size:11px;padding-right:28px}.stat{font-size:25px}.stat-sub{font-size:10px}.metric-card:after{left:18px;right:18px}.card-head{gap:8px}.card-head h3{font-size:13px}.chart{height:165px}.kv{grid-template-columns:1fr;gap:5px}.kv .v{margin-bottom:8px}.copy-row{flex-wrap:wrap}.toolbar .input,.toolbar select{max-width:100%}.banner{flex-wrap:wrap}.login-card{padding:28px 24px}.topbar .crumb{font-size:11px}}
  @media(prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;transition:none!important}}
</style>
</head>
<body>

<div id="loginView" class="login-view">
  <div class="login-card">
    <div class="login-brand">
      <svg class="logo" viewBox="0 0 48 48" fill="none"><rect width="48" height="48" rx="12" fill="#1b2740"/><path d="M14 30V20l6 6 4-9 4 9 6-6v10" stroke="#4f8cff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/><circle cx="31" cy="17" r="2.4" fill="#34d399"/></svg>
      <div><h1>小米健康桥</h1><p>Mi Fitness · Muse Data Bridge</p></div>
    </div>
    <h2>管理后台</h2>
    <div class="hint">首次登录使用服务器 <span class="mono">/opt/health-bridge/.env</span> 里的 <span class="mono">ADMIN_PASSWORD</span>，登录后可在「设置」里修改。</div>
    <div class="field">
      <input id="password" class="input" aria-label="管理密码" type="password" placeholder="管理密码" autocomplete="current-password">
      <button id="btnLogin" class="btn">登录</button>
    </div>
    <div id="loginError" class="error"></div>
    <div class="login-foot">凭据只保存在你的服务器，浏览器只持有一个 12 小时有效的签名 Cookie。</div>
  </div>
</div>

<div id="appView" class="app hidden">
  <aside class="sidebar">
    <div class="brand-row">
      <svg class="logo" viewBox="0 0 48 48" fill="none"><rect width="48" height="48" rx="12" fill="#1b2740"/><path d="M14 30V20l6 6 4-9 4 9 6-6v10" stroke="#4f8cff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/><circle cx="31" cy="17" r="2.4" fill="#34d399"/></svg>
      <div><div class="name">小米健康桥</div><div class="sub">Health Bridge</div></div>
    </div>
    <nav>
      <a href="#/overview" data-nav="overview"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></svg>概览</a>
      <a href="#/data" data-nav="data"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 6h16M4 12h16M4 18h16"/></svg>数据</a>
      <a href="#/sync" data-nav="sync"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M20 12a8 8 0 1 1-2.3-5.6"/><path d="M20 4v4h-4"/></svg>同步</a>
      <a href="#/xiaomi" data-nav="xiaomi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="8" r="3.4"/><path d="M5 20c1.2-3.5 3.8-5.2 7-5.2s5.8 1.7 7 5.2"/></svg>小米账号</a>
      <a href="#/backups" data-nav="backups"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 8h16v11a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V8Z"/><path d="M4 8V6a2 2 0 0 1 2-2h5l2 2h5a2 2 0 0 1 2 2"/></svg>备份</a>
      <a href="#/settings" data-nav="settings"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="3"/><path d="M19 12a7 7 0 0 0-.1-1.2l2-1.6-2-3.4-2.4 1a7 7 0 0 0-2-1.2L14 3h-4l-.5 2.6a7 7 0 0 0-2 1.2l-2.4-1-2 3.4 2 1.6a7 7 0 0 0 0 2.4l-2 1.6 2 3.4 2.4-1a7 7 0 0 0 2 1.2L10 21h4l.5-2.6a7 7 0 0 0 2-1.2l2.4 1 2-3.4-2-1.6c.1-.4.1-.8.1-1.2Z"/></svg>设置</a>
    </nav>
    <div class="sidebar-foot">
      <span id="sideDot" class="dot warn"></span>
      <span id="sideStatus">连接中</span>
      <span id="sideVer" class="ver"></span>
    </div>
  </aside>

  <main class="main">
    <header class="topbar">
      <div>
        <h2 id="pageTitle">概览</h2>
        <div id="pageCrumb" class="crumb">健康数据总览</div>
      </div>
      <div class="top-actions">
        <span id="syncPill" class="pill"><span class="dot warn"></span>加载中</span>
        <button id="btnRefresh" class="icon-btn" title="刷新" aria-label="刷新数据"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M20 12a8 8 0 1 1-2.3-5.6"/><path d="M20 4v4h-4"/></svg></button>
        <button id="btnLogout" class="icon-btn" title="退出" aria-label="退出登录"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3"/><path d="M10 17l-5-5 5-5"/><path d="M5 12h10"/></svg></button>
      </div>
    </header>

    <section id="page-overview" class="page">
      <div class="dashboard-intro">
        <div><div class="eyebrow">YOUR HEALTH, CONNECTED</div><h1>每一天，都更了解自己。</h1><p>步数、睡眠与运动，让健康变化清晰可见。</p></div>
        <div class="intro-tag"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M12 3 4 6v6c0 5 8 9 8 9s8-4 8-9V6Z"/><path d="m8 12 3 3 5-6"/></svg>个人健康数据空间</div>
      </div>
      <div id="overviewBanner" class="banner hidden">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" style="color:#f87171"><path d="M12 9v4"/><path d="M12 17h.01"/><path d="M10.3 3.9 2.6 17a2 2 0 0 0 1.7 3h15.4a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/></svg>
        <span>小米登录已失效，数据暂停更新。</span>
        <button class="btn sm" onclick="location.hash='#/xiaomi'">重新登录</button>
      </div>

      <div class="grid cols-4 metric-grid">
        <div class="card metric-card metric-steps"><div class="metric-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="m13 4-3 5 4 3-2 8M10 9 6 12l-3-1M14 7l3 4h4M7 21l3-5"/><circle cx="16" cy="3" r="1.5"/></svg></div><h3>最近步数</h3><div id="statSteps" class="stat">—</div><div id="statStepsSub" class="stat-sub">—</div></div>
        <div class="card metric-card metric-sleep"><div class="metric-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M20.5 14A9 9 0 0 1 10 3.5 9 9 0 1 0 20.5 14Z"/></svg></div><h3>最近睡眠</h3><div id="statSleep" class="stat">—</div><div id="statSleepSub" class="stat-sub">—</div></div>
        <div class="card metric-card metric-heart"><div class="metric-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M20 13c5-7-4-13-8-6-4-7-13-1-8 6l8 8Z"/><path d="M3 12h5l2-3 3 6 2-3h6"/></svg></div><h3>静息心率</h3><div id="statHr" class="stat">—</div><div id="statHrSub" class="stat-sub">—</div></div>
        <div class="card metric-card metric-workouts"><div class="metric-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="m7 4-3 3 13 13 3-3ZM4 14l6 6M14 4l6 6M2 17l5 5M17 2l5 5"/></svg></div><h3>近 7 天运动</h3><div id="statWorkouts" class="stat">—</div><div id="statWorkoutsSub" class="stat-sub">—</div></div>
      </div>

      <div class="grid cols-2 trend-grid">
        <div class="card">
          <div class="card-head"><h3>步数 · 近 30 天</h3><span id="stepsMeta" class="muted" style="font-size:12px"></span></div>
          <div id="chartSteps"></div>
          <div class="axis"><span id="stepsFrom"></span><span id="stepsTo"></span></div>
        </div>
        <div class="card">
          <div class="card-head"><h3>睡眠结构 · 近 30 天</h3><span class="muted" style="font-size:12px">深睡 / 浅睡 / REM / 清醒</span></div>
          <div id="chartSleep"></div>
          <div class="axis"><span id="sleepFrom"></span><span id="sleepTo"></span></div>
          <div class="legend"><span><i style="background:#7f91db"></i>深睡</span><span><i style="background:#c4d4f7"></i>浅睡</span><span><i style="background:#b49cdd"></i>REM</span><span><i style="background:#e2e7ef"></i>清醒</span></div>
        </div>
      </div>

      <div class="grid cols-2">
        <div class="card">
          <div class="card-head"><h3>静息心率 · 近 30 天</h3><span id="hrMeta" class="muted" style="font-size:12px"></span></div>
          <div id="chartHr"></div>
          <div class="axis"><span id="hrFrom"></span><span id="hrTo"></span></div>
        </div>
        <div class="card">
          <div class="card-head"><h3>最近运动</h3><button class="btn ghost sm" onclick="location.hash='#/data'">查看数据</button></div>
          <div id="recentWorkouts"></div>
        </div>
      </div>
    </section>

    <section id="page-data" class="page hidden">
      <div class="card" style="margin-bottom:14px">
        <div class="toolbar">
          <select id="dataDomain" class="input"></select>
          <div class="seg" id="dataRangeSeg">
            <button data-range="7" class="active">7 天</button>
            <button data-range="30">30 天</button>
            <button data-range="90">90 天</button>
            <button data-range="365">365 天</button>
          </div>
          <input id="dataFrom" class="input" type="date">
          <input id="dataTo" class="input" type="date">
          <button id="btnLoadData" class="btn">查询</button>
          <span class="grow"></span>
          <button id="btnExport" class="btn ghost">导出 CSV</button>
        </div>
        <div id="dataNotes" class="muted" style="font-size:12px;margin-bottom:10px"></div>
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
        <div class="card-head"><h3>各数据域状态</h3><span class="muted" style="font-size:12px">来自 sync_state</span></div>
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

<div id="toasts"></div>
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
  var state = { overview: null, page: "overview", summaryMarkdown: "", token: "", prompt: "" };

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
  function gridLines(h){
    var out = "";
    [0.25,0.5,0.75].forEach(function(p){
      out += '<line x1="0" y1="' + (h*p).toFixed(1) + '" x2="600" y2="' + (h*p).toFixed(1) + '" stroke="#edf1f6" stroke-width="1"/>';
    });
    return out;
  }
  function barChart(values, color){
    var W = 600, H = 150, max = 1;
    values.forEach(function(v){ if(v != null && v > max) max = v; });
    var n = values.length || 1, bw = W / n;
    var bars = "";
    values.forEach(function(v, i){
      var hh = v == null ? 0 : Math.max(2, (v/max) * (H - 16));
      var x = i * bw + bw * 0.18, w = Math.max(1, bw * 0.64), y = H - 8 - hh;
      bars += '<rect x="' + x.toFixed(1) + '" y="' + y.toFixed(1) + '" width="' + w.toFixed(1) + '" height="' + hh.toFixed(1) + '" rx="2.5" fill="' + (v == null ? "#202938" : color) + '"><title>' + (v == null ? "无数据" : fmtNum(v)) + '</title></rect>';
    });
    return '<svg class="chart" viewBox="0 0 ' + W + ' ' + H + '" preserveAspectRatio="none">' + gridLines(H) + bars + '</svg>';
  }
  function stackedSleep(sleep){
    var W = 600, H = 150, n = sleep.dates.length || 1, bw = W / n;
    var colors = { deep: "#7f91db", light: "#c4d4f7", rem: "#b49cdd", awake: "#e2e7ef" };
    var bars = "";
    sleep.dates.forEach(function(d, i){
      var total = (sleep.series.sleep_deep_min[i] || 0) + (sleep.series.sleep_light_min[i] || 0) + (sleep.series.sleep_rem_min[i] || 0) + (sleep.series.sleep_awake_min[i] || 0);
      if(!total){ return; }
      var y = H - 8, x = i*bw + bw*0.18, w = Math.max(1, bw*0.64);
      ["deep","light","rem","awake"].forEach(function(k){
        var key = {deep:"sleep_deep_min", light:"sleep_light_min", rem:"sleep_rem_min", awake:"sleep_awake_min"}[k];
        var v = sleep.series[key][i] || 0; if(!v) return;
        var hh = (v/540) * (H - 16);
        y -= hh;
        bars += '<rect x="' + x.toFixed(1) + '" y="' + y.toFixed(1) + '" width="' + w.toFixed(1) + '" height="' + hh.toFixed(1) + '" fill="' + colors[k] + '"><title>' + d + " " + k + ": " + Math.round(v) + " 分钟</title></rect>";
      });
    });
    return '<svg class="chart" viewBox="0 0 ' + W + ' ' + H + '" preserveAspectRatio="none">' + gridLines(H) + bars + '</svg>';
  }
  function lineChart(values, color){
    var W = 600, H = 150, pts = [], vals = values.filter(function(v){ return v != null; });
    if(!vals.length){ return '<svg class="chart" viewBox="0 0 ' + W + ' ' + H + '"><text x="300" y="76" text-anchor="middle" fill="#5f6b7f" font-size="13">暂无数据</text></svg>'; }
    var min = Math.min.apply(null, vals), max = Math.max.apply(null, vals);
    var span = (max - min) || 1, pad = (H - 26) / 2, n = values.length;
    var d = "", area = "";
    values.forEach(function(v, i){
      if(v == null){ return; }
      var x = (i/(n-1)) * (W - 8) + 4;
      var y = H - 22 - ((v - min)/span) * (H - 40);
      d += (d ? " L" : "M") + x.toFixed(1) + " " + y.toFixed(1);
      pts.push([x, y]);
    });
    if(pts.length > 1){
      area = "M" + pts[0][0].toFixed(1) + " " + (H-22) + " L" + pts.map(function(p){ return p[0].toFixed(1) + " " + p[1].toFixed(1); }).join(" L") + " L" + pts[pts.length-1][0].toFixed(1) + " " + (H-22) + " Z";
    }
    return '<svg class="chart" viewBox="0 0 ' + W + ' ' + H + '" preserveAspectRatio="none">' + gridLines(H) +
      '<path d="' + area + '" fill="' + color + '" opacity="0.10"/>' +
      '<path d="' + d + '" fill="none" stroke="' + color + '" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>' +
      pts.map(function(p){ return '<circle cx="' + p[0].toFixed(1) + '" cy="' + p[1].toFixed(1) + '" r="2" fill="' + color + '"/>'; }).join("") +
      '<text x="6" y="12" fill="#5f6b7f" font-size="11">' + fmtNum(max,1) + '</text>' +
      '<text x="6" y="' + (H-8) + '" fill="#5f6b7f" font-size="11">' + fmtNum(min,1) + '</text>' +
      '</svg>';
  }

  /* ---------------- pages ---------------- */
  var PAGE_META = {
    overview: ["概览", "健康数据总览"],
    data: ["数据", "按日期与指标浏览，支持导出 CSV"],
    sync: ["同步", "手动同步与各数据域状态"],
    xiaomi: ["小米账号", "扫码登录与会话状态"],
    backups: ["备份", "SQLite 与登录态备份"],
    settings: ["设置", "运行配置、MCP 接入与审计"]
  };

  function showLogin(){ $("#loginView").classList.remove("hidden"); $("#appView").classList.add("hidden"); }
  function showApp(){ $("#loginView").classList.add("hidden"); $("#appView").classList.remove("hidden"); }

  function setStatus(ok, text){
    var dot = $("#sideDot"); var pill = $("#syncPill");
    dot.className = "dot " + (ok ? "" : "bad");
    $("#sideStatus").textContent = text;
    pill.innerHTML = '<span class="dot ' + (ok ? "" : "bad") + '"></span>' + esc(text);
  }

  function renderOverview(data){
    state.overview = data;
    var s = data.session, o = data.summary.overview, t = data.timeline;
    var daily = data.summary.daily || [];
    var last = daily.length ? daily[daily.length-1] : null;
    $("#overviewBanner").classList.toggle("hidden", !s.expired);

    $("#statSteps").innerHTML = (last && last.steps != null ? fmtNum(last.steps) : "—") + '<small>步</small>';
    $("#statStepsSub").textContent = last ? (last.date + " · 距离 " + fmtFloat((last.distance_m||0)/1000,2) + " km") : "暂无数据";
    $("#statSleep").innerHTML = last && last.sleep_total_min != null ? fmtMin(last.sleep_total_min) : "—";
    $("#statSleepSub").textContent = last ? ("深睡 " + fmtMin(last.sleep_deep_min) + " · REM " + fmtMin(last.sleep_rem_min)) : "暂无数据";
    $("#statHr").innerHTML = last && last.hr_resting != null ? fmtNum(last.hr_resting) + '<small>bpm</small>' : "—";
    $("#statHrSub").textContent = last ? (last.date + " · 日均 " + fmtNum(last.hr_avg)) : "暂无数据";
    $("#statWorkouts").innerHTML = fmtNum(o.workout_count) + '<small>次</small>';
    $("#statWorkoutsSub").textContent = o.workout_count
      ? (o.workout_distance_m ? ("合计 " + fmtFloat(o.workout_distance_m/1000,1) + " km") : "近 7 天")
      : ((data.recent_workouts && data.recent_workouts.length) ? ("最近一次 " + (data.recent_workouts[0].date || "")) : "暂无运动记录");

    $("#chartSteps").innerHTML = barChart(t.series.steps, "#4f8cff");
    $("#chartSleep").innerHTML = stackedSleep(t);
    $("#chartHr").innerHTML = lineChart(t.series.hr_resting, "#db858c");
    $("#stepsMeta").textContent = "合计 " + fmtNum(t.series.steps.reduce(function(a,b){ return a + (b||0); }, 0)) + " 步";
    var hrVals = t.series.hr_resting.filter(function(v){ return v != null; });
    $("#hrMeta").textContent = hrVals.length ? ("均值 " + fmtFloat(hrVals.reduce(function(a,b){ return a+b; },0)/hrVals.length,0) + " bpm") : "";
    ["steps","sleep","hr"].forEach(function(k){
      $("#" + k + "From").textContent = t.from;
      $("#" + k + "To").textContent = t.to;
    });

    var wl = data.recent_workouts || [];
    if(!wl.length){ $("#recentWorkouts").innerHTML = '<div class="empty">暂无运动记录</div>'; }
    else {
      $("#recentWorkouts").innerHTML = wl.map(function(w){
        var meta = [sportLabel(w.sport), w.distance_m ? fmtFloat(w.distance_m/1000,2)+" km" : "", w.duration_s ? Math.round(w.duration_s/60)+" 分钟" : "", w.avg_hr ? "心率 "+fmtNum(w.avg_hr) : ""].filter(Boolean).join(" · ");
        return '<div class="workout-row"><div style="display:flex;justify-content:space-between;gap:10px"><span style="font-weight:600">' + esc(sportLabel(w.sport)) + '</span><span class="muted" style="font-size:12px">' + esc((w.start_time||w.date||"").slice(0,16).replace("T"," ")) + '</span></div><div class="muted" style="font-size:12px;margin-top:2px">' + esc(meta) + '</div></div>';
      }).join("");
    }

    var sync = data.sync || {};
    if(sync.state === "running"){ setStatus(false, "同步中"); }
    else if(s.expired){ setStatus(false, "需要重新登录"); }
    else if(s.last_sync_at){ var age = (Date.now()-new Date(s.last_sync_at).getTime())/3600000; setStatus(age < 36, "同步于 " + rel(s.last_sync_at)); }
    else { setStatus(false, "尚未同步"); }
    $("#sideVer").textContent = "v" + (data.version || "");

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
      resultEl.innerHTML = '<span style="color:' + (errs ? "#fbbf24" : "#34d399") + '">' + (errs ? "完成，但有 " + errs + " 个错误" : "同步完成") + '</span>' +
        ' · 范围 ' + esc(r.from || "") + ' ~ ' + esc(r.to || "") + ' · ' + fmtNum(r.days) + ' 天 · ' + fmtNum(r.chunks) + ' 个分块';
      if(errs){ resultEl.innerHTML += '<div class="err" style="margin-top:4px;font-size:11.5px">' + esc((r.errors || []).slice(0, 3).join("；")) + '</div>'; }
    } else if(sync.state === "error"){
      resultEl.innerHTML = '<span style="color:#f87171">同步失败：' + esc(sync.error || "") + '</span>';
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
    $("#xmSession").innerHTML = s.expired ? '<span style="color:#f87171">已失效，需要重新登录</span>' : '<span style="color:#34d399">正常</span>';
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
    $$("#dataRangeSeg button").forEach(function(b){ b.classList.toggle("active", Number(b.dataset.range) === days); });
    loadData();
  }
  var ALL_COLUMNS = ["date","steps","distance_m","sleep_total_min","sleep_deep_min","sleep_rem_min","hr_resting","hr_avg","spo2_avg","stress_avg","weight_kg","active_kcal"];
  var COLUMN_LABELS = {
    steps:"步数", distance_m:"距离(m)", step_calories:"步行千卡", active_kcal:"活动千卡", resting_kcal:"静息千卡",
    intake_kcal:"摄入千卡", total_kcal:"总千卡", hr_avg:"平均心率", hr_min:"最低心率", hr_max:"最高心率", hr_resting:"静息心率",
    sleep_total_min:"睡眠", sleep_deep_min:"深睡", sleep_light_min:"浅睡", sleep_rem_min:"REM", sleep_awake_min:"清醒",
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
    $$("nav a").forEach(function(a){ a.classList.toggle("active", a.dataset.nav === page); });
  }
  function route(){
    var raw = location.hash.replace(/^#\//, "");
    var page = PAGE_META[raw] ? raw : "overview";
    state.page = page;
    $$(".page").forEach(function(p){ p.classList.add("hidden"); });
    var el = $("#page-" + page); if(el){ el.classList.remove("hidden"); }
    $("#pageTitle").textContent = PAGE_META[page][0];
    $("#pageCrumb").textContent = PAGE_META[page][1];
    setActiveNav(page);
    if(page === "data"){ initDataPage(); }
    if(page === "backups"){ loadBackups(); }
    if(page === "settings"){ loadSettings(); }
    if(page === "sync"){ loadSchedule(); }
    if(page === "sync" || page === "xiaomi" || page === "overview"){ loadOverview(); }
  }

  /* ---------------- boot ---------------- */
  function bind(){
    $("#btnLogin").onclick = login;
    $("#password").addEventListener("keydown", function(e){ if(e.key === "Enter"){ login(); } });
    $("#btnLogout").onclick = async function(){ try{ await api("/logout", {method:"POST", body:{}}); }catch(e){}; location.reload(); };
    $("#btnRefresh").onclick = function(){ loadOverview(); route(); };
    $("#btnLoadData").onclick = loadData;
    $("#btnExport").onclick = function(){
      var domain = $("#dataDomain").value, from = $("#dataFrom").value, to = $("#dataTo").value;
      window.location = "/admin/api/export.csv?domain=" + encodeURIComponent(domain) + "&start=" + from + "&end=" + to;
    };
    $$("#syncSeg button").forEach(function(b){ b.onclick = function(){ startSync(Number(b.dataset.days)); }; });
    $("#schedMode").onchange = toggleSchedule;
    $("#btnSaveSchedule").onclick = saveSchedule;
    $$("#dataRangeSeg button").forEach(function(b){ b.onclick = function(){ setDataRange(Number(b.dataset.range)); }; });
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
    try{
      await api("/session", {method:"POST", body:{password: $("#password").value}});
      showApp(); route(); loadOverview(); startPolling();
    } catch(e){ $("#loginError").textContent = e.message; }
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
