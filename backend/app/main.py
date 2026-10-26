"""The web API. Start it with:  uvicorn app.main:app --reload   (from the backend/ folder)"""
from datetime import date, time

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import analysis
from .config import DEFAULT_CUTOFF, FIRST_DELIVERY_DATE, LAST_DELIVERY_DATE
from .data_loader import load_actuals, load_forecasts
from .schemas import AccuracyResponse, ConfigResponse, ForecastResponse

app = FastAPI(title="Wind Forecast Monitor", description="UK day-ahead wind forecast and accuracy")

# Allow the React app (running on another port) to call this API.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])


def parse_cutoff(cutoff: str) -> time:
    """Turn "09:00" into a time, or answer with a clear 422 error."""
    try:
        return time.fromisoformat(cutoff)
    except ValueError:
        raise HTTPException(status_code=422, detail="cutoff must look like HH:MM, e.g. 09:00")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/config", response_model=ConfigResponse)
def get_config():
    """Date range and default cutoff the front-end should offer."""
    return ConfigResponse(
        first_delivery_date=FIRST_DELIVERY_DATE,
        last_delivery_date=LAST_DELIVERY_DATE,
        default_cutoff=DEFAULT_CUTOFF.strftime("%H:%M"),
    )


@app.get("/api/forecast", response_model=ForecastResponse)
def get_forecast(
    delivery_date: date,
    cutoff: str = Query(DEFAULT_CUTOFF.strftime("%H:%M"), description="Decision time on D-1, UK time, HH:MM"),
    demand_mw: float | None = Query(None, ge=0, description="Buyer's demand in MW (same every hour)"),
):
    """The latest forecast the buyer could see at the cutoff, plus buying advice from past errors."""
    if not FIRST_DELIVERY_DATE <= delivery_date <= LAST_DELIVERY_DATE:
        raise HTTPException(status_code=404, detail=f"delivery_date must be {FIRST_DELIVERY_DATE} to {LAST_DELIVERY_DATE}")
    cutoff_time = parse_cutoff(cutoff)

    forecast = analysis.forecast_available_at_cutoff(load_forecasts(), delivery_date, cutoff_time)
    if forecast.empty:
        raise HTTPException(status_code=404, detail="No forecast was published before this cutoff")

    table = forecast.merge(load_actuals(), on="target_time", how="left")
    table["error"] = table["forecast"] - table["actual"]

    # Only errors from days before this delivery day are used, so there is no peeking into the future.
    comparison = analysis.compare_with_actuals(load_forecasts(), load_actuals(), cutoff_time)
    history = analysis.history_known_at_decision(comparison, delivery_date)
    plan = order = None
    if history is not None and demand_mw is not None:
        plan = analysis.build_buy_plan(table, history, demand_mw)
        order = analysis.hourly_order(table, history, demand_mw)

    return ForecastResponse(
        history=history,
        plan=plan,
        order=order,
        delivery_date=delivery_date,
        cutoff_utc=analysis.cutoff_time_utc(delivery_date, cutoff_time),
        publish_time=table["publish_time"].iloc[0],
        hours=[
            {
                "target_time": row.target_time,
                "forecast": row.forecast,
                "actual": analysis.to_json_safe(row.actual),
                "error": analysis.to_json_safe(row.error),
            }
            for row in table.sort_values("target_time").itertuples()
        ],
    )


@app.get("/api/accuracy", response_model=AccuracyResponse)
def get_accuracy(cutoff: str = Query(DEFAULT_CUTOFF.strftime("%H:%M"))):
    """How accurate the cutoff-time forecasts were over the whole study period."""
    cutoff_time = parse_cutoff(cutoff)
    forecasts, actuals = load_forecasts(), load_actuals()

    comparison = analysis.compare_with_actuals(forecasts, actuals, cutoff_time)
    if comparison.empty:
        raise HTTPException(status_code=404, detail="No forecast was published before this cutoff")

    return AccuracyResponse(
        cutoff=cutoff,
        summary=analysis.summarize_errors(comparison),
        by_hour_of_day=analysis.errors_by_hour_of_day(comparison),
        by_delivery_day=analysis.errors_by_delivery_day(comparison),
        by_lead_time=analysis.errors_by_lead_time(forecasts, actuals),
    )
