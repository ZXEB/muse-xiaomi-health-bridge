from __future__ import annotations

from types import SimpleNamespace

import pytest
from mifit import (
    ActivityDailySummary,
    ConsumptionRecord,
    HeartRateDailySummary,
    MiFit,
    SleepRecord,
    SleepSession,
    Spo2DailySummary,
    StepRecord,
    StressDailySummary,
    UserProfile,
    WeightRecord,
    Workout,
)

from health_bridge.config import Settings
from health_bridge.db import Database
from health_bridge.mcp_server import create_mcp_app
from health_bridge.service import HealthService
from health_bridge.source import MiFitnessSource

TOKEN = "test-token"

EPOCH = 1762473600  # 2025-11-07T00:00:00+08:00


def _session(start_epoch: int = EPOCH, end_epoch: int = EPOCH + 6 * 3600) -> SleepSession:
    return SleepSession(
        start_epoch_s=start_epoch,
        end_epoch_s=end_epoch,
        utc_offset_s=8 * 3600,
        asleep_min=330,
        deep_min=70,
        light_min=210,
        rem_min=50,
        awake_min=30,
        stages=[],
    )


class FakeClient:
    """Mimics the parts of mifit.MiFit that MiFitnessSource uses."""

    def steps(self, start, end):
        return SimpleNamespace(
            records=[StepRecord(date=start, steps=9000, distance_m=6300.0, step_calories=320.0, epoch_s=EPOCH)]
        )

    def consumption(self, start, end):
        return SimpleNamespace(
            records=[
                ConsumptionRecord(
                    date=start,
                    epoch_s=EPOCH,
                    resting_kcal=1500.0,
                    active_kcal=300.0,
                    intake_kcal=2100.0,
                    total_kcal=1800.0,
                )
            ]
        )

    def heart_rate_daily(self, start, end):
        return SimpleNamespace(
            records=[
                HeartRateDailySummary(
                    date=start, epoch_s=EPOCH, avg_bpm=72.0, max_bpm=141.0, min_bpm=52.0, resting_bpm=57.0
                )
            ]
        )

    def sleep(self, start, end):
        return SimpleNamespace(
            records=[
                SleepRecord(
                    date=start,
                    epoch_s=EPOCH,
                    asleep_min=330,
                    deep_min=70,
                    light_min=210,
                    rem_min=50,
                    awake_min=30,
                    avg_hr_bpm=58.0,
                    min_hr_bpm=49.0,
                    max_hr_bpm=71.0,
                    avg_spo2_pct=96.0,
                    min_spo2_pct=93.0,
                    max_spo2_pct=98.0,
                    sessions=[_session()],
                )
            ]
        )

    def spo2_daily(self, start, end):
        return SimpleNamespace(
            records=[
                Spo2DailySummary(date=start, epoch_s=EPOCH, avg_spo2_pct=97.0, min_spo2_pct=93.0, max_spo2_pct=99.0)
            ]
        )

    def stress_daily(self, start, end):
        return SimpleNamespace(
            records=[
                StressDailySummary(
                    date=start,
                    epoch_s=EPOCH,
                    avg_stress_level=32.0,
                    max_stress_level=61.0,
                    min_stress_level=12.0,
                    relaxed_min=300,
                    mild_min=120,
                    moderate_min=40,
                    severe_min=10,
                )
            ]
        )

    def activity_daily(self, start, end):
        return SimpleNamespace(
            records=[ActivityDailySummary(date=start, epoch_s=EPOCH, activity_count=6, activity_min=48, active_kcal=300.0)]
        )

    def weight(self, start, end):
        return SimpleNamespace(records=[WeightRecord(epoch_s=EPOCH, weight_kg=68.4, bmi=22.1)])

    def workouts(self, start, end):
        return SimpleNamespace(
            records=[
                Workout(
                    start_epoch_s=EPOCH + 12 * 3600,
                    end_epoch_s=EPOCH + 12 * 3600 + 1800,
                    utc_offset_s=8 * 3600,
                    sport="Outdoor run",
                    source_sport_code=1,
                    duration_s=1800,
                    distance_m=5000.0,
                    active_kcal=320.0,
                    total_kcal=360.0,
                    avg_hr_bpm=152.0,
                    max_hr_bpm=171.0,
                    steps=5200,
                )
            ]
        )

    def profile(self):
        return SimpleNamespace(
            records=[
                UserProfile(
                    height_cm=175,
                    weight_kg=68.4,
                    step_goal=8000,
                    calorie_goal_kcal=500,
                    activity_goal_min=30,
                )
            ]
        )


def make_settings(tmp_path, token: str = TOKEN, **overrides) -> Settings:
    values = {
        "bridge_token": token,
        "db_path": str(tmp_path / "health.db"),
        "tz": "Asia/Shanghai",
        "min_request_interval": 0.0,
        "rate_limit_per_min": 1000,
    }
    values.update(overrides)
    return Settings(**values)


def make_service(tmp_path, **overrides) -> HealthService:
    settings = make_settings(tmp_path, **overrides)
    db = Database(settings.db_path)
    source = MiFitnessSource(settings, client=FakeClient())
    return HealthService(settings, db=db, source=source)


@pytest.fixture
def service(tmp_path) -> HealthService:
    return make_service(tmp_path)


@pytest.fixture
def rest_app(service):
    from health_bridge.api import create_rest_app

    return create_rest_app(service, token=TOKEN)


@pytest.fixture
def mcp_app(service):
    return create_mcp_app(service, token=TOKEN)


@pytest.fixture(autouse=True)
def _no_mifit_session(monkeypatch):
    # Every test injects a fake client; make accidental real login fail loudly.
    def _boom(*args, **kwargs):
        raise AssertionError("tests must not construct a real MiFit client")

    monkeypatch.setattr(MiFit, "__init__", _boom, raising=True)
