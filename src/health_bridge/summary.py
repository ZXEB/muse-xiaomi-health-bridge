from __future__ import annotations

from datetime import date, timedelta
from typing import Any

WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def _fmt_min(minutes: float | int | None) -> str | None:
    if minutes is None:
        return None
    total = int(round(float(minutes)))
    return f"{total // 60}h{total % 60:02d}m"


def _avg(values: list[float]) -> float | None:
    clean = [v for v in values if v is not None]
    return round(sum(clean) / len(clean), 1) if clean else None


def build_summary(
    metrics: list[dict[str, Any]],
    workouts: list[dict[str, Any]],
    start: date,
    end: date,
    timezone_name: str,
) -> dict[str, Any]:
    days_with_steps = [m["steps"] for m in metrics if m.get("steps") is not None]
    sleep_values = [m["sleep_total_min"] for m in metrics if m.get("sleep_total_min") is not None]
    deep_values = [m["sleep_deep_min"] for m in metrics if m.get("sleep_deep_min") is not None]
    rem_values = [m["sleep_rem_min"] for m in metrics if m.get("sleep_rem_min") is not None]
    resting_values = [m["hr_resting"] for m in metrics if m.get("hr_resting") is not None]
    spo2_values = [m["spo2_avg"] for m in metrics if m.get("spo2_avg") is not None]
    stress_values = [m["stress_avg"] for m in metrics if m.get("stress_avg") is not None]

    best_steps = max(metrics, key=lambda m: m.get("steps") or -1, default=None)
    latest_sleep = None
    for row in reversed(metrics):
        if row.get("sleep_total_min") is not None:
            latest_sleep = row
            break
    latest_weight = None
    for row in reversed(metrics):
        if row.get("weight_kg") is not None:
            latest_weight = row
            break

    overview: dict[str, Any] = {
        "steps_total": sum(days_with_steps) if days_with_steps else None,
        "steps_avg": _avg(days_with_steps),
        "steps_best": (
            {"date": best_steps["date"], "steps": best_steps["steps"]}
            if best_steps and best_steps.get("steps") is not None
            else None
        ),
        "sleep_avg_min": _avg(sleep_values),
        "sleep_deep_avg_min": _avg(deep_values),
        "sleep_rem_avg_min": _avg(rem_values),
        "sleep_latest": (
            {
                "date": latest_sleep["date"],
                "asleep_min": latest_sleep["sleep_total_min"],
                "start": latest_sleep.get("sleep_start"),
                "end": latest_sleep.get("sleep_end"),
            }
            if latest_sleep
            else None
        ),
        "resting_hr_avg": _avg(resting_values),
        "resting_hr_min": min(resting_values) if resting_values else None,
        "resting_hr_max": max(resting_values) if resting_values else None,
        "spo2_avg": _avg(spo2_values),
        "spo2_min": min(spo2_values) if spo2_values else None,
        "stress_avg": _avg(stress_values),
        "weight_latest": (
            {"date": latest_weight["date"], "weight_kg": latest_weight["weight_kg"]}
            if latest_weight
            else None
        ),
        "workout_count": len(workouts),
        "workout_distance_m": round(
            sum(w.get("distance_m") or 0 for w in workouts), 1
        )
        if workouts
        else 0,
    }

    return {
        "timezone": timezone_name,
        "from": start.isoformat(),
        "to": end.isoformat(),
        "days": len(metrics),
        "overview": overview,
        "daily": metrics,
        "workouts": workouts,
        "notes": [],
    }


def to_markdown(summary: dict[str, Any]) -> str:
    o = summary["overview"]
    lines = [
        f"# 小米运动健康摘要（{summary['from']} ~ {summary['to']}，{summary['timezone']}）",
        "",
        "## 概览",
    ]

    if o["steps_avg"] is not None:
        best = o.get("steps_best")
        best_txt = f"，最高 {best['date']}（{best['steps']:,} 步）" if best else ""
        lines.append(
            f"- 步数：日均 {o['steps_avg']:,.0f}，合计 {o['steps_total']:,} 步{best_txt}"
        )
    if o["sleep_avg_min"] is not None:
        parts = [f"日均 {_fmt_min(o['sleep_avg_min'])}"]
        if o["sleep_deep_avg_min"] is not None:
            parts.append(f"深睡 {_fmt_min(o['sleep_deep_avg_min'])}")
        if o["sleep_rem_avg_min"] is not None:
            parts.append(f"REM {_fmt_min(o['sleep_rem_avg_min'])}")
        latest = o.get("sleep_latest")
        if latest:
            parts.append(
                f"最近一晚 {latest['date']} 睡 {_fmt_min(latest['asleep_min'])}"
                + (f"（{latest['start']} → {latest['end']}）" if latest.get("start") else "")
            )
        lines.append("- 睡眠：" + "；".join(parts))
    if o["resting_hr_avg"] is not None:
        lines.append(
            f"- 静息心率：均值 {o['resting_hr_avg']:.0f} bpm"
            f"（{o['resting_hr_min']:.0f}–{o['resting_hr_max']:.0f}）"
        )
    if o["spo2_avg"] is not None:
        lines.append(f"- 血氧：日均 {o['spo2_avg']:.0f}%，最低 {o['spo2_min']:.0f}%")
    if o["stress_avg"] is not None:
        lines.append(f"- 压力：日均 {o['stress_avg']:.0f}")
    if o["weight_latest"]:
        lines.append(
            f"- 体重：{o['weight_latest']['weight_kg']:.1f} kg（{o['weight_latest']['date']}）"
        )
    if o["workout_count"]:
        lines.append(
            f"- 运动：{o['workout_count']} 次，合计 {o['workout_distance_m'] / 1000:.1f} km"
        )

    if summary["daily"]:
        lines += ["", "## 每日", "| 日期 | 步数 | 睡眠 | 静息心率 | 血氧 | 压力 |", "| --- | --- | --- | --- | --- | --- |"]
        for row in summary["daily"]:
            d = date.fromisoformat(row["date"])
            label = f"{row['date']} {WEEKDAYS[d.weekday()]}"
            lines.append(
                "| "
                + " | ".join(
                    [
                        label,
                        f"{row['steps']:,}" if row.get("steps") is not None else "-",
                        _fmt_min(row.get("sleep_total_min")) or "-",
                        f"{row['hr_resting']:.0f}" if row.get("hr_resting") is not None else "-",
                        f"{row['spo2_avg']:.0f}%" if row.get("spo2_avg") is not None else "-",
                        f"{row['stress_avg']:.0f}" if row.get("stress_avg") is not None else "-",
                    ]
                )
                + " |"
            )

    if summary["workouts"]:
        lines += ["", "## 运动"]
        for w in summary["workouts"]:
            km = f"{w['distance_m'] / 1000:.2f} km " if w.get("distance_m") else ""
            kcal = f"{w['active_kcal']:.0f} kcal" if w.get("active_kcal") else ""
            hr = f"，平均心率 {w['avg_hr']:.0f}" if w.get("avg_hr") else ""
            lines.append(
                f"- {w.get('start_time') or w.get('date')} {w.get('sport')}：{km}"
                f"{(w.get('duration_s') or 0) // 60} 分钟 {kcal}{hr}"
            )

    return "\n".join(lines) + "\n"
