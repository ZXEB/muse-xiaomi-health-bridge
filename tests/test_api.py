from __future__ import annotations

from datetime import timedelta

from fastapi.testclient import TestClient

from tests.conftest import TOKEN

HEADERS = {"Authorization": f"Bearer {TOKEN}"}


def _seed(service):
    today = service.today()
    yesterday = today - timedelta(days=1)
    service.db.upsert_daily(
        [
            {
                "date": yesterday.isoformat(),
                "steps": 8000,
                "distance_m": 5600.0,
                "sleep_total_min": 420,
                "sleep_deep_min": 90,
                "sleep_light_min": 260,
                "sleep_rem_min": 70,
                "sleep_awake_min": 20,
                "hr_resting": 56.0,
                "hr_avg": 71.0,
                "spo2_avg": 97.0,
                "spo2_min": 94.0,
                "stress_avg": 30.0,
                "weight_kg": 68.5,
            },
            {
                "date": today.isoformat(),
                "steps": 12000,
                "distance_m": 8400.0,
                "sleep_total_min": 390,
                "hr_resting": 58.0,
                "spo2_avg": 96.5,
                "stress_avg": 33.0,
            },
        ]
    )
    service.db.upsert_workouts(
        [
            {
                "id": "w1",
                "date": yesterday.isoformat(),
                "start_time": f"{yesterday.isoformat()}T18:00:00+08:00",
                "end_time": f"{yesterday.isoformat()}T18:30:00+08:00",
                "sport": "Outdoor run",
                "duration_s": 1800,
                "distance_m": 5000.0,
                "active_kcal": 320.0,
                "total_kcal": 360.0,
                "avg_hr": 152.0,
                "max_hr": 171.0,
                "steps": 5200,
            }
        ]
    )


def test_summary_json(service, rest_app):
    _seed(service)
    with TestClient(rest_app) as client:
        response = client.get("/v1/summary?days=7", headers=HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert body["days"] == 2
    assert body["overview"]["steps_total"] == 20000
    assert body["overview"]["workout_count"] == 1
    assert "markdown" in body


def test_summary_markdown(service, rest_app):
    _seed(service)
    with TestClient(rest_app) as client:
        response = client.get("/v1/summary?days=7&format=md", headers=HEADERS)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert "步数" in response.text


def test_domain_endpoints(service, rest_app):
    _seed(service)
    with TestClient(rest_app) as client:
        for domain in ("sleep", "steps", "heart-rate", "spo2", "stress", "weight"):
            response = client.get(f"/v1/{domain}", headers=HEADERS)
            assert response.status_code == 200, domain
            assert response.json()["rows"], domain
        workouts = client.get("/v1/workouts", headers=HEADERS)
    assert workouts.status_code == 200
    assert len(workouts.json()["rows"]) == 1


def test_metrics_fields_filter(service, rest_app):
    _seed(service)
    with TestClient(rest_app) as client:
        response = client.get("/v1/metrics?fields=steps,steps", headers=HEADERS)
    assert response.status_code == 200
    row = response.json()["rows"][0]
    assert set(row.keys()) == {"date", "steps"}


def test_range_too_long_is_rejected(service, rest_app):
    with TestClient(rest_app) as client:
        response = client.get(
            "/v1/metrics?from=2025-01-01&to=2025-12-31", headers=HEADERS
        )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "bad_request"


def test_unknown_domain_is_404_or_405(rest_app):
    with TestClient(rest_app) as client:
        response = client.get("/v1/nope", headers=HEADERS)
    assert response.status_code in (404, 405)
