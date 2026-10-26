"""Read the saved Elexon JSON files and turn them into clean pandas tables.

Both tables use UTC timestamps. The data is loaded once and kept in memory.
"""
import json
from functools import lru_cache

import pandas as pd

from .config import ACTUALS_FILE, FORECASTS_FILE


def _read_json_table(path) -> pd.DataFrame:
    table = pd.DataFrame(json.loads(path.read_text()))
    table["startTime"] = pd.to_datetime(table["startTime"], utc=True)
    table["publishTime"] = pd.to_datetime(table["publishTime"], utc=True)
    return table


@lru_cache
def load_actuals() -> pd.DataFrame:
    """Actual wind generation per HOUR, columns: target_time, actual (MW).

    Elexon gives one value per 30 minutes. Forecasts are hourly, so we average
    the two half-hours of each hour to compare like with like.
    """
    table = _read_json_table(ACTUALS_FILE)

    # Fetching in chunks returns the boundary days twice. Keep only the latest copy.
    table = table.sort_values("publishTime").drop_duplicates("startTime", keep="last")

    table["target_time"] = table["startTime"].dt.floor("h")
    hourly = table.groupby("target_time", as_index=False)["generation"].mean()
    return hourly.rename(columns={"generation": "actual"})


@lru_cache
def load_forecasts() -> pd.DataFrame:
    """Every forecast ever published, columns: target_time, publish_time, forecast (MW).

    Forecasts about hours that had already passed when they were published are
    dropped, because they are not real predictions.
    """
    table = _read_json_table(FORECASTS_FILE)
    table = table.rename(columns={
        "startTime": "target_time",
        "publishTime": "publish_time",
        "generation": "forecast",
    })
    table = table[table["target_time"] >= table["publish_time"]]
    return table[["target_time", "publish_time", "forecast"]].reset_index(drop=True)
