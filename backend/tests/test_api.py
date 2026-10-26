"""End-to-end API tests against the saved January 2026 data."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_config_has_date_range():
    body = client.get("/api/config").json()
    assert body["first_delivery_date"] == "2026-01-02"
    assert body["last_delivery_date"] == "2026-01-31"


def test_forecast_returns_24_hours_published_before_cutoff():
    body = client.get("/api/forecast", params={"delivery_date": "2026-01-15", "cutoff": "09:00"}).json()
    assert len(body["hours"]) == 24
    assert body["publish_time"] <= body["cutoff_utc"]


def test_forecast_outside_january_is_404():
    assert client.get("/api/forecast", params={"delivery_date": "2026-03-01"}).status_code == 404


def test_bad_cutoff_is_422():
    response = client.get("/api/forecast", params={"delivery_date": "2026-01-15", "cutoff": "banana"})
    assert response.status_code == 422


def test_accuracy_covers_every_delivery_hour():
    body = client.get("/api/accuracy").json()
    assert body["summary"]["hours_compared"] == 30 * 24
    assert len(body["by_hour_of_day"]) == 24
    assert len(body["by_delivery_day"]) == 30
    assert body["summary"]["mae"] > 0
