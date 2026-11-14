from __future__ import annotations

from datetime import date

from health_bridge.summary import build_summary, to_markdown


def test_markdown_contains_overview():
    metrics = [
        {
            "date": "2026-11-13",
            "steps": 9000,
            "sleep_total_min": 420,
            "sleep_deep_min": 80,
            "hr_resting": 57.0,
            "spo2_avg": 97.0,
            "stress_avg": 30.0,
        },
        {
            "date": "2026-11-14",
            "steps": 12000,
            "sleep_total_min": 390,
            "hr_resting": 59.0,
            "spo2_avg": 96.0,
            "stress_avg": 34.0,
        },
    ]
    workouts = [
        {
            "id": "w1",
            "date": "2026-11-13",
            "start_time": "2026-11-13T18:00:00+08:00",
            "sport": "Outdoor run",
            "duration_s": 1800,
            "distance_m": 5000.0,
            "active_kcal": 320.0,
            "avg_hr": 152.0,
        }
    ]
    summary = build_summary(metrics, workouts, date(2026, 11, 13), date(2026, 11, 14), "Asia/Shanghai")
    assert summary["overview"]["steps_total"] == 21000
    assert summary["overview"]["steps_avg"] == 10500

    text = to_markdown(summary)
    assert "步数" in text
    assert "睡眠" in text
    assert "7h00m" in text  # 420 minutes
    assert "Outdoor run" in text


def test_empty_summary_renders_without_daily_table():
    summary = build_summary([], [], date(2026, 11, 13), date(2026, 11, 14), "Asia/Shanghai")
    text = to_markdown(summary)
    assert "## 每日" not in text
    assert "小米运动健康摘要" in text
