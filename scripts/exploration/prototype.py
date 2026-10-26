"""Phase 1 prototype: latest-before-cutoff alignment + error metrics."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

D = Path(__file__).resolve().parent.parent.parent / "backend" / "data"
a = pd.DataFrame(json.loads((D / "actuals_raw.json").read_text()))
f = pd.DataFrame(json.loads((D / "forecasts_raw.json").read_text()))
for df in (a, f):
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    df["publishTime"] = pd.to_datetime(df["publishTime"], utc=True)

# actuals: dedupe chunk overlaps (keep latest publish), then check
a = a.sort_values("publishTime").drop_duplicates("startTime", keep="last").sort_values("startTime")
print("actuals after dedupe:", len(a), "range", a.startTime.min(), a.startTime.max())

# hourly actual = mean of the two half-hours starting at hh:00 and hh:30
a["hour"] = a.startTime.dt.floor("h")
act_h = a.groupby("hour").generation.agg(["mean", "count"])
print("hours with !=2 half-hours:", (act_h["count"] != 2).sum())
act_h = act_h["mean"].rename("actual")

# Negative horizons: forecasts for times before publish
f["h"] = (f.startTime - f.publishTime).dt.total_seconds() / 3600
print("share forecast rows with horizon<0:", (f.h < 0).mean().round(3))
print("min positive horizon per publish (median):", f[f.h >= 0].groupby("publishTime").h.min().median())

CUTOFF_HOUR = 9  # UTC == UK in January
rows = []
for day in pd.date_range("2026-01-02", "2026-01-31", tz="UTC"):  # delivery days; decisions on D-1 in Jan
    cutoff = day - pd.Timedelta(days=1) + pd.Timedelta(hours=CUTOFF_HOUR)
    pubs = f[f.publishTime <= cutoff].publishTime
    if pubs.empty:
        continue
    pub = pubs.max()
    sub = f[(f.publishTime == pub) & (f.startTime >= day) & (f.startTime < day + pd.Timedelta(days=1))]
    sub = sub.assign(delivery_day=day, used_publish=pub)
    rows.append(sub)
m = pd.concat(rows).merge(act_h, left_on="startTime", right_index=True, how="left")
m["err"] = m.generation - m.actual
print("\naligned rows:", len(m), "missing actual:", m.actual.isna().sum(), "days:", m.delivery_day.nunique())
print("rows per day (expect 24):", m.groupby("delivery_day").size().value_counts().to_dict())
e = m.err.dropna()
print(f"MAE={e.abs().mean():.0f} MW  RMSE={np.sqrt((e**2).mean()):.0f}  bias={e.mean():.0f}  "
      f"P50|e|={e.abs().quantile(.5):.0f} P90|e|={e.abs().quantile(.9):.0f}  "
      f"MAPE={(e.abs()/m.actual.loc[e.index]).mean()*100:.1f}%  mean actual={m.actual.mean():.0f}")
print("\nhorizon (h before delivery hour) range:", m.eval("(startTime-used_publish).dt.total_seconds()/3600").describe()[["min","max"]].to_dict())
m["hod"] = m.startTime.dt.hour
print("\nMAE by hour of day:\n", m.groupby("hod").err.apply(lambda s: s.abs().mean()).round(0).to_string())
print("\nused publish hours UTC:", m.used_publish.dt.hour.value_counts().to_dict())

