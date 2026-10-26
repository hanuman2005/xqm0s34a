"""Download January 2026 wind data from Elexon and save it into backend/data/.

Run from the project root:
    backend/venv/Scripts/python scripts/fetch_data.py      (Windows)
    backend/venv/bin/python scripts/fetch_data.py          (Mac / Linux)
"""
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

# Let Python find the `app` package inside backend/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.config import ACTUALS_FILE, FORECASTS_FILE
from app.elexon import fetch_actual_wind, fetch_wind_forecasts

# Decisions are made 1-30 Jan, so forecasts published 31 Dec .. 31 Jan are enough.
# Actuals are needed for delivery days 2-31 Jan (we also grab 1 Feb to be safe).
actuals = fetch_actual_wind(date(2026, 1, 1), date(2026, 2, 1))
forecasts = fetch_wind_forecasts(
    datetime(2025, 12, 31, tzinfo=timezone.utc),
    datetime(2026, 2, 1, tzinfo=timezone.utc),
)

ACTUALS_FILE.write_text(json.dumps(actuals))
FORECASTS_FILE.write_text(json.dumps(forecasts))
print(f"Saved {len(actuals)} actual rows and {len(forecasts)} forecast rows.")
