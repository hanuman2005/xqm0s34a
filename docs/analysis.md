# Data Analysis Findings (Phase 1)

Scripts: `scripts/explore.py` (fetch + profile), `scripts/prototype.py` (alignment + metrics). Raw cache: `data/*.json` (git-ignored or committed as Jan 2026 snapshot, decide in Phase 4).

## API
Base: `https://data.elexon.co.uk/bmrs/api/v1/datasets`
- Actuals: `FUELHH/stream?settlementDateFrom&settlementDateTo&fuelType=WIND`
- Forecasts: `WINDFOR/stream?publishDateTimeFrom&publishDateTimeTo` (filter is on **publish time**, not target time)
- No auth needed. Fetched in chunks (7 days actuals, 2 days forecasts) to stay safe on limits.

## Actuals (FUELHH, WIND)
- 30-min resolution, no nulls, no gaps. Range 2025-12-30 .. 2026-02-03.
- Chunk edges overlap (inclusive date ranges): 192 duplicate `startTime`. Must dedupe (keep latest `publishTime`).
- Wind actual: mean ~11.5 GW, range 1.7 - 17.8 GW.

## Forecasts (WINDFOR)
- **Hourly** resolution (60 min step), vs 30-min actuals. Align by averaging the two half-hours of each hour (verified every hour has exactly 2).
- Each publish contains 73 rows (hourly). ~8-9 publishes/day at irregular UTC hours: 02:30, 04:30, 07:30, 09:30, 11:30, 12:30, 15:30, 18:30, 22:30.
- ~20% of rows have startTime **before** publishTime (already-elapsed hours). Ignore for decision use; only horizon >= 0 is a true forecast.
- Max horizon ~66h. No duplicates on (startTime, publishTime), no nulls.

## Decision-time logic
For delivery day D (Jan 2 .. Jan 31 here; decisions made on D-1 in January):
- cutoff = D-1 at HH:MM (default **09:00 UK**, configurable). UK = UTC in January.
- For each target hour: use the forecast with the **max publishTime <= cutoff**.
- With 09:00 cutoff the used publish is always the 07:30 run (horizon 16.5 - 39.5 h before delivery hours).
- Result: 30 delivery days x 24 h = 720 aligned points, 0 missing.
- Note: a forecast published after cutoff (09:30 etc.) must NOT be used for accuracy evaluation. That would leak future info.

## Prototype accuracy (cutoff 09:00, hourly, Jan 2-31 2026)
| Metric | Value |
|---|---|
| MAE | 2,073 MW |
| RMSE | 2,539 MW |
| Bias (forecast - actual) | **+1,773 MW** (forecasts over-predict wind) |
| P50 / P90 abs error | 1,720 / 4,167 MW |
| MAPE | 22.2% |
| Mean actual | 11,454 MW |

- Strong **positive bias**: buyer relying on the raw forecast would under-buy thermal by ~1.8 GW on average. Key client message.
- Error by hour of day is fairly flat (1.8 - 2.5 GW), higher in early morning (03-06h).

## No look-ahead rule (added in Phase 5)
The table above uses all of January, so it is a look-back report only. For buying advice on delivery day D the app uses errors from delivery days up to D-2 (needs at least 3 days). Using later days would leak the future. Safe wind = forecast - P90 of past (forecast - actual). Buy = demand - safe wind, compared against buying on the raw forecast.

## Decisions
- Metrics: MAE, RMSE, bias, P50/P90/P95 abs error, MAPE (guard actual near 0), error by hour of day, error by horizon, daily MAE trend.
- Show bias-corrected / error-band view: forecast minus bias, with P10-P90 band, as buying guidance.
- Cutoff configurable; default 09:00 UK.
- Data layer: backend fetches on demand and caches to disk; for Vercel ship a pre-fetched Jan 2026 snapshot.

## Open
- Confirm with domain knowledge that day-ahead gate is ~09:20 UK (N2EX/EPEX auctions) so 09:00 is a reasonable default.
- Check whether the Jan 1 delivery day belongs in scope (decision on Dec 31 = not January). Current choice: delivery days Jan 2 - Feb 1 (decisions Jan 1 - Jan 31). Feb 1 forecast needs publish up to Jan 31, actuals through Feb 1: available.
