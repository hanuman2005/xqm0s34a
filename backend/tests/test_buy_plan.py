"""Tests for the history rule (no peeking at the future) and the buy plan arithmetic."""
from datetime import date

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app import analysis
from app.main import app


def make_comparison(days_and_errors):
    """One row per (delivery_date, error)."""
    return pd.DataFrame(days_and_errors, columns=["delivery_date", "error"])


def test_history_ignores_the_day_before_and_all_later_days():
    comparison = make_comparison([(date(2026, 1, d), 100.0 * d) for d in range(1, 11)])
    history = analysis.history_known_at_decision(comparison, date(2026, 1, 8))
    # Delivery day 8 Jan -> only days up to 6 Jan are known
    assert history["through_date"] == date(2026, 1, 6)
    assert history["days_used"] == 6


def test_history_needs_a_few_days():
    comparison = make_comparison([(date(2026, 1, 1), 100.0), (date(2026, 1, 2), 100.0)])
    assert analysis.history_known_at_decision(comparison, date(2026, 1, 5)) is None


def test_buy_plan_numbers_without_actuals():
    # 2 hours, forecast 10000 MW, history says forecasts run 1000 too high at worst (P90) and 500 on average
    day = pd.DataFrame({"forecast": [10000.0, 10000.0], "actual": [None, None]})
    history = {"error_p90": 1000.0, "bias": 500.0}
    plan = analysis.build_buy_plan(day, history, demand_mw=15000.0)
    assert plan["safe_wind_avg_mw"] == 9000
    assert plan["expected_wind_avg_mw"] == 9500
    assert plan["buy_raw_mw"] == 5000      # 15000 - 10000
    assert plan["buy_guided_mw"] == 6000   # 15000 - 9000
    assert plan["outcome"] is None


def test_buy_plan_outcome_when_actuals_known():
    # Real wind was only 8000 in both hours.
    day = pd.DataFrame({"forecast": [10000.0, 10000.0], "actual": [8000.0, 8000.0]})
    plan = analysis.build_buy_plan(day, {"error_p90": 1000.0, "bias": 0.0}, demand_mw=15000.0)
    outcome = plan["outcome"]
    # Needed 7000/hour. Raw bought 5000 -> short 2000 x 2 hours. Guided bought 6000 -> short 1000 x 2.
    assert outcome["shortfall_raw_mwh"] == 4000
    assert outcome["shortfall_guided_mwh"] == 2000
    assert outcome["surplus_raw_mwh"] == 0


def test_buy_never_negative_when_wind_exceeds_demand():
    day = pd.DataFrame({"forecast": [20000.0], "actual": [None]})
    plan = analysis.build_buy_plan(day, {"error_p90": 0.0, "bias": 0.0}, demand_mw=15000.0)
    assert plan["buy_raw_mw"] == 0


def test_hourly_order_buys_demand_minus_safe_wind():
    day = pd.DataFrame({
        "target_time": pd.to_datetime(["2026-01-10 01:00", "2026-01-10 00:00"], utc=True),
        "forecast": [12000.0, 10000.0],
    })
    order = analysis.hourly_order(day, {"error_p90": 1000.0}, demand_mw=15000.0)
    assert [row["buy_mw"] for row in order] == [6000, 4000]  # sorted by time: 00:00 then 01:00


client = TestClient(app)


def test_api_returns_plan_with_demand_and_history():
    body = client.get("/api/forecast", params={"delivery_date": "2026-01-20", "demand_mw": 30000}).json()
    assert body["history"]["through_date"] == "2026-01-18"
    assert body["plan"]["buy_guided_mw"] >= body["plan"]["buy_raw_mw"]
    assert len(body["order"]) == 24


def test_api_has_no_history_for_first_day():
    body = client.get("/api/forecast", params={"delivery_date": "2026-01-02", "demand_mw": 30000}).json()
    assert body["history"] is None
    assert body["plan"] is None


def test_api_without_demand_has_history_but_no_plan():
    body = client.get("/api/forecast", params={"delivery_date": "2026-01-20"}).json()
    assert body["history"] is not None
    assert body["plan"] is None
