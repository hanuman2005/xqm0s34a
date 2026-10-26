"""Phase 1: fetch Jan 2026 FUELHH (WIND) + WINDFOR from Elexon, cache raw, profile."""
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx
import pandas as pd

BASE = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
OUT = Path(__file__).resolve().parent.parent.parent / "backend" / "data"
OUT.mkdir(exist_ok=True)


def chunks(start, end, days):
    cur = start
    while cur < end:
        nxt = min(cur + timedelta(days=days), end)
        yield cur, nxt
        cur = nxt


def get(client, path, params):
    r = client.get(f"{BASE}/{path}", params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def fetch_actuals(client):
    rows = []
    for a, b in chunks(date(2025, 12, 30), date(2026, 2, 3), 7):
        rows += get(client, "FUELHH/stream", {
            "settlementDateFrom": a.isoformat(),
            "settlementDateTo": b.isoformat(),
            "fuelType": "WIND",
        })
    return rows


def fetch_forecasts(client):
    rows = []
    t0 = datetime(2025, 12, 29, tzinfo=timezone.utc)
    t1 = datetime(2026, 2, 1, tzinfo=timezone.utc)
    for a, b in chunks(t0, t1, 2):
        rows += get(client, "WINDFOR/stream", {
            "publishDateTimeFrom": a.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "publishDateTimeTo": b.strftime("%Y-%m-%dT%H:%M:%SZ"),
        })
    return rows


if __name__ == "__main__":
    with httpx.Client() as c:
        act = fetch_actuals(c)
        fc = fetch_forecasts(c)
    (OUT / "actuals_raw.json").write_text(json.dumps(act))
    (OUT / "forecasts_raw.json").write_text(json.dumps(fc))

    a = pd.DataFrame(act)
    f = pd.DataFrame(fc)
    for d, cols in ((a, ["startTime", "publishTime"]), (f, ["startTime", "publishTime"])):
        for col in cols:
            d[col] = pd.to_datetime(d[col], utc=True)

    print("== ACTUALS ==", a.shape)
    print(a.fuelType.unique(), a.startTime.min(), a.startTime.max())
    print("dup startTime:", a.startTime.duplicated().sum(), "nulls:", a.generation.isna().sum())
    exp = pd.date_range(a.startTime.min(), a.startTime.max(), freq="30min")
    print("missing 30-min slots:", len(exp.difference(pd.DatetimeIndex(a.startTime))))
    print(a.generation.describe())

    print("\n== FORECASTS ==", f.shape)
    print(f.startTime.min(), f.startTime.max(), f.publishTime.min(), f.publishTime.max())
    print("nulls:", f.generation.isna().sum())
    print("startTime step (min):", f.startTime.drop_duplicates().sort_values().diff().dt.total_seconds().div(60).value_counts().head())
    pt = f.publishTime.drop_duplicates().sort_values()
    print("publish count:", len(pt), "publish step (h):", pt.diff().dt.total_seconds().div(3600).value_counts().head())
    print("publish hours UTC:", sorted(pt.dt.hour.unique()))
    h = (f.startTime - f.publishTime).dt.total_seconds() / 3600
    print("horizon h min/max:", h.min(), h.max())
    print("dup (start,publish):", f.duplicated(["startTime", "publishTime"]).sum())
    print("forecasts per publishTime:\n", f.groupby("publishTime").size().describe())

