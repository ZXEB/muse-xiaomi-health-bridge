from __future__ import annotations

import threading
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable

from mifit import ApiError, AuthError, MiFit, RenewalError

from .config import Settings


class AuthExpiredError(RuntimeError):
    """The stored mifit session is gone and must be refreshed with `mifit login`."""


class UpstreamError(RuntimeError):
    """The Xiaomi cloud call failed after retries."""


def _local_iso(epoch_s: int | float | None, offset_s: int | None, fallback_tz) -> str | None:
    if epoch_s is None:
        return None
    tz = timezone(timedelta(seconds=offset_s)) if offset_s is not None else fallback_tz
    return datetime.fromtimestamp(float(epoch_s), tz).isoformat(timespec="seconds")


def _date_of(epoch_s: int | float | None, fallback_tz) -> str | None:
    if epoch_s is None:
        return None
    return datetime.fromtimestamp(float(epoch_s), fallback_tz).date().isoformat()


class MiFitnessSource:
    """Thin, polite wrapper around the mifit client.

    One request at a time, with a minimum interval between calls, so the
    Xiaomi cloud is never hammered. `client` can be injected in tests.
    """

    def __init__(self, settings: Settings, client: Any | None = None):
        self.settings = settings
        self._client = client
        self._lock = threading.Lock()
        self._last_call = 0.0

    def _get_client(self):
        if self._client is None:
            try:
                self._client = MiFit(auto_renew=True)
            except AuthError as exc:
                raise AuthExpiredError(
                    "mifit has no usable session; run `docker compose run --rm bridge mifit login`."
                ) from exc
        return self._client

    def _wait_turn(self) -> None:
        with self._lock:
            wait = self.settings.min_request_interval - (time.monotonic() - self._last_call)
            if wait > 0:
                time.sleep(wait)
            self._last_call = time.monotonic()

    def _call(self, method: str, *args: Any) -> Any:
        last_error: Exception | None = None
        for attempt in range(3):
            self._wait_turn()
            try:
                return getattr(self._get_client(), method)(*args)
            except (AuthError, RenewalError) as exc:
                raise AuthExpiredError(
                    "mifit session expired; run `docker compose run --rm bridge mifit login`."
                ) from exc
            except ApiError as exc:
                last_error = exc
            except Exception as exc:  # network errors surface as requests exceptions
                last_error = exc
            time.sleep(min(5.0, 1.5 * (attempt + 1)))
        raise UpstreamError(f"{method} failed after retries: {last_error}")

    # -- daily domains ---------------------------------------------------
    def steps(self, start: str, end: str) -> list[dict[str, Any]]:
        result = self._call("steps", start, end)
        return [
            {
                "date": str(rec.date),
                "steps": rec.steps,
                "distance_m": rec.distance_m,
                "step_calories": rec.step_calories,
            }
            for rec in result.records
        ]

    def consumption(self, start: str, end: str) -> list[dict[str, Any]]:
        result = self._call("consumption", start, end)
        return [
            {
                "date": str(rec.date),
                "resting_kcal": rec.resting_kcal,
                "active_kcal": rec.active_kcal,
                "intake_kcal": rec.intake_kcal,
                "total_kcal": rec.total_kcal,
            }
            for rec in result.records
        ]

    def heart_rate_daily(self, start: str, end: str) -> list[dict[str, Any]]:
        result = self._call("heart_rate_daily", start, end)
        return [
            {
                "date": str(rec.date),
                "hr_avg": rec.avg_bpm,
                "hr_min": rec.min_bpm,
                "hr_max": rec.max_bpm,
                "hr_resting": rec.resting_bpm,
            }
            for rec in result.records
        ]

    def sleep(self, start: str, end: str) -> list[dict[str, Any]]:
        result = self._call("sleep", start, end)
        rows: list[dict[str, Any]] = []
        for rec in result.records:
            starts = [s.start_epoch_s for s in rec.sessions if s.start_epoch_s]
            ends = [s.end_epoch_s for s in rec.sessions if s.end_epoch_s]
            offsets = [s.utc_offset_s for s in rec.sessions if s.utc_offset_s is not None]
            offset = offsets[0] if offsets else None
            sessions: dict[tuple[int, int], dict[str, Any]] = {}
            for session in rec.sessions:
                if session.asleep_min <= 0 or session.end_epoch_s <= session.start_epoch_s:
                    continue
                key = (session.start_epoch_s, session.end_epoch_s)
                sessions.setdefault(key, {
                    "start": _local_iso(session.start_epoch_s, session.utc_offset_s, self.settings.tzinfo),
                    "end": _local_iso(session.end_epoch_s, session.utc_offset_s, self.settings.tzinfo),
                    "asleep_min": session.asleep_min,
                    "deep_min": session.deep_min,
                    "light_min": session.light_min,
                    "rem_min": session.rem_min,
                    "awake_min": session.awake_min,
                })
            rows.append(
                {
                    "date": str(rec.date),
                    "sleep_total_min": rec.asleep_min,
                    "sleep_deep_min": rec.deep_min,
                    "sleep_light_min": rec.light_min,
                    "sleep_rem_min": rec.rem_min,
                    "sleep_awake_min": rec.awake_min,
                    "sleep_start": _local_iso(min(starts) if starts else None, offset, self.settings.tzinfo),
                    "sleep_end": _local_iso(max(ends) if ends else None, offset, self.settings.tzinfo),
                    "sleep_sessions": [sessions[key] for key in sorted(sessions)],
                }
            )
        return rows

    def spo2_daily(self, start: str, end: str) -> list[dict[str, Any]]:
        result = self._call("spo2_daily", start, end)
        return [
            {
                "date": str(rec.date),
                "spo2_avg": rec.avg_spo2_pct,
                "spo2_min": rec.min_spo2_pct,
                "spo2_max": rec.max_spo2_pct,
            }
            for rec in result.records
        ]

    def stress_daily(self, start: str, end: str) -> list[dict[str, Any]]:
        result = self._call("stress_daily", start, end)
        return [
            {
                "date": str(rec.date),
                "stress_avg": rec.avg_stress_level,
                "stress_max": rec.max_stress_level,
                "stress_relaxed_min": rec.relaxed_min,
                "stress_mild_min": rec.mild_min,
                "stress_moderate_min": rec.moderate_min,
                "stress_severe_min": rec.severe_min,
            }
            for rec in result.records
        ]

    def activity_daily(self, start: str, end: str) -> list[dict[str, Any]]:
        result = self._call("activity_daily", start, end)
        return [
            {
                "date": str(rec.date),
                "activity_count": rec.activity_count,
                "activity_min": rec.activity_min,
            }
            for rec in result.records
        ]

    # -- point-ish domains ----------------------------------------------
    def weights(self, start: str, end: str) -> list[dict[str, Any]]:
        result = self._call("weight", start, end)
        latest: dict[str, dict[str, Any]] = {}
        for rec in result.records:
            day = _date_of(rec.epoch_s, self.settings.tzinfo)
            if day is None:
                continue
            latest[day] = {
                "date": day,
                "weight_kg": rec.weight_kg,
                "weight_bmi": rec.bmi,
            }
        return list(latest.values())

    def workouts(self, start: str, end: str) -> list[dict[str, Any]]:
        result = self._call("workouts", start, end)
        rows: list[dict[str, Any]] = []
        for rec in result.records:
            offset = rec.utc_offset_s
            start_iso = _local_iso(rec.start_epoch_s, offset, self.settings.tzinfo)
            rows.append(
                {
                    "id": f"{rec.start_epoch_s}-{rec.source_sport_code or rec.sport}",
                    "date": _date_of(rec.start_epoch_s, self.settings.tzinfo),
                    "start_time": start_iso,
                    "end_time": _local_iso(rec.end_epoch_s, offset, self.settings.tzinfo),
                    "sport": rec.sport,
                    "duration_s": rec.duration_s,
                    "distance_m": rec.distance_m,
                    "active_kcal": rec.active_kcal,
                    "total_kcal": rec.total_kcal,
                    "avg_hr": rec.avg_hr_bpm,
                    "max_hr": rec.max_hr_bpm,
                    "steps": rec.steps,
                }
            )
        return rows

    def profile(self) -> dict[str, Any]:
        result = self._call("profile")
        if not result.records:
            return {}
        rec = result.records[0]
        return {
            "height_cm": rec.height_cm,
            "weight_kg": rec.weight_kg,
            "step_goal": rec.step_goal,
            "calorie_goal_kcal": rec.calorie_goal_kcal,
            "activity_goal_min": rec.activity_goal_min,
        }


DOMAINS: dict[str, Callable[[MiFitnessSource, str, str], list[dict[str, Any]]]] = {
    "steps": MiFitnessSource.steps,
    "consumption": MiFitnessSource.consumption,
    "heart_rate_daily": MiFitnessSource.heart_rate_daily,
    "sleep": MiFitnessSource.sleep,
    "spo2_daily": MiFitnessSource.spo2_daily,
    "stress_daily": MiFitnessSource.stress_daily,
    "activity_daily": MiFitnessSource.activity_daily,
    "weight": MiFitnessSource.weights,
}
