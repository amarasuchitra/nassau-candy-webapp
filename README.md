# Nassau Candy — Factory Reallocation & Shipping Optimization

**Where should we ship each product from?** A full-stack web application that
answers that for every product, destination region and ship mode, compares
factories before you move a product, ranks the biggest reassignment
opportunities and flags the risky ones.

```
 data/*.csv ──► pipeline ──► trained model + outputs/ ──► FastAPI backend ──► dashboard (web/)
               (clean → EDA → train 3 models → simulate → rank)     /api/*            same page, live data
```

- **Frontend** — `web/index.html`: Factory Simulator · Compare · Recommendations · Risk & Impact Panel
- **Backend** — `backend/` (FastAPI): serves the dashboard and a JSON API, with
  live lead-time predictions from the trained model
- **Pipeline** — `backend/pipeline.py` runs the analysis code in `src/` end to end
- **Deployment** — Render (one-click Blueprint), Docker, Railway/Heroku (`Procfile`),
  or any static host for the dashboard alone

---

## Run it locally

**Windows:** double-click **`start_dashboard.bat`**.
**Mac/Linux:** run `./start.sh`.

The first run sets up a private Python environment (about 1–2 minutes). After
that, the browser opens **http://127.0.0.1:8000** (or the next free port, e.g. 8001,
if something else is already using 8000 — the window shows the exact address).
Keep the black window open while you use the app; close it to stop.

Everything the page needs (including the Chart.js charting library, in `web/vendor/`)
ships with the app, so it works without internet access.

