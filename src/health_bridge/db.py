from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Sequence

DAILY_COLUMNS = [
    "date",
    "steps",
    "distance_m",
    "step_calories",
    "active_kcal",
    "resting_kcal",
    "intake_kcal",
    "total_kcal",
    "hr_avg",
    "hr_min",
    "hr_max",
    "hr_resting",
    "sleep_total_min",
    "sleep_deep_min",
    "sleep_light_min",
    "sleep_rem_min",
    "sleep_awake_min",
    "sleep_start",
    "sleep_end",
    "spo2_avg",
    "spo2_min",
    "spo2_max",
    "stress_avg",
    "stress_max",
    "stress_relaxed_min",
    "stress_mild_min",
    "stress_moderate_min",
    "stress_severe_min",
    "activity_count",
    "activity_min",
    "weight_kg",
    "weight_bmi",
    "raw_json",
    "updated_at",
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS daily_metrics (
    date TEXT PRIMARY KEY,
    steps INTEGER,
    distance_m REAL,
    step_calories REAL,
    active_kcal REAL,
    resting_kcal REAL,
    intake_kcal REAL,
    total_kcal REAL,
    hr_avg REAL,
    hr_min REAL,
    hr_max REAL,
    hr_resting REAL,
    sleep_total_min INTEGER,
    sleep_deep_min INTEGER,
    sleep_light_min INTEGER,
    sleep_rem_min INTEGER,
    sleep_awake_min INTEGER,
    sleep_start TEXT,
    sleep_end TEXT,
    spo2_avg REAL,
    spo2_min REAL,
    spo2_max REAL,
    stress_avg REAL,
    stress_max REAL,
    stress_relaxed_min INTEGER,
    stress_mild_min INTEGER,
    stress_moderate_min INTEGER,
    stress_severe_min INTEGER,
    activity_count INTEGER,
    activity_min INTEGER,
    weight_kg REAL,
    weight_bmi REAL,
    raw_json TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS workouts (
    id TEXT PRIMARY KEY,
    date TEXT,
    start_time TEXT,
    end_time TEXT,
    sport TEXT,
    duration_s INTEGER,
    distance_m REAL,
    active_kcal REAL,
    total_kcal REAL,
    avg_hr REAL,
    max_hr REAL,
    steps INTEGER,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS sync_state (
    domain TEXT PRIMARY KEY,
    last_synced_at TEXT,
    last_date TEXT,
    last_error TEXT
);

CREATE TABLE IF NOT EXISTS admin_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    at TEXT NOT NULL,
    action TEXT NOT NULL,
    detail TEXT,
    ip TEXT
);

CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


class Database:
    def __init__(self, path: str | Path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")
            conn.execute("PRAGMA synchronous=NORMAL")
            yield conn
            conn.commit()
        finally:
            conn.close()

    # -- writes ---------------------------------------------------------
    def upsert_daily(self, rows: Sequence[dict[str, Any]]) -> None:
        if not rows:
            return
        now = datetime.now(timezone.utc).isoformat()
        columns = [c for c in DAILY_COLUMNS if c != "date"]
        placeholders = ", ".join("?" for _ in DAILY_COLUMNS)
        updates = ", ".join(f"{c}=COALESCE(excluded.{c}, daily_metrics.{c})" for c in columns)
        sql = (
            f"INSERT INTO daily_metrics ({', '.join(DAILY_COLUMNS)}) VALUES ({placeholders}) "
            f"ON CONFLICT(date) DO UPDATE SET {updates}"
        )
        with self._connect() as conn:
            for row in rows:
                payload = dict(row)
                if isinstance(payload.get("raw_json"), (dict, list)):
                    payload["raw_json"] = json.dumps(payload["raw_json"], ensure_ascii=False)
                payload["updated_at"] = now
                values = [payload.get(c) for c in DAILY_COLUMNS]
                conn.execute(sql, values)

    def upsert_workouts(self, rows: Sequence[dict[str, Any]]) -> None:
        if not rows:
            return
        now = datetime.now(timezone.utc).isoformat()
        columns = [
            "id",
            "date",
            "start_time",
            "end_time",
            "sport",
            "duration_s",
            "distance_m",
            "active_kcal",
            "total_kcal",
            "avg_hr",
            "max_hr",
            "steps",
            "updated_at",
        ]
        placeholders = ", ".join("?" for _ in columns)
        updates = ", ".join(f"{c}=excluded.{c}" for c in columns if c not in ("id", "updated_at"))
        sql = (
            f"INSERT INTO workouts ({', '.join(columns)}) VALUES ({placeholders}) "
            f"ON CONFLICT(id) DO UPDATE SET {updates}, updated_at=excluded.updated_at"
        )
        with self._connect() as conn:
            for row in rows:
                payload = dict(row)
                payload["updated_at"] = now
                conn.execute(sql, [payload.get(c) for c in columns])

    def set_sync_state(
        self,
        domain: str,
        last_date: str | None,
        error: str | None,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO sync_state(domain, last_synced_at, last_date, last_error) "
                "VALUES(?,?,?,?) ON CONFLICT(domain) DO UPDATE SET "
                "last_synced_at=excluded.last_synced_at, last_date=excluded.last_date, "
                "last_error=excluded.last_error",
                (domain, now, last_date, error),
            )

    # -- reads ----------------------------------------------------------
    def metrics_between(self, start: str, end: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT * FROM daily_metrics WHERE date BETWEEN ? AND ? ORDER BY date",
                (start, end),
            )
            return [dict(row) for row in cursor.fetchall()]

    def workouts_between(self, start: str, end: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT * FROM workouts WHERE date BETWEEN ? AND ? ORDER BY start_time",
                (start, end),
            )
            return [dict(row) for row in cursor.fetchall()]

    def latest_date(self) -> str | None:
        with self._connect() as conn:
            row = conn.execute("SELECT MAX(date) AS d FROM daily_metrics").fetchone()
        return row["d"] if row and row["d"] else None

    def earliest_date(self) -> str | None:
        with self._connect() as conn:
            row = conn.execute("SELECT MIN(date) AS d FROM daily_metrics").fetchone()
        return row["d"] if row and row["d"] else None

    def add_audit(self, action: str, detail: str = "", ip: str = "") -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO admin_audit(at, action, detail, ip) VALUES(?,?,?,?)",
                (now, action[:80], detail[:500], ip[:64]),
            )
            conn.execute(
                "DELETE FROM admin_audit WHERE id NOT IN "
                "(SELECT id FROM admin_audit ORDER BY id DESC LIMIT 500)"
            )

    def list_audit(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT * FROM admin_audit ORDER BY id DESC LIMIT ?", (max(1, min(limit, 500)),)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_setting(self, key: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None

    def set_setting(self, key: str, value: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO app_settings(key, value) VALUES(?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )

    def delete_setting(self, key: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM app_settings WHERE key = ?", (key,))

    def sync_states(self) -> dict[str, dict[str, Any]]:
        with self._connect() as conn:
            cursor = conn.execute("SELECT * FROM sync_state")
            return {row["domain"]: dict(row) for row in cursor.fetchall()}

    def counts(self) -> dict[str, int]:
        with self._connect() as conn:
            daily = conn.execute("SELECT COUNT(*) AS n FROM daily_metrics").fetchone()["n"]
            workouts = conn.execute("SELECT COUNT(*) AS n FROM workouts").fetchone()["n"]
        return {"daily_rows": daily, "workout_rows": workouts}
