"""Tests for the core logic, using tiny hand-made tables so every number can be checked by eye."""
from datetime import date, time

import pandas as pd
import pytest

from app import analysis


def utc(text: str) -> pd.Timestamp:
    return pd.Timestamp(text, tz="UTC")


def make_forecasts(rows):
    """rows: (publish_time, target_time, forecast_mw)"""
    return pd.DataFrame(rows, columns=["publish_time", "target_time", "forecast"]).assign(
        publish_time=lambda t: pd.to_datetime(t["publish_time"], utc=True),
        target_time=lambda t: pd.to_datetime(t["target_time"], utc=True),
    )


def test_cutoff_is_day_before_at_given_uk_time():
    # In January UK time equals UTC
    assert analysis.cutoff_time_utc(date(2026, 1, 10), time(9, 0)) == utc("2026-01-09 09:00")


def test_cutoff_in_summer_uses_british_summer_time():
    # In July UK is UTC+1, so 09:00 UK is 08:00 UTC
    assert analysis.cutoff_time_utc(date(2026, 7, 10), time(9, 0)) == utc("2026-07-09 08:00")


def test_picks_newest_forecast_published_before_cutoff():
    forecasts = make_forecasts([
        ("2026-01-09 04:30", "2026-01-10 12:00", 100),  # old run
        ("2026-01-09 07:30", "2026-01-10 12:00", 200),  # newest run before 09:00  -> expected
        ("2026-01-09 09:30", "2026-01-10 12:00", 300),  # after the cutoff, must be ignored
    ])
    result = analysis.forecast_available_at_cutoff(forecasts, date(2026, 1, 10), time(9, 0))
    assert result["forecast"].tolist() == [200]


def test_forecast_published_exactly_at_cutoff_is_allowed():
    forecasts = make_forecasts([("2026-01-09 09:00", "2026-01-10 12:00", 150)])
    result = analysis.forecast_available_at_cutoff(forecasts, date(2026, 1, 10), time(9, 0))
    assert len(result) == 1


def test_returns_empty_when_nothing_published_before_cutoff():
    forecasts = make_forecasts([("2026-01-09 09:30", "2026-01-10 12:00", 300)])
    result = analysis.forecast_available_at_cutoff(forecasts, date(2026, 1, 10), time(9, 0))
    assert result.empty


def test_only_hours_of_the_delivery_day_are_returned():
    forecasts = make_forecasts([
        ("2026-01-09 07:30", "2026-01-09 23:00", 1),  # day before delivery
        ("2026-01-09 07:30", "2026-01-10 00:00", 2),  # delivery day
        ("2026-01-09 07:30", "2026-01-11 00:00", 3),  # day after
    ])
    result = analysis.forecast_available_at_cutoff(forecasts, date(2026, 1, 10), time(9, 0))
    assert result["forecast"].tolist() == [2]


def test_summarize_errors_known_numbers():
    # errors (forecast - actual): +100, -300  ->  MAE 200, bias -100, RMSE sqrt((10000+90000)/2)
    comparison = pd.DataFrame({"actual": [1000.0, 1000.0], "error": [100.0, -300.0]})
    summary = analysis.summarize_errors(comparison)
    assert summary["hours_compared"] == 2
    assert summary["mae"] == 200
    assert summary["bias"] == -100
    assert summary["rmse"] == pytest.approx(223.607, rel=1e-4)
    assert summary["mape_percent"] == pytest.approx(20.0)


def test_summarize_ignores_hours_without_actuals():
    comparison = pd.DataFrame({"actual": [1000.0, None], "error": [100.0, None]})
    assert analysis.summarize_errors(comparison)["hours_compared"] == 1


def test_to_json_safe_turns_nan_into_none():
    assert analysis.to_json_safe(float("nan")) is None
    assert analysis.to_json_safe(5.0) == 5.0
