from __future__ import annotations

from health_bridge.db import Database


def test_upsert_merges_partial_rows(tmp_path):
    db = Database(tmp_path / "health.db")
    db.upsert_daily([{"date": "2026-11-01", "steps": 1000}])
    db.upsert_daily([{"date": "2026-11-01", "sleep_total_min": 400}])

    rows = db.metrics_between("2026-11-01", "2026-11-01")
    assert len(rows) == 1
    assert rows[0]["steps"] == 1000
    assert rows[0]["sleep_total_min"] == 400
    assert rows[0]["updated_at"]


def test_upsert_does_not_blank_missing_values(tmp_path):
    db = Database(tmp_path / "health.db")
    db.upsert_daily([{"date": "2026-11-02", "steps": 5000, "weight_kg": 68.0}])
    db.upsert_daily([{"date": "2026-11-02", "steps": None, "hr_resting": 55.0}])

    row = db.metrics_between("2026-11-02", "2026-11-02")[0]
    assert row["steps"] == 5000
    assert row["weight_kg"] == 68.0
    assert row["hr_resting"] == 55.0


def test_workouts_are_deduplicated(tmp_path):
    db = Database(tmp_path / "health.db")
    base = {
        "id": "w1",
        "date": "2026-11-03",
        "start_time": "2026-11-03T18:00:00+08:00",
        "end_time": "2026-11-03T18:30:00+08:00",
        "sport": "Outdoor run",
        "duration_s": 1800,
        "distance_m": 5000.0,
        "active_kcal": 320.0,
        "total_kcal": 360.0,
        "avg_hr": 152.0,
        "max_hr": 171.0,
        "steps": 5200,
    }
    db.upsert_workouts([base])
    db.upsert_workouts([{**base, "distance_m": 5100.0}])

    rows = db.workouts_between("2026-11-03", "2026-11-03")
    assert len(rows) == 1
    assert rows[0]["distance_m"] == 5100.0


def test_sync_state_roundtrip(tmp_path):
    db = Database(tmp_path / "health.db")
    db.set_sync_state("steps", "2026-11-03", None)
    state = db.sync_states()["steps"]
    assert state["last_date"] == "2026-11-03"
    assert state["last_error"] is None
