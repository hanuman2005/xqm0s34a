"""The core logic: which forecast could the buyer see, and how accurate was it?

Vocabulary used in this file:
  delivery day  - the day the electricity is used (day D)
  cutoff        - the moment on day D-1 when the buyer must place the order
  error         - forecast minus actual, in MW. Positive = the forecast was too high.
"""
from datetime import date, datetime, time, timedelta

import numpy as np
import pandas as pd

from .config import FIRST_DELIVERY_DATE, LAST_DELIVERY_DATE, MIN_HISTORY_DAYS, UK_TIMEZONE


# ---------- time helpers ----------

def cutoff_time_utc(delivery_day: date, cutoff: time) -> pd.Timestamp:
    """The buyer's deadline: `cutoff` (UK time) on the day before delivery, as UTC."""
    day_before = delivery_day - timedelta(days=1)
    uk_moment = datetime.combine(day_before, cutoff, tzinfo=UK_TIMEZONE)
    return pd.Timestamp(uk_moment).tz_convert("UTC")


def day_window_utc(first_day: date, last_day: date) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Start (inclusive) and end (exclusive) of the UK days first_day..last_day, as UTC."""
    start = pd.Timestamp(datetime.combine(first_day, time(0, 0), tzinfo=UK_TIMEZONE))
    end = pd.Timestamp(datetime.combine(last_day + timedelta(days=1), time(0, 0), tzinfo=UK_TIMEZONE))
    return start.tz_convert("UTC"), end.tz_convert("UTC")


def all_delivery_days() -> list[date]:
    days = (LAST_DELIVERY_DATE - FIRST_DELIVERY_DATE).days + 1
    return [FIRST_DELIVERY_DATE + timedelta(days=i) for i in range(days)]


# ---------- step 1: pick the forecast the buyer could see ----------

def forecast_available_at_cutoff(forecasts: pd.DataFrame, delivery_day: date, cutoff: time) -> pd.DataFrame:
    """The newest forecast run published on or before the cutoff, for one delivery day.

    Returns one row per hour of the delivery day (empty if nothing was published yet).
    Forecasts published after the cutoff are ignored: the buyer could not have seen them.
    """
    deadline = cutoff_time_utc(delivery_day, cutoff)
    published_in_time = forecasts[forecasts["publish_time"] <= deadline]
    if published_in_time.empty:
        return published_in_time

    newest_run = published_in_time["publish_time"].max()
    day_start, day_end = day_window_utc(delivery_day, delivery_day)
    in_delivery_day = (forecasts["target_time"] >= day_start) & (forecasts["target_time"] < day_end)
    return forecasts[(forecasts["publish_time"] == newest_run) & in_delivery_day]


# ---------- step 2: compare with what really happened ----------

def compare_with_actuals(forecasts: pd.DataFrame, actuals: pd.DataFrame, cutoff: time) -> pd.DataFrame:
    """One row per delivery hour in the study period, with forecast, actual and error.

    Columns: delivery_date, target_time, publish_time, hours_ahead, forecast, actual, error
    """
    daily_tables = []
    for delivery_day in all_delivery_days():
        table = forecast_available_at_cutoff(forecasts, delivery_day, cutoff).copy()
        table["delivery_date"] = delivery_day
        daily_tables.append(table)

    comparison = pd.concat(daily_tables, ignore_index=True)
    comparison = comparison.merge(actuals, on="target_time", how="left")
    comparison["error"] = comparison["forecast"] - comparison["actual"]
    comparison["hours_ahead"] = (comparison["target_time"] - comparison["publish_time"]).dt.total_seconds() / 3600
    return comparison.sort_values("target_time").reset_index(drop=True)


# ---------- step 3: accuracy numbers ----------

def summarize_errors(comparison: pd.DataFrame) -> dict:
    """Headline accuracy numbers (all in MW except mape_percent)."""
    valid = comparison.dropna(subset=["actual", "error"])
    error = valid["error"]
    absolute_error = error.abs()
    return {
        "hours_compared": int(len(valid)),
        "mean_actual": float(valid["actual"].mean()),
        "mae": float(absolute_error.mean()),                       # average size of the miss
        "rmse": float(np.sqrt((error ** 2).mean())),               # like MAE but punishes big misses
        "bias": float(error.mean()),                               # >0: forecasts too high on average
        "mape_percent": float((absolute_error / valid["actual"]).mean() * 100),
        "error_p10": float(error.quantile(0.1)),                   # signed: 1 hour in 10 the forecast was this much too LOW or worse
        "error_p90": float(error.quantile(0.9)),                   # signed: 1 hour in 10 the forecast was this much too HIGH or worse
        "median_abs_error": float(absolute_error.quantile(0.5)),
        "p90_abs_error": float(absolute_error.quantile(0.9)),      # 9 hours in 10 miss by less than this
        "p95_abs_error": float(absolute_error.quantile(0.95)),
    }


def history_known_at_decision(comparison: pd.DataFrame, delivery_day: date) -> dict | None:
    """Past forecast errors the buyer could already know when ordering for `delivery_day`.

    Orders are placed on day D-1, when day D-1 is not finished yet. So only delivery
    days up to D-2 count. Later days are the future and must never be used.
    Returns None when there are fewer than MIN_HISTORY_DAYS days of history.
    """
    last_known_day = delivery_day - timedelta(days=2)
    known = comparison[comparison["delivery_date"] <= last_known_day].dropna(subset=["error"])
    days_used = known["delivery_date"].nunique()
    if days_used < MIN_HISTORY_DAYS:
        return None

    error = known["error"]
    return {
        "days_used": int(days_used),
        "through_date": known["delivery_date"].max(),
        "mae": float(error.abs().mean()),
        "bias": float(error.mean()),
        "error_p10": float(error.quantile(0.1)),
        "error_p90": float(error.quantile(0.9)),
    }


def hourly_order(day_forecast: pd.DataFrame, history: dict, demand_mw: float) -> list[dict]:
    """The order to place for each hour of the delivery day (the 'guided' plan).

    Columns needed: target_time, forecast. Each row says how many MW to buy in that hour.
    """
    safe_wind = (day_forecast["forecast"] - history["error_p90"]).clip(lower=0)
    table = pd.DataFrame({
        "target_time": day_forecast["target_time"],
        "forecast_mw": day_forecast["forecast"],
        "safe_wind_mw": safe_wind,
        "buy_mw": (demand_mw - safe_wind).clip(lower=0),
    })
    return table.sort_values("target_time").to_dict("records")


def build_buy_plan(day_forecast: pd.DataFrame, history: dict, demand_mw: float) -> dict:
    """How much to buy for one delivery day, with and without correcting for past errors.

    day_forecast needs columns forecast and actual (actual may be empty).
    Demand is assumed to be the same in every hour of the day.

      raw plan     trusts the forecast as it is
      guided plan  counts on less wind: forecast minus the P90 error seen in the history
    """
    forecast = day_forecast["forecast"]
    safe_wind = (forecast - history["error_p90"]).clip(lower=0)

    def to_buy(wind):
        return (demand_mw - wind).clip(lower=0)

    plan = {
        "demand_mw": demand_mw,
        "forecast_avg_mw": float(forecast.mean()),
        "expected_wind_avg_mw": float(forecast.mean() - history["bias"]),
        "safe_wind_avg_mw": float(safe_wind.mean()),
        "buy_raw_mw": float(to_buy(forecast).mean()),
        "buy_guided_mw": float(to_buy(safe_wind).mean()),
        "outcome": None,
    }

    # When the real wind is already known, check how each plan would have turned out.
    actual = day_forecast["actual"]
    if actual.notna().all():
        needed = to_buy(actual)  # what the buyer really had to buy
        outcome = {}
        for name, wind in (("raw", forecast), ("guided", safe_wind)):
            bought = to_buy(wind)
            outcome[f"shortfall_{name}_mwh"] = float((needed - bought).clip(lower=0).sum())  # bought too little
            outcome[f"surplus_{name}_mwh"] = float((bought - needed).clip(lower=0).sum())    # bought too much
        plan["outcome"] = outcome
    return plan


def errors_by_hour_of_day(comparison: pd.DataFrame) -> list[dict]:
    """Average miss for each hour of the UK day (0-23)."""
    valid = comparison.dropna(subset=["error"]).copy()
    valid["hour"] = valid["target_time"].dt.tz_convert(UK_TIMEZONE).dt.hour
    grouped = valid.groupby("hour")["error"]
    table = pd.DataFrame({"mae": grouped.apply(lambda e: e.abs().mean()), "bias": grouped.mean()})
    return table.reset_index().to_dict("records")


def errors_by_delivery_day(comparison: pd.DataFrame) -> list[dict]:
    """Average miss for each delivery day, to see good and bad days."""
    valid = comparison.dropna(subset=["error"])
    grouped = valid.groupby("delivery_date")["error"]
    table = pd.DataFrame({"mae": grouped.apply(lambda e: e.abs().mean()), "bias": grouped.mean()})
    table = table.reset_index()
    table["delivery_date"] = table["delivery_date"].astype(str)
    return table.to_dict("records")


def errors_by_lead_time(forecasts: pd.DataFrame, actuals: pd.DataFrame, bucket_hours: int = 6) -> list[dict]:
    """How accuracy changes with how far ahead the forecast was made.

    Uses every published forecast (not only the one at the cutoff) whose target
    hour falls in the study period.
    """
    start, end = day_window_utc(FIRST_DELIVERY_DATE, LAST_DELIVERY_DATE)
    in_period = forecasts[(forecasts["target_time"] >= start) & (forecasts["target_time"] < end)]
    table = in_period.merge(actuals, on="target_time", how="inner")

    table["error"] = table["forecast"] - table["actual"]
    hours_ahead = (table["target_time"] - table["publish_time"]).dt.total_seconds() / 3600
    table["bucket_start"] = (hours_ahead // bucket_hours * bucket_hours).astype(int)

    grouped = table.groupby("bucket_start")["error"]
    result = pd.DataFrame({
        "mae": grouped.apply(lambda e: e.abs().mean()),
        "bias": grouped.mean(),
        "count": grouped.size(),
    }).reset_index()
    result["bucket_end"] = result["bucket_start"] + bucket_hours
    return result.to_dict("records")


# ---------- helper for the API ----------

def to_json_safe(value):
    """Turn NaN / NaT into None so the value can be sent as JSON."""
    return None if pd.isna(value) else value
