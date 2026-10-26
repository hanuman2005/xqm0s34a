"""Download wind data from the Elexon API.

Used by `scripts/fetch_data.py` to create the saved JSON files. The web app itself
reads the saved files, so it never waits on Elexon.
"""
from datetime import date, datetime, timedelta

import httpx

from .config import ELEXON_BASE_URL


def _split_into_chunks(start, end, step: timedelta):
    """Yield (chunk_start, chunk_end) pairs so one API call never asks for too much data."""
    chunk_start = start
    while chunk_start < end:
        chunk_end = min(chunk_start + step, end)
        yield chunk_start, chunk_end
        chunk_start = chunk_end


def _get_json(client: httpx.Client, dataset: str, params: dict) -> list[dict]:
    response = client.get(f"{ELEXON_BASE_URL}/{dataset}/stream", params=params, timeout=60)
    response.raise_for_status()
    return response.json()


def fetch_actual_wind(first_day: date, last_day: date) -> list[dict]:
    """Actual wind generation (FUELHH dataset), one row per 30 minutes."""
    rows = []
    with httpx.Client() as client:
        for chunk_start, chunk_end in _split_into_chunks(first_day, last_day, timedelta(days=7)):
            rows += _get_json(client, "FUELHH", {
                "settlementDateFrom": chunk_start.isoformat(),
                "settlementDateTo": chunk_end.isoformat(),
                "fuelType": "WIND",
            })
    return rows


def fetch_wind_forecasts(published_from: datetime, published_to: datetime) -> list[dict]:
    """Wind forecasts (WINDFOR dataset) published between the two moments (UTC)."""
    rows = []
    with httpx.Client() as client:
        for chunk_start, chunk_end in _split_into_chunks(published_from, published_to, timedelta(days=2)):
            rows += _get_json(client, "WINDFOR", {
                "publishDateTimeFrom": chunk_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "publishDateTimeTo": chunk_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            })
    return rows
