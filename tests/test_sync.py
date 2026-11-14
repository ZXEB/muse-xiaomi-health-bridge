from __future__ import annotations

from datetime import date

from health_bridge.sync import compute_next_run, iter_chunks, read_schedule, run_sync


def test_read_schedule_defaults(service):
    schedule = read_schedule(service.db, service.settings)
    assert schedule == {"interval_minutes": 0, "hour": 4, "minute": 30, "days": 7}


def test_compute_next_run_daily():
    from datetime import datetime as dt

    schedule = {"interval_minutes": 0, "hour": 4, "minute": 30, "days": 7}
    now = dt(2026, 11, 14, 3, 0)
    assert compute_next_run(schedule, now, None) == dt(2026, 11, 14, 4, 30)
    later = dt(2026, 11, 14, 5, 0)
    assert compute_next_run(schedule, later, None) == dt(2026, 11, 15, 4, 30)


def test_compute_next_run_interval():
    from datetime import datetime as dt, timedelta as td

    schedule = {"interval_minutes": 30, "hour": 4, "minute": 30, "days": 7}
    now = dt(2026, 11, 14, 8, 0)
    last = dt(2026, 11, 14, 7, 50)
    assert compute_next_run(schedule, now, last) == last + td(minutes=30)


def test_iter_chunks_covers_range():
    chunks = list(iter_chunks(date(2026, 1, 1), date(2026, 3, 31), size=31))
    assert chunks[0][0] == date(2026, 1, 1)
    assert chunks[-1][1] == date(2026, 3, 31)
    assert sum((end - start).days + 1 for start, end in chunks) == 90


def test_run_sync_writes_rows_and_state(service):
    today = date(2026, 11, 14)
    result = run_sync(service.settings, service.db, service.source, 2, today=today)

    assert result["errors"] == []
    assert result["from"] == "2026-11-13"
    rows = service.db.metrics_between("2026-11-13", "2026-11-14")
    assert rows
    assert rows[0]["steps"] == 9000
    assert rows[0]["sleep_total_min"] == 330
    # The fake client anchors its workout at a fixed epoch, 2025-11-07 in +08:00.
    assert service.db.workouts_between("2025-11-07", "2025-11-07")
    assert service.db.sync_states()["steps"]["last_date"] == "2026-11-14"


def test_run_sync_reports_domain_errors(service):
    class BrokenClient(type(service.source._client)):
        pass

    def boom(start, end):
        raise RuntimeError("cloud said no")

    broken = service.source
    broken._client = BrokenClient()
    broken._client.steps = boom  # type: ignore[method-assign]

    result = run_sync(service.settings, service.db, broken, 1, today=date(2026, 11, 14))
    assert any("steps" in error for error in result["errors"])
    assert service.db.sync_states()["steps"]["last_error"].startswith("steps")
