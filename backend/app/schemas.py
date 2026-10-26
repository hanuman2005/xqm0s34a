"""Shapes of the JSON the API sends back. FastAPI uses these to validate and document responses."""
from datetime import date, datetime

from pydantic import BaseModel


class ConfigResponse(BaseModel):
    first_delivery_date: date
    last_delivery_date: date
    default_cutoff: str  # "HH:MM", UK time


class ForecastHour(BaseModel):
    target_time: datetime
    forecast: float
    actual: float | None  # None if the real value is not known
    error: float | None   # forecast - actual


class HistorySummary(BaseModel):
    """Past errors known at decision time (earlier delivery days only)."""
    days_used: int
    through_date: date
    mae: float
    bias: float
    error_p10: float
    error_p90: float


class PlanOutcome(BaseModel):
    """How each plan turned out once the real wind was known. MWh = MW summed over the day's hours."""
    shortfall_raw_mwh: float
    shortfall_guided_mwh: float
    surplus_raw_mwh: float
    surplus_guided_mwh: float


class BuyPlan(BaseModel):
    demand_mw: float
    forecast_avg_mw: float
    expected_wind_avg_mw: float
    safe_wind_avg_mw: float
    buy_raw_mw: float
    buy_guided_mw: float
    outcome: PlanOutcome | None


class ForecastResponse(BaseModel):
    delivery_date: date
    cutoff_utc: datetime      # the buyer's deadline
    publish_time: datetime    # when the forecast we used was created
    hours: list[ForecastHour]
    history: HistorySummary | None   # None when too few earlier days exist
    plan: BuyPlan | None             # None without history or without a demand figure


class AccuracySummary(BaseModel):
    hours_compared: int
    mean_actual: float
    mae: float
    rmse: float
    bias: float
    mape_percent: float
    error_p10: float
    error_p90: float
    median_abs_error: float
    p90_abs_error: float
    p95_abs_error: float


class HourOfDayError(BaseModel):
    hour: int
    mae: float
    bias: float


class DeliveryDayError(BaseModel):
    delivery_date: str
    mae: float
    bias: float


class LeadTimeError(BaseModel):
    bucket_start: int
    bucket_end: int
    mae: float
    bias: float
    count: int


class AccuracyResponse(BaseModel):
    cutoff: str
    summary: AccuracySummary
    by_hour_of_day: list[HourOfDayError]
    by_delivery_day: list[DeliveryDayError]
    by_lead_time: list[LeadTimeError]
