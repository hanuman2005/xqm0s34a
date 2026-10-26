"""Settings shared by the whole backend. Change values here, not inside other files."""
from datetime import date, time
from pathlib import Path
from zoneinfo import ZoneInfo

# Elexon BMRS open data API (no API key needed)
ELEXON_BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/datasets"

# Folder holding the saved January 2026 data (so the app works offline and loads fast)
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ACTUALS_FILE = DATA_DIR / "actuals_raw.json"
FORECASTS_FILE = DATA_DIR / "forecasts_raw.json"

# Electricity is traded in UK local time
UK_TIMEZONE = ZoneInfo("Europe/London")

# Purchase decisions are made in January 2026 (on day D-1), for delivery on day D.
# Decisions on 1 Jan .. 30 Jan  ->  delivery days 2 Jan .. 31 Jan.
FIRST_DELIVERY_DATE = date(2026, 1, 2)
LAST_DELIVERY_DATE = date(2026, 1, 31)

# Fewest earlier delivery days needed before we trust past errors for buying advice.
MIN_HISTORY_DAYS = 3

# Time of day (UK) when the buyer must decide, on the day before delivery.
DEFAULT_CUTOFF = time(9, 0)
