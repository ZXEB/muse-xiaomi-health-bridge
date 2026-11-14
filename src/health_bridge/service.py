from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from typing import Any, Iterable

from .config import Settings
from .db import Database
from .source import MiFitnessSource
from .summary import build_summary, to_markdown
from .sync import run_sync

DOMAIN_FIELDS: dict[str, tuple[str, ...]] = {
    "steps": ("date", "steps", "distance_m", "step_calories"),
    "sleep": (
        "date",
        "sleep_total_min",
        "sleep_deep_min",
        "sleep_light_min",
        "sleep_rem_min",
        "sleep_awake_min",
        "sleep_start",
        "sleep_end",
    ),
    "heart-rate": ("date", "hr_avg", "hr_min", "hr_max", "hr_resting"),
    "spo2": ("date", "spo2_avg", "spo2_min", "spo2_max"),
    "stress": (
        "date",
        "stress_avg",
        "stress_max",
        "stress_relaxed_min",
        "stress_mild_min",
        "stress_moderate_min",
        "stress_severe_min",
    ),
    "weight": ("date", "weight_kg", "weight_bmi"),
    "activity": ("date", "activity_count", "activity_min"),
    "calories": ("date", "resting_kcal", "active_kcal", "intake_kcal", "total_kcal"),
}

MAX_RANGE_DAYS = 92


class HealthService:
    def __init__(
        self,
        settings: Settings,
        db: Database | None = None,
        source: MiFitnessSource | None = None,
    ):
        self.settings = settings
        self.db = db or Database(settings.db_path)
        self.source = source or MiFitnessSource(settings)

    # -- helpers --------------------------------------------------------
    def today(self) -> date:
        return datetime.now(self.settings.tzinfo).date()

    def parse_range(
        self,
        start: str | None,
        end: str | None,
        default_days: int = 7,
        max_days: int = MAX_RANGE_DAYS,
    ) -> tuple[date, date]:
        end_date = date.fromisoformat(end) if end else self.today()
        start_date = date.fromisoformat(start) if start else end_date - timedelta(days=default_days - 1)
        if start_date > end_date:
            raise ValueError("start must be on or before end")
        if (end_date - start_date).days + 1 > max_days:
            raise ValueError(f"range is longer than {max_days} days; use smaller windows")
        return start_date, end_date

    def _cap(self, rows: list[dict[str, Any]], notes: list[str]) -> list[dict[str, Any]]:
        if len(rows) > self.settings.max_rows:
            notes.append(
                f"Only the most recent {self.settings.max_rows} of {len(rows)} rows are shown."
            )
            rows = rows[-self.settings.max_rows :]
        while rows:
            payload = json.dumps(rows, ensure_ascii=False, default=str)
            if len(payload.encode("utf-8")) <= self.settings.max_bytes or len(rows) == 1:
                break
            rows = rows[: len(rows) // 2]
            notes.append("Response trimmed to fit the size limit.")
        return rows

    # -- reads ----------------------------------------------------------
    def status(self) -> dict[str, Any]:
        states = self.db.sync_states()
        counts = self.db.counts()
        last_sync = max((s.get("last_synced_at") or "" for s in states.values()), default="")
        error_text = " ".join((s.get("last_error") or "") for s in states.values()).lower()
        session_expired = any(
            marker in error_text
            for marker in ("no usable session", "session expired", "mifit login")
        )
        return {
            "ok": True,
            "timezone": self.settings.tz,
            "today": self.today().isoformat(),
            "latest_data_date": self.db.latest_date(),
            "last_sync_at": last_sync or None,
            "session_expired": session_expired,
            "counts": counts,
            "domains": states,
        }

    def metrics(self, start: str | None, end: str | None, fields: str | None = None):
        start_date, end_date = self.parse_range(start, end)
        rows = self.db.metrics_between(start_date.isoformat(), end_date.isoformat())
        notes: list[str] = []
        if fields:
            wanted = [f.strip() for f in fields.split(",") if f.strip()]
            if "date" not in wanted:
                wanted = ["date", *wanted]
            rows = [{k: row.get(k) for k in wanted} for row in rows]
        rows = self._cap(rows, notes)
        return {
            "timezone": self.settings.tz,
            "from": start_date.isoformat(),
            "to": end_date.isoformat(),
            "fields": fields,
            "rows": rows,
            "notes": notes,
        }

    def domain(self, name: str, start: str | None, end: str | None) -> dict[str, Any]:
        if name not in DOMAIN_FIELDS:
            raise ValueError(f"unknown domain {name!r}")
        start_date, end_date = self.parse_range(start, end)
        notes: list[str] = []
        rows = self.db.metrics_between(start_date.isoformat(), end_date.isoformat())
        fields = DOMAIN_FIELDS[name]
        rows = [{k: row.get(k) for k in fields} for row in rows]
        rows = self._cap(rows, notes)
        return {
            "timezone": self.settings.tz,
            "domain": name,
            "from": start_date.isoformat(),
            "to": end_date.isoformat(),
            "rows": rows,
            "notes": notes,
        }

    def workouts(self, start: str | None, end: str | None) -> dict[str, Any]:
        start_date, end_date = self.parse_range(start, end)
        notes: list[str] = []
        rows = self.db.workouts_between(start_date.isoformat(), end_date.isoformat())
        rows = self._cap(rows, notes)
        return {
            "timezone": self.settings.tz,
            "from": start_date.isoformat(),
            "to": end_date.isoformat(),
            "rows": rows,
            "notes": notes,
        }

    def summary(self, days: int = 7) -> dict[str, Any]:
        days = max(1, min(int(days), MAX_RANGE_DAYS))
        end_date = self.today()
        start_date = end_date - timedelta(days=days - 1)
        metrics = self.db.metrics_between(start_date.isoformat(), end_date.isoformat())
        workouts = self.db.workouts_between(start_date.isoformat(), end_date.isoformat())
        result = build_summary(metrics, workouts, start_date, end_date, self.settings.tz)
        result["markdown"] = to_markdown(result)
        if not metrics:
            result["notes"].append(
                "No data stored yet. Run a sync, or check /v1/status for login issues."
            )
        return result

    # -- writes ---------------------------------------------------------
    def sync(self, days: int = 7) -> dict[str, Any]:
        days = max(1, min(int(days), 366))
        return run_sync(self.settings, self.db, self.source, days)
