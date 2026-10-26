# Plan: UK Wind Forecast Monitor (Day-Ahead Buying Support)

Time budget: max 16h. Track with checkboxes. Update status as we go.

## 1. Task Understanding

**Client:** UK energy utility, team buys power on the **day-ahead market**.
**Problem:** Decide how much power to buy (e.g. thermal) beyond wind. Decision made D-1, so they rely on wind **forecasts**.
**Product must let them:**
1. See the **latest wind forecast available at decision time** (for delivery day D, the newest forecast published before the D-1 decision cutoff).
2. **Quantify forecast accuracy** (error metrics) so decisions can include an error margin.

**Scope limits:** National-level wind only. Elexon BMRS data only. Decisions made in **January 2026** only.

**Data sources (Elexon BMRS):**
| Dataset | Endpoint | Fields used |
|---|---|---|
| Actuals FUELHH | `/datasets/FUELHH/stream` | `fuelType=WIND`, `startTime` (30 min), `generation` |
| Forecast WINDFOR | `/datasets/WINDFOR/stream` | `startTime`, `publishTime`, `generation` |

**Stack:** React (frontend), Python (backend), Docker, deploy on Vercel or Heroku.

**Deliverables:**
- Unlisted YouTube video, max 10 min total: Part 1 client pitch (<=5 min), Part 2 tech-lead walkthrough (<=5 min). Evaluated first.
- Public GitHub repo with anonymous random name. README: file/dir details, how to start, deployed link, **AI tools usage mention**.
- Submit form: https://forms.cloud.microsoft/r/FTX6K2bbnU. Check every URL in incognito.

## 2. Key Domain Decisions (to confirm in research)

- Day-ahead decision cutoff: assumption = gate ~09:20 UK (EPEX/N2EX auctions ~09:20-12:00 on D-1). Pick a cutoff (e.g. 09:00 D-1) and make it **configurable** in UI.
- "Latest forecast available" for target time T = forecast with max `publishTime` <= cutoff(D-1) for T on day D.
- WINDFOR is hourly-ish with horizon up to several days; check actual resolution. FUELHH is 30 min. Align by resampling/matching on `startTime`.
- Metrics: MAE, RMSE, bias (mean error), MAPE (careful near zero), P50/P90/P95 abs error, error by horizon, error by hour of day. Optional: error as % of capacity/mean.
- Output for buyer: forecast + error band (e.g. forecast +/- P90 error) and "residual demand to cover" view.
- Data time range: target days in Jan 2026 (decisions made Jan 2026 -> deliveries Jan 2 .. Feb 1 possibly; decide and document).

## 3. Phases

### Phase 0: Setup  (~0.5h)
- [x] Folder `D:\wind-forecast-app`
- [x] `backend/venv` Python venv
- [x] `frontend` Vite + React app, deps installed
- [ ] `git init`, `.gitignore`, anonymous repo name chosen
- [ ] Install Docker Desktop (not found locally)

### Phase 1: Data research (~1.5h)
- [x] Call FUELHH + WINDFOR streams for Jan 2026, inspect shape, resolution, gaps, duplicates
- [x] Understand forecast horizons (publishTime vs startTime gap)
- [x] Decide cutoff + date range, write findings in `docs/analysis.md`
- [x] Script prototyping the metrics (`scripts/prototype.py`)

### Phase 2: Backend (~3h) DONE
- [x] FastAPI app, `requirements.txt`
- [x] Elexon client (`elexon.py`), saved snapshot in `backend/data/` (`scripts/fetch_data.py` refreshes it)
- [x] Alignment of "latest-before-cutoff" forecast vs actuals (`analysis.py`)
- [x] Endpoints: `/api/health`, `/api/config`, `/api/forecast`, `/api/accuracy`
- [x] pytest: 15 tests pass (logic + API)
- [x] Pydantic schemas, 404/422 errors
- Code layout: config -> elexon -> data_loader -> analysis -> main (one job per file)

### Phase 3: Frontend (~4h) MOSTLY DONE
- [x] Layout, theme (light + dark, validated chart colours), API client
- [x] Controls: delivery date picker, decision cutoff
- [x] Chart: actual vs forecast + likely-range band, hourly
- [x] KPI cards: MAE, bias, RMSE, worst 1-in-10
- [x] Error views: by day, by hour of day, by lead time
- [x] "What to plan for" guidance panel
- [x] Loading / error states
- [ ] Check real phone width, light-mode screenshot, README/test pass
### Phase 4: Docker + Deploy (~2h)
- [x] backend/Dockerfile, frontend/Dockerfile (+ nginx.conf), docker-compose.yml, .dockerignore files
- [x] Vercel setup: vercel.json, api/index.py, root requirements.txt (entry point tested locally)
- [ ] Install Docker Desktop, run `docker compose up --build`, open http://localhost:8080
- [ ] Push repo to GitHub (random name), import in Vercel, deploy
- [ ] Verify deployed app in incognito
### Phase 5: Docs + Repo (~1h)
- [x] README: structure, run steps, AI usage disclosure (live link still TODO)
- [ ] Push to public repo with random name

### Phase 6: Video (~2h)
- [ ] Script Part 1 (client pitch, <=5 min) and Part 2 (tech review, <=5 min), total <=10 min
- [ ] Record, upload unlisted to YouTube, verify in incognito

### Phase 7: Submit (~0.5h)
- [ ] Fill form, verify all URLs in incognito

## 4. Proposed Structure
```
wind-forecast-app/
  plan.md
  README.md
  docker-compose.yml
  backend/
    venv/            (ignored)
    app/ (main.py, elexon.py, analysis.py, schemas.py)
    tests/
    requirements.txt
    Dockerfile
  frontend/
    src/ (components, api, pages)
    Dockerfile
  docs/analysis.md
```

## 5. Risks / Open Questions
- Docker not installed locally: install Docker Desktop (needs WSL2).
- Elexon stream API limits (date range per call): may need chunked fetch.
- Vercel Python serverless has timeout/size limits: cache pre-fetched Jan 2026 data as static file if API slow.
- Exact decision cutoff time: document assumption clearly in video + README.

## 6. Progress Log
- 2026-10-26: Project folder, venv, React app created.
- 2026-10-26: Phase 2 done. API numbers match prototype (MAE 2073, bias +1773). Frontend re-scaffolded as real React (first attempt was vanilla TS).
- 2026-10-26: Phase 1 done. Findings in `docs/analysis.md`. Forecasts hourly vs actuals 30-min; actuals need dedupe; 09:00 cutoff -> MAE 2.07 GW, bias +1.77 GW (over-forecast).


