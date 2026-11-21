(function (global) {
  "use strict";

  const WEEKDAYS = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];

  function weekdayLabel(isoDate) {
    if (!isoDate) return "";
    const parts = isoDate.split("-").map(Number);
    const dt = new Date(parts[0], parts[1] - 1, parts[2]);
    return WEEKDAYS[dt.getDay()] || "";
  }

  function shortDate(isoDate) {
    if (!isoDate || isoDate.length < 10) return isoDate || "";
    return isoDate.slice(5);
  }

  function fmtMin(min) {
    if (min == null || Number.isNaN(Number(min))) return "—";
    const total = Math.round(Number(min));
    const h = Math.floor(total / 60);
    const m = total % 60;
    return h > 0 ? `${h}h ${String(m).padStart(2, "0")}m` : `${m}m`;
  }

  function fmtNum(v, decimals) {
    if (v == null || Number.isNaN(Number(v))) return "—";
    return Number(v).toLocaleString("zh-CN", {
      minimumFractionDigits: decimals || 0,
      maximumFractionDigits: decimals || 0,
    });
  }

  function escapeHtml(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function sparkline(values, opts) {
    const cfg = opts || {};
    const mode = cfg.mode || "line";
    const color = cfg.color || "#e85420";
    const w = 82;
    const h = 34;
    const clean = (values || []).map((v) => (v == null ? null : Number(v)));
    const nums = clean.filter((v) => v != null && !Number.isNaN(v));
    if (!nums.length) {
      return `<svg class="kpi-spark" viewBox="0 0 ${w} ${h}" aria-hidden="true">
        <line x1="2" y1="${h - 6}" x2="${w - 2}" y2="${h - 6}" stroke="rgba(21,24,30,0.12)" stroke-dasharray="3 3" />
      </svg>`;
    }

    if (mode === "bars") {
      const maxV = Math.max(...nums, 1);
      const count = clean.length;
      const gap = 3;
      const barW = Math.max(3, (w - gap * (count - 1)) / count);
      const rects = clean
        .map((v, i) => {
          const x = i * (barW + gap);
          const bh = v == null ? 2 : Math.max(4, (v / maxV) * (h - 4));
          const y = h - bh;
          const opacity = v == null ? 0.14 : i === count - 1 ? 1 : 0.62;
          return `<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${barW.toFixed(1)}" height="${bh.toFixed(1)}" rx="2" fill="${color}" fill-opacity="${opacity}" />`;
        })
        .join("");
      return `<svg class="kpi-spark" viewBox="0 0 ${w} ${h}" aria-hidden="true">${rects}</svg>`;
    }

    const minV = Math.min(...nums);
    const maxV = Math.max(...nums);
    const span = maxV - minV || 1;
    const padY = 4;
    const usableH = h - padY * 2;
    const pts = [];
    clean.forEach((v, i) => {
      if (v == null) return;
      const x = clean.length === 1 ? w / 2 : 3 + (i / (clean.length - 1)) * (w - 6);
      const y = h - padY - ((v - minV) / span) * usableH;
      pts.push([x, y]);
    });
    const poly = pts.map((p) => `${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" ");
    const last = pts[pts.length - 1];
    return `<svg class="kpi-spark" viewBox="0 0 ${w} ${h}" aria-hidden="true">
      <polyline fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" points="${poly}" />
      ${last ? `<circle cx="${last[0].toFixed(1)}" cy="${last[1].toFixed(1)}" r="2.8" fill="${color}" />` : ""}
    </svg>`;
  }

  function sleepRing(deepMin, lightMin, remMin, totalMin) {
    const deep = Math.max(0, Number(deepMin) || 0);
    const light = Math.max(0, Number(lightMin) || 0);
    const rem = Math.max(0, Number(remMin) || 0);
    const sum = deep + light + rem;
    const size = 156;
    const cx = size / 2;
    const cy = size / 2;
    const r = 58;
    const circ = 2 * Math.PI * r;

    let arcs = `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="rgba(21,24,30,0.07)" stroke-width="14" />`;
    if (sum > 0) {
      const segs = [
        { val: deep, color: "#3f51b5" },
        { val: light, color: "#8ea0ff" },
        { val: rem, color: "#0ea5a4" },
      ];
      let offset = 0;
      arcs += segs
        .filter((s) => s.val > 0)
        .map((s) => {
          const frac = s.val / sum;
          const dash = Math.max(0, frac * circ - 2.5);
          const el = `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${s.color}" stroke-width="14"
            stroke-dasharray="${dash.toFixed(2)} ${circ.toFixed(2)}"
            stroke-dashoffset="${(-offset).toFixed(2)}"
            stroke-linecap="butt" transform="rotate(-90 ${cx} ${cy})" />`;
          offset += frac * circ;
          return el;
        })
        .join("");
    }

    const centerText = totalMin != null ? fmtMin(totalMin) : "—";
    return `<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" role="img" aria-label="睡眠结构占比">
      ${arcs}
      <text x="${cx}" y="${cy - 4}" text-anchor="middle" font-size="20" font-weight="700" fill="#15181e" style="font-variant-numeric:tabular-nums">${escapeHtml(centerText)}</text>
      <text x="${cx}" y="${cy + 16}" text-anchor="middle" font-size="11.5" fill="#7b8391">7日日均睡眠</text>
    </svg>`;
  }

  function niceTicks(minV, maxV, count) {
    const stepRaw = (maxV - minV) / Math.max(1, count - 1);
    if (stepRaw <= 0) return [minV, minV + 1];
    const mag = Math.pow(10, Math.floor(Math.log10(stepRaw)));
    const norm = stepRaw / mag;
    let nice = 1;
    if (norm <= 1) nice = 1;
    else if (norm <= 2) nice = 2;
    else if (norm <= 2.5) nice = 2.5;
    else if (norm <= 5) nice = 5;
    else nice = 10;
    const step = nice * mag;
    const start = Math.floor(minV / step) * step;
    const end = Math.ceil(maxV / step) * step;
    const out = [];
    for (let v = start; v <= end + step * 0.001; v += step) {
      out.push(Number(v.toFixed(4)));
    }
    return out;
  }

  function trendChart(container, opts) {
    if (!container) return;
    const timeline = opts.timeline;
    const metric = opts.metric || "steps";
    if (!timeline || !timeline.dates || !timeline.dates.length) {
      container.innerHTML = `<div class="empty-state"><strong>暂无趋势数据</strong><p>完成首次同步后将自动绘制健康曲线。</p></div>`;
      return;
    }

    const dates = timeline.dates;
    const series = timeline.series || {};
    const workouts = timeline.workouts || [];
    const n = dates.length;

    const W = 760;
    const H = 264;
    const pad = { top: 18, right: 16, bottom: 32, left: 50 };
    const plotW = W - pad.left - pad.right;
    const plotH = H - pad.top - pad.bottom;

    const vals = (series[metric === "sleep" ? "sleep_total_min" : metric] || []).map((v) =>
      v == null ? null : Number(v)
    );
    const valid = vals.filter((v) => v != null && !Number.isNaN(v));

    if (!valid.length) {
      container.innerHTML = `<div class="empty-state"><strong>该指标在所选周期内暂无记录</strong><p>可以切换其他指标或拉长统计周期。</p></div>`;
      return;
    }

    let yMin = 0;
    let yMax = Math.max(...valid);
    let ticks = [];
    let refLine = null;
    let yFormatter = (v) => fmtNum(v, 0);

    if (metric === "steps") {
      yMax = Math.max(yMax * 1.12, 8000);
      ticks = niceTicks(0, yMax, 5);
      yMax = ticks[ticks.length - 1];
      refLine = { value: 8000, label: "8,000 步" };
      yFormatter = (v) => (v >= 1000 ? `${(v / 1000).toFixed(v % 1000 === 0 ? 0 : 1)}k` : String(v));
    } else if (metric === "sleep") {
      yMax = Math.max(yMax * 1.12, 480);
      ticks = [0, 180, 360, 480, 600].filter((t) => t <= Math.max(600, Math.ceil(yMax / 60) * 60));
      if (yMax > ticks[ticks.length - 1]) ticks.push(Math.ceil(yMax / 60) * 60);
      yMax = ticks[ticks.length - 1];
      refLine = { value: 480, label: "8h 参考" };
      yFormatter = (v) => `${Math.round(v / 60)}h`;
    } else if (metric === "hr_resting") {
      yMin = Math.max(35, Math.floor((Math.min(...valid) - 5) / 5) * 5);
      yMax = Math.ceil((Math.max(...valid) + 5) / 5) * 5;
      ticks = niceTicks(yMin, yMax, 5);
      yMin = ticks[0];
      yMax = ticks[ticks.length - 1];
      yFormatter = (v) => `${Math.round(v)}`;
    } else if (metric === "spo2_avg") {
      yMin = Math.min(92, Math.floor(Math.min(...valid) - 2));
      yMax = 100;
      ticks = niceTicks(yMin, 100, 5);
      yMin = ticks[0];
      yMax = 100;
      refLine = { value: 95, label: "95%" };
      yFormatter = (v) => `${Math.round(v)}%`;
    } else if (metric === "stress_avg") {
      yMax = Math.max(80, Math.ceil((yMax + 10) / 20) * 20);
      ticks = [0, 25, 50, 75, 100].filter((t) => t <= Math.max(100, yMax));
      yMax = ticks[ticks.length - 1];
      yFormatter = (v) => String(v);
    } else {
      yMax = Math.max(yMax * 1.15, 200);
      ticks = niceTicks(0, yMax, 5);
      yMax = ticks[ticks.length - 1];
      yFormatter = (v) => `${Math.round(v)}`;
    }

    const slotW = plotW / n;
    const xAt = (i) => pad.left + slotW * (i + 0.5);
    const yAt = (v) => pad.top + plotH - ((v - yMin) / Math.max(1e-6, yMax - yMin)) * plotH;

    // Gridlines & Y labels
    const gridSvg = ticks
      .map((t) => {
        const y = yAt(t);
        return `<line x1="${pad.left}" y1="${y.toFixed(1)}" x2="${W - pad.right}" y2="${y.toFixed(1)}" stroke="rgba(21,24,30,0.07)" />
          <text x="${pad.left - 9}" y="${(y + 4).toFixed(1)}" text-anchor="end" font-size="11" fill="#7b8391" style="font-variant-numeric:tabular-nums">${escapeHtml(yFormatter(t))}</text>`;
      })
      .join("");

    // Reference guide line (drawn on top with crisp pill label)
    let refSvg = "";
    if (refLine && refLine.value >= yMin && refLine.value <= yMax) {
      const ry = yAt(refLine.value);
      const pillW = Math.max(46, refLine.label.length * 9 + 14);
      const pillX = W - pad.right - pillW;
      const pillY = Math.max(pad.top, ry - 21);
      refSvg = `<line x1="${pad.left}" y1="${ry.toFixed(1)}" x2="${W - pad.right}" y2="${ry.toFixed(1)}" stroke="rgba(232,84,32,0.48)" stroke-width="1.2" stroke-dasharray="4 4" />
        <rect x="${pillX.toFixed(1)}" y="${pillY.toFixed(1)}" width="${pillW}" height="17" rx="5" fill="rgba(255,255,255,0.94)" stroke="rgba(232,84,32,0.32)" stroke-width="1" />
        <text x="${(pillX + pillW / 2).toFixed(1)}" y="${(pillY + 12).toFixed(1)}" text-anchor="middle" font-size="10" font-weight="700" fill="#c2410c">${escapeHtml(refLine.label)}</text>`;
    }

    // X-axis labels
    const labelEvery = Math.max(1, Math.ceil(n / 8));
    const xLabels = dates
      .map((d, i) => {
        if (i !== 0 && i !== n - 1 && i % labelEvery !== 0) return "";
        if (i !== n - 1 && n - 1 - i < Math.ceil(labelEvery * 0.55)) return "";
        return `<text x="${xAt(i).toFixed(1)}" y="${H - 8}" text-anchor="middle" font-size="11" fill="#7b8391" style="font-variant-numeric:tabular-nums">${escapeHtml(shortDate(d))}</text>`;
      })
      .join("");

    // Series geometry
    let dataSvg = "";
    const barW = Math.max(4, Math.min(22, slotW * 0.62));

    if (metric === "steps" || metric === "stress_avg") {
      dataSvg += vals
        .map((v, i) => {
          if (v == null) return "";
          const x = xAt(i) - barW / 2;
          const y = yAt(v);
          const bh = Math.max(2, pad.top + plotH - y);
          let fill = "#e85420";
          if (metric === "stress_avg") {
            fill = v < 30 ? "#0d9488" : v < 55 ? "#d97706" : "#dc2626";
          }
          return `<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${barW.toFixed(1)}" height="${bh.toFixed(1)}" rx="3" fill="${fill}" fill-opacity="0.86" />`;
        })
        .join("");

      if (metric === "steps" && n >= 7) {
        const maPts = [];
        for (let i = 0; i < n; i++) {
          let sum = 0;
          let cnt = 0;
          for (let j = Math.max(0, i - 6); j <= i; j++) {
            if (vals[j] != null) {
              sum += vals[j];
              cnt += 1;
            }
          }
          if (cnt >= 2) {
            maPts.push(`${xAt(i).toFixed(1)},${yAt(sum / cnt).toFixed(1)}`);
          }
        }
        if (maPts.length >= 2) {
          dataSvg += `<polyline fill="none" stroke="#15181e" stroke-opacity="0.6" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" points="${maPts.join(" ")}" />`;
        }
      }
    } else if (metric === "sleep") {
      const deepArr = series.sleep_deep_min || [];
      const lightArr = series.sleep_light_min || [];
      const remArr = series.sleep_rem_min || [];
      dataSvg += vals
        .map((total, i) => {
          if (total == null || total <= 0) return "";
          const x = xAt(i) - barW / 2;
          const deep = Number(deepArr[i]) || 0;
          const light = Number(lightArr[i]) || 0;
          const rem = Number(remArr[i]) || 0;
          const staged = deep + light + rem;
          if (staged <= 0) {
            const y = yAt(total);
            const bh = Math.max(2, pad.top + plotH - y);
            return `<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${barW.toFixed(1)}" height="${bh.toFixed(1)}" rx="3" fill="#94a3b8" fill-opacity="0.72" />`;
          }
          const extra = Math.max(0, total - staged);
          const parts = [
            { v: deep, c: "#3f51b5" },
            { v: light, c: "#8ea0ff" },
            { v: rem, c: "#0ea5a4" },
            { v: extra, c: "#f59e0b" },
          ];
          let acc = 0;
          return parts
            .filter((p) => p.v > 0)
            .map((p) => {
              const yBottom = yAt(acc);
              const yTop = yAt(acc + p.v);
              acc += p.v;
              return `<rect x="${x.toFixed(1)}" y="${yTop.toFixed(1)}" width="${barW.toFixed(1)}" height="${Math.max(1.5, yBottom - yTop).toFixed(1)}" rx="1.5" fill="${p.c}" />`;
            })
            .join("");
        })
        .join("");
    } else {
      const palette =
        metric === "hr_resting"
          ? { stroke: "#e11d48", fill: "rgba(225,29,72,0.12)" }
          : metric === "spo2_avg"
          ? { stroke: "#0284c7", fill: "rgba(2,132,199,0.12)" }
          : { stroke: "#e85420", fill: "rgba(232,84,32,0.13)" };

      const segs = [];
      let cur = [];
      vals.forEach((v, i) => {
        if (v == null) {
          if (cur.length) segs.push(cur);
          cur = [];
        } else {
          cur.push({ i, x: xAt(i), y: yAt(v), v });
        }
      });
      if (cur.length) segs.push(cur);

      const baseY = pad.top + plotH;
      segs.forEach((seg) => {
        if (seg.length >= 2) {
          const linePath = seg.map((p, idx) => `${idx === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");
          const areaPath = `${linePath} L${seg[seg.length - 1].x.toFixed(1)},${baseY.toFixed(1)} L${seg[0].x.toFixed(1)},${baseY.toFixed(1)} Z`;
          dataSvg += `<path d="${areaPath}" fill="${palette.fill}" />`;
          dataSvg += `<path d="${linePath}" fill="none" stroke="${palette.stroke}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />`;
        }
        seg.forEach((p) => {
          dataSvg += `<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="${n > 45 ? 2.2 : 3.2}" fill="#ffffff" stroke="${palette.stroke}" stroke-width="2" />`;
        });
      });
    }

    // Workout markers along bottom axis
    const workoutSvg = workouts
      .map((cnt, i) => {
        if (!cnt) return "";
        const cx = xAt(i);
        const cy = pad.top + plotH + 5;
        return `<circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="2.6" fill="#0d9488" />`;
      })
      .join("");

    // Hover zones
    const zones = dates
      .map((_, i) => {
        const zx = pad.left + slotW * i;
        return `<rect class="hb-zone" data-idx="${i}" x="${zx.toFixed(1)}" y="${pad.top}" width="${slotW.toFixed(1)}" height="${plotH}" fill="transparent" />`;
      })
      .join("");

    container.innerHTML = `
      <svg class="chart-svg" viewBox="0 0 ${W} ${H}" role="img" aria-label="健康趋势图">
        ${gridSvg}
        <line class="hb-crosshair" x1="0" y1="${pad.top}" x2="0" y2="${pad.top + plotH}" stroke="rgba(21,24,30,0.28)" stroke-dasharray="3 3" visibility="hidden" />
        ${dataSvg}
        ${refSvg}
        ${workoutSvg}
        ${xLabels}
        ${zones}
      </svg>
      <div class="chart-tooltip"></div>
    `;

    const svgEl = container.querySelector("svg");
    const crosshair = container.querySelector(".hb-crosshair");
    const tip = container.querySelector(".chart-tooltip");

    function showTip(idx) {
      const d = dates[idx];
      const cx = xAt(idx);
      crosshair.setAttribute("x1", cx.toFixed(1));
      crosshair.setAttribute("x2", cx.toFixed(1));
      crosshair.setAttribute("visibility", "visible");

      let rowsHtml = "";
      if (metric === "steps") {
        rowsHtml += `<div class="chart-tt-row"><span><i class="chart-tt-dot" style="background:#e85420"></i>步数</span><strong>${vals[idx] != null ? fmtNum(vals[idx], 0) + " 步" : "无记录"}</strong></div>`;
        const kcal = (series.active_kcal || [])[idx];
        if (kcal != null) rowsHtml += `<div class="chart-tt-row"><span>活动消耗</span><strong>${fmtNum(kcal, 0)} kcal</strong></div>`;
      } else if (metric === "sleep") {
        const tot = vals[idx];
        const dp = (series.sleep_deep_min || [])[idx];
        const lt = (series.sleep_light_min || [])[idx];
        const rm = (series.sleep_rem_min || [])[idx];
        rowsHtml += `<div class="chart-tt-row"><span>总睡眠</span><strong>${fmtMin(tot)}</strong></div>`;
        if (dp != null) rowsHtml += `<div class="chart-tt-row"><span><i class="chart-tt-dot" style="background:#3f51b5"></i>深睡</span><strong>${fmtMin(dp)}</strong></div>`;
        if (lt != null) rowsHtml += `<div class="chart-tt-row"><span><i class="chart-tt-dot" style="background:#8ea0ff"></i>浅睡</span><strong>${fmtMin(lt)}</strong></div>`;
        if (rm != null) rowsHtml += `<div class="chart-tt-row"><span><i class="chart-tt-dot" style="background:#0ea5a4"></i>REM</span><strong>${fmtMin(rm)}</strong></div>`;
      } else if (metric === "hr_resting") {
        rowsHtml += `<div class="chart-tt-row"><span><i class="chart-tt-dot" style="background:#e11d48"></i>静息心率</span><strong>${vals[idx] != null ? Math.round(vals[idx]) + " bpm" : "无记录"}</strong></div>`;
        const avgHr = (series.hr_avg || [])[idx];
        if (avgHr != null) rowsHtml += `<div class="chart-tt-row"><span>日均心率</span><strong>${Math.round(avgHr)} bpm</strong></div>`;
      } else if (metric === "spo2_avg") {
        rowsHtml += `<div class="chart-tt-row"><span><i class="chart-tt-dot" style="background:#0284c7"></i>平均血氧</span><strong>${vals[idx] != null ? vals[idx].toFixed(1) + "%" : "无记录"}</strong></div>`;
      } else if (metric === "stress_avg") {
        const v = vals[idx];
        const tag = v == null ? "" : v < 30 ? "放松" : v < 55 ? "中等" : "偏高";
        rowsHtml += `<div class="chart-tt-row"><span><i class="chart-tt-dot" style="background:#d97706"></i>平均压力</span><strong>${v != null ? Math.round(v) + " · " + tag : "无记录"}</strong></div>`;
      } else {
        rowsHtml += `<div class="chart-tt-row"><span><i class="chart-tt-dot" style="background:#e85420"></i>活动消耗</span><strong>${vals[idx] != null ? fmtNum(vals[idx], 0) + " kcal" : "无记录"}</strong></div>`;
      }

      if (workouts[idx]) {
        rowsHtml += `<div class="chart-tt-row"><span><i class="chart-tt-dot" style="background:#0d9488"></i>当日运动</span><strong>${workouts[idx]} 次</strong></div>`;
      }

      tip.innerHTML = `<div class="chart-tt-date"><span>${escapeHtml(d)}</span><span>${escapeHtml(weekdayLabel(d))}</span></div>${rowsHtml}`;

      const rect = svgEl.getBoundingClientRect();
      const px = (cx / W) * rect.width;
      const clampedX = Math.max(92, Math.min(rect.width - 92, px));
      const py = vals[idx] != null ? (yAt(vals[idx]) / H) * rect.height : rect.height * 0.45;
      tip.style.left = `${clampedX}px`;
      tip.style.top = `${Math.max(58, py)}px`;
      tip.classList.add("visible");
    }

    container.querySelectorAll(".hb-zone").forEach((z) => {
      z.addEventListener("mouseenter", () => showTip(Number(z.dataset.idx)));
      z.addEventListener("touchstart", () => showTip(Number(z.dataset.idx)), { passive: true });
    });

    svgEl.addEventListener("mouseleave", () => {
      crosshair.setAttribute("visibility", "hidden");
      tip.classList.remove("visible");
    });
  }

  function sleepLabChart(container, sleepPayload, selectedDate, onSelect) {
    if (!container) return;
    if (!sleepPayload || !sleepPayload.dates || !sleepPayload.dates.length) {
      container.innerHTML = `<div class="empty-state"><strong>暂无睡眠记录</strong><p>同步睡眠数据后将展示主睡眠阶段与小睡分布。</p></div>`;
      return;
    }

    const dates = sleepPayload.dates;
    const byDate = {};
    (sleepPayload.days || []).forEach((d) => {
      byDate[d.date] = d;
    });

    const n = dates.length;
    const W = 980;
    const H = 280;
    const pad = { top: 20, right: 18, bottom: 34, left: 48 };
    const plotW = W - pad.left - pad.right;
    const plotH = H - pad.top - pad.bottom;

    const maxTotal = Math.max(
      540,
      ...(sleepPayload.days || []).map((d) => Number(d.total_min) || 0)
    );
    const yMax = Math.ceil(maxTotal / 60) * 60;
    const ticks = [];
    for (let m = 0; m <= yMax; m += 120) ticks.push(m);
    if (ticks[ticks.length - 1] < yMax) ticks.push(yMax);

    const slotW = plotW / n;
    const barW = Math.max(5, Math.min(24, slotW * 0.64));
    const xAt = (i) => pad.left + slotW * (i + 0.5);
    const yAt = (v) => pad.top + plotH - (v / Math.max(1, yMax)) * plotH;

    const gridSvg = ticks
      .map((t) => {
        const y = yAt(t);
        return `<line x1="${pad.left}" y1="${y.toFixed(1)}" x2="${W - pad.right}" y2="${y.toFixed(1)}" stroke="rgba(21,24,30,0.07)" />
          <text x="${pad.left - 9}" y="${(y + 4).toFixed(1)}" text-anchor="end" font-size="11" fill="#7b8391">${Math.round(t / 60)}h</text>`;
      })
      .join("");

    const refY = yAt(480);
    const refPillW = 62;
    const refPillX = W - pad.right - refPillW;
    const refPillY = Math.max(4, refY - 21);
    const refSvg = `<line x1="${pad.left}" y1="${refY.toFixed(1)}" x2="${W - pad.right}" y2="${refY.toFixed(1)}" stroke="rgba(63,81,181,0.45)" stroke-width="1.2" stroke-dasharray="4 4" />
      <rect x="${refPillX.toFixed(1)}" y="${refPillY.toFixed(1)}" width="${refPillW}" height="17" rx="5" fill="rgba(255,255,255,0.94)" stroke="rgba(63,81,181,0.32)" stroke-width="1" />
      <text x="${(refPillX + refPillW / 2).toFixed(1)}" y="${(refPillY + 12).toFixed(1)}" text-anchor="middle" font-size="10" font-weight="700" fill="#3f51b5">8h 推荐线</text>`;

    const labelEvery = Math.max(1, Math.ceil(n / 10));
    const xLabels = dates
      .map((d, i) => {
        if (i !== 0 && i !== n - 1 && i % labelEvery !== 0) return "";
        if (i !== n - 1 && n - 1 - i < Math.ceil(labelEvery * 0.5)) return "";
        return `<text x="${xAt(i).toFixed(1)}" y="${H - 10}" text-anchor="middle" font-size="11" fill="#7b8391">${escapeHtml(shortDate(d))}</text>`;
      })
      .join("");

    const barsSvg = dates
      .map((d, i) => {
        const info = byDate[d];
        const x = xAt(i) - barW / 2;
        const isSel = d === selectedDate;
        let selBg = "";
        if (isSel) {
          selBg = `<rect x="${(pad.left + slotW * i + 1).toFixed(1)}" y="${pad.top}" width="${Math.max(4, slotW - 2).toFixed(1)}" height="${plotH}" rx="6" fill="rgba(232,84,32,0.09)" stroke="rgba(232,84,32,0.4)" stroke-width="1" />`;
        }
        if (!info || !info.total_min) {
          return `${selBg}<rect x="${x.toFixed(1)}" y="${(pad.top + plotH - 3).toFixed(1)}" width="${barW.toFixed(1)}" height="3" rx="1.5" fill="rgba(21,24,30,0.09)" />`;
        }

        if (info.detail_status === "missing" || (!info.main && !(info.naps && info.naps.length))) {
          const y = yAt(info.total_min);
          return `${selBg}<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${barW.toFixed(1)}" height="${Math.max(2, pad.top + plotH - y).toFixed(1)}" rx="3" fill="url(#hbLegacyHatch)" stroke="#94a3b8" stroke-width="0.8" />`;
        }

        const main = info.main || {};
        const deep = Number(main.deep_min) || 0;
        const light = Number(main.light_min) || 0;
        const rem = Number(main.rem_min) || 0;
        const nap = Number(info.nap_min) || 0;
        const staged = deep + light + rem + nap;
        const otherMin = Math.max(0, Number(info.total_min) - staged);

        const segs = [
          { v: deep, c: "#3f51b5" },
          { v: light, c: "#8ea0ff" },
          { v: rem, c: "#0ea5a4" },
          { v: otherMin, c: "#94a3b8" },
          { v: nap, c: "#d97706" },
        ];
        let acc = 0;
        const stacks = segs
          .filter((s) => s.v > 0)
          .map((s) => {
            const yb = yAt(acc);
            const yt = yAt(acc + s.v);
            acc += s.v;
            return `<rect x="${x.toFixed(1)}" y="${yt.toFixed(1)}" width="${barW.toFixed(1)}" height="${Math.max(1.8, yb - yt).toFixed(1)}" rx="1.5" fill="${s.c}" />`;
          })
          .join("");
        return selBg + stacks;
      })
      .join("");

    const zones = dates
      .map((d, i) => {
        const zx = pad.left + slotW * i;
        return `<rect class="hb-sleep-zone" data-date="${escapeHtml(d)}" data-idx="${i}" x="${zx.toFixed(1)}" y="${pad.top}" width="${slotW.toFixed(1)}" height="${plotH}" fill="transparent" style="cursor:pointer" />`;
      })
      .join("");

    container.innerHTML = `
      <svg class="chart-svg" viewBox="0 0 ${W} ${H}" role="img" aria-label="睡眠结构柱状图">
        <defs>
          <pattern id="hbLegacyHatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <rect width="6" height="6" fill="#e2e8f0" />
            <line x1="0" y1="0" x2="0" y2="6" stroke="#94a3b8" stroke-width="2" />
          </pattern>
        </defs>
        ${gridSvg}
        ${barsSvg}
        ${refSvg}
        ${xLabels}
        ${zones}
      </svg>
      <div class="chart-tooltip"></div>
    `;

    const svgEl = container.querySelector("svg");
    const tip = container.querySelector(".chart-tooltip");

    container.querySelectorAll(".hb-sleep-zone").forEach((z) => {
      z.addEventListener("mouseenter", () => {
        const idx = Number(z.dataset.idx);
        const d = dates[idx];
        const info = byDate[d];
        let html = `<div class="chart-tt-date"><span>${escapeHtml(d)}</span><span>${escapeHtml(weekdayLabel(d))}</span></div>`;
        if (!info) {
          html += `<div class="chart-tt-row"><span>状态</span><strong>无睡眠记录</strong></div>`;
        } else {
          html += `<div class="chart-tt-row"><span>当日合计</span><strong>${fmtMin(info.total_min)}</strong></div>`;
          if (info.main) {
            html += `<div class="chart-tt-row"><span><i class="chart-tt-dot" style="background:#3f51b5"></i>主睡眠</span><strong>${fmtMin(info.main.asleep_min)}</strong></div>`;
          }
          if (info.nap_min) {
            html += `<div class="chart-tt-row"><span><i class="chart-tt-dot" style="background:#d97706"></i>小睡 (${(info.naps || []).length}次)</span><strong>${fmtMin(info.nap_min)}</strong></div>`;
          }
          if (info.detail_status === "missing") {
            html += `<div class="chart-tt-row"><span>明细</span><strong>仅总量（未分段）</strong></div>`;
          }
        }
        tip.innerHTML = html;
        const rect = svgEl.getBoundingClientRect();
        const px = (xAt(idx) / W) * rect.width;
        const py = info && info.total_min ? (yAt(info.total_min) / H) * rect.height : rect.height * 0.55;
        tip.style.left = `${Math.max(96, Math.min(rect.width - 96, px))}px`;
        tip.style.top = `${Math.max(60, py)}px`;
        tip.classList.add("visible");
      });

      z.addEventListener("click", () => {
        if (typeof onSelect === "function") onSelect(z.dataset.date);
      });
    });

    svgEl.addEventListener("mouseleave", () => tip.classList.remove("visible"));
  }

  global.HBCharts = {
    sparkline,
    sleepRing,
    trendChart,
    sleepLabChart,
    fmtMin,
    fmtNum,
    weekdayLabel,
    escapeHtml,
  };
})(window);
