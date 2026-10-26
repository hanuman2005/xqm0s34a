# Wind Forecast Monitor

A web app that helps a UK energy buyer decide how much power to buy on the day-ahead market. It shows the latest national wind forecast available at decision time, and measures how accurate those forecasts have been, so the buyer can plan for the error.

Data: Elexon BMRS only. Actual wind generation (`FUELHH`, fuel type `WIND`) and wind forecasts (`WINDFOR`). Scope: purchase decisions made in January 2026 (delivery days 2 to 31 January 2026).

**Live app:** `TODO: add Vercel link here`

**Use of AI tools:** This project was built with the help of Claude Code (Anthropic's AI coding assistant) for planning, code generation and documentation. All code was reviewed and run by the author.

## How it works

1. The buyer places an order by a cutoff time (default 09:00 UK time) on the day before delivery.
2. For each delivery day, the app takes the newest forecast published on or before that cutoff. Forecasts published later are ignored, because the buyer could not have seen them.
3. That forecast is compared with the wind that was actually generated. Error is forecast minus actual, so a positive error means the forecast was too high.
4. Accuracy numbers (typical miss, bias, worst-case misses) are turned into plain guidance: how much wind to count on.

Assumptions:
- Forecasts are hourly and actuals are half-hourly, so each hour's actual is the average of its two half-hours.
- The 09:00 default cutoff is an assumption about the day-ahead deadline. It can be changed in the app.
- Forecasts about hours that had already passed when they were published are dropped.
- Duplicate actual rows created by fetching in chunks are removed.

More detail and the numbers behind these choices: [docs/analysis.md](docs/analysis.md).

## Files and directories

```
.
├── README.md
├── plan.md                  Project plan and progress tracker
├── docker-compose.yml       Starts backend and frontend together
├── vercel.json              Vercel deployment settings
├── requirements.txt         Python dependencies for the Vercel function
├── api/
│   └── index.py             Vercel entry point (loads the FastAPI app)
├── backend/                 Python API (FastAPI)
│   ├── app/
│   │   ├── config.py        Settings: dates, default cutoff, file paths
│   │   ├── elexon.py        Downloads data from the Elexon API
│   │   ├── data_loader.py   Reads saved data, cleans it, builds hourly tables
│   │   ├── analysis.py      Picks the forecast at the cutoff, compares, computes metrics
│   │   ├── schemas.py       Shape of the API responses
│   │   └── main.py          API routes
│   ├── data/                Saved January 2026 data from Elexon (JSON)
│   ├── tests/               pytest tests (logic and API)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                React app (Vite)
│   ├── src/
│   │   ├── App.jsx          Page layout and data loading
│   │   ├── api.js           Calls to the backend
│   │   ├── useApi.js        Small hook for loading data
│   │   ├── format.js        Number and date formatting
│   │   ├── components/      Controls, charts, guidance panel, accuracy section
│   │   ├── App.css          Layout and component styles
│   │   └── index.css        Colours and fonts (light and dark themes)
│   ├── nginx.conf           Serves the app and forwards /api in Docker
│   └── Dockerfile
├── scripts/
│   ├── fetch_data.py        Refreshes backend/data from Elexon
│   └── exploration/         Early scripts used to study the data
└── docs/
    └── analysis.md          Data findings and design decisions
```

## Run with Docker

```
docker compose up --build
```

Open http://localhost:8080. The API docs are at http://localhost:8000/docs.

## Run without Docker

Backend (Python 3.12 or newer), from the project root:

```
cd backend
python -m venv venv
venv\Scripts\activate            # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000
```

Frontend (Node 20 or newer), in a second terminal:

```
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The dev server forwards `/api` to the backend on port 8000.

## Tests

```
cd backend
venv\Scripts\python -m pytest
```

## API

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | Health check |
| `GET /api/config` | Allowed date range and default cutoff |
| `GET /api/forecast?delivery_date=2026-01-15&cutoff=09:00` | The forecast the buyer could see at the cutoff, with actuals |
| `GET /api/accuracy?cutoff=09:00` | Accuracy over all of January: summary, by day, by hour, by lead time |

## Refreshing the data

The app reads the saved files in `backend/data/`, so it does not call Elexon while running. To download the data again:

```
backend\venv\Scripts\python scripts\fetch_data.py
```

## Deploying to Vercel

Import the repository in Vercel and deploy with the default settings. `vercel.json` builds the frontend and runs the API as a Python function.