You need Python 3.11 or newer ([python.org](https://www.python.org/downloads/); on Windows tick
*"Add python.exe to PATH"*).

Manual alternative:

```bash
python -m venv .venv
.venv\Scripts\activate            # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

- Dashboard: http://localhost:8000
- Interactive API docs: http://localhost:8000/docs

> Opening `web/index.html` directly (double-click) still works too. It uses a
> built-in copy of the data (the status bar shows *Offline data* instead of *Live data*).

---

## API

| Method | Endpoint | What it answers |
|---|---|---|
| GET | `/api/health` | Is the app up, is the model loaded |
| GET | `/api/meta` | Products (with current factory), regions, factories, ship modes |
| GET | `/api/summary` | Orders analysed, win-win routes, estimated profit uplift |
| GET | `/api/simulate?product=&region=&ship_mode=` | Every factory ranked by predicted lead time, recommended vs current, days/miles saved |
| POST | `/api/predict` | Live model prediction for any product × region × factory × ship mode (optional units, sales) |
| GET | `/api/compare?product=&candidate=` | Current factory vs a candidate: lead time, shipping cost, orders affected, per region |
| GET | `/api/recommendations?region=&min_orders=&priority=&limit=` | Ranked recommendations (priority 0 = profit first, 1 = speed first) |
| GET | `/api/recommendations/top?n=3` | The biggest opportunities |
| GET | `/api/risk` | Profit trade-offs and low-confidence recommendations |
| GET | `/api/bundle` | Everything the dashboard renders, in one document |
| POST | `/api/admin/rebuild?full=true` | Re-run the pipeline (needs `ADMIN_TOKEN`, sent as `X-Admin-Token`) |

Example:

```bash
curl "http://localhost:8000/api/simulate?product=Wonka%20Bar%20-%20Milk%20Chocolate&region=Pacific&ship_mode=Same%20Day"
curl -X POST http://localhost:8000/api/predict -H "content-type: application/json" \
     -d '{"product":"Nerds","region":"Gulf","factory":"Wicked Choccy'"'"'s","ship_mode":"First Class"}'
```

---

## Deploy

### Option 1 — Render (recommended, free tier)

1. Put this folder in a GitHub repository (github.com → **New repository** → upload the files,
   or `git init && git add . && git commit -m "init" && git push`).
2. On [render.com](https://render.com): **New + → Blueprint** → pick the repository.
   Render reads `render.yaml` and creates the web service automatically.
3. Click **Apply**. First deploy takes ~3–5 minutes. You get a URL like
   `https://nassau-candy-reallocation.onrender.com`.

Health check: `/api/health`. Free instances sleep after 15 minutes idle; the
first visit afterwards takes ~30–60 seconds to wake up.

*(Without the Blueprint: New + → Web Service → Build command `pip install -r requirements.txt`,
Start command `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`, env var `PYTHON_VERSION=3.11.9`.)*

### Option 2 — Docker (any cloud: AWS, Azure, GCP, Fly.io, a VM)

```bash
docker build -t nassau-candy .
docker run -p 8000:8000 nassau-candy
```

The container honours `$PORT` and has a built-in health check.

### Option 3 — Railway / Heroku-style hosts

Connect the repository; the `Procfile` starts the app. Set `PYTHON_VERSION=3.11.9` if asked.

### Option 4 — Dashboard only, no backend (Netlify / Vercel / GitHub Pages)

`netlify.toml` and `vercel.json` publish the `web/` folder. The page detects there is no
API and uses its built-in data (`web/data/`); the numbers are the same.
Netlify drag & drop: [app.netlify.com/drop](https://app.netlify.com/drop) → drag the `web` folder in.

### Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `PORT` | 8000 | Port to listen on (set automatically by hosts) |
| `ADMIN_TOKEN` | *(unset)* | Enables `POST /api/admin/rebuild`. Render generates one for you. |
| `CORS_ORIGINS` | `*` | Comma-separated origins allowed to call the API from another site |

---

## Update the data / retrain

Replace `data/Nassau_Candy_Distributor.csv` (same columns), then:

```bash
python -m backend.pipeline              # clean → EDA → train & compare 3 models → simulate → rank → dashboard data (~30 s)
python -m backend.pipeline --skip-eda   # faster, no charts
python -m backend.pipeline --bundle     # only rebuild dashboard data from existing outputs
```

Restart the app (or call `/api/admin/rebuild?full=true` on a deployed one) to serve the new results.
The pipeline is deterministic: re-running it on the current CSV reproduces every number exactly.

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

17 API tests cover every endpoint, input validation, and parity between the live model
and the dashboard. GitHub Actions runs them on every push (`.github/workflows/ci.yml`).

---

## Project structure

```
backend/
  main.py            FastAPI app: API routes + serves web/
  services.py        Simulator, compare, recommendations, risk (mirrors the dashboard logic)
  bundle.py          Builds the dashboard data from pipeline outputs + the model
  pipeline.py        One command for the whole analysis pipeline
  config.py          Paths and environment settings
src/                 Analysis code: data_prep, eda, modeling, simulate, constants
web/
  index.html         The dashboard
  data/              Built-in copy of the data (static hosting / offline)
data/                Source orders CSV
outputs/             Trained model, recommendations, summaries, charts
tests/               API tests
streamlit_app/       Earlier Streamlit version (optional; see below)
Dockerfile, render.yaml, Procfile, .python-version    Deployment
start_dashboard.bat, start.sh                         Local launchers
research_paper.md, executive_summary.md               Project write-ups
```

The earlier Streamlit version still runs on its own if you need it:
`pip install -r streamlit_app/requirements.txt && streamlit run streamlit_app/app.py`
(it does not include the new dashboard design).

---

## Notes on the numbers

- The source file's `Ship Date` is 2–4 years ahead of `Order Date` on every row (a data-export
  artifact), so lead time is a transparent distance + ship-mode **model-based estimate**
  (see `research_paper.md` §3). When real shipment dates are available, re-run the pipeline;
  nothing else needs to change.
- Shipping cost is not in the source data; it uses an illustrative **$0.001 per mile per unit**
  proxy (`src/constants.py`). Recalibrate against real freight invoices before using it financially.
