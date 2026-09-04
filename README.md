# Decision Simulator
### "Make your next business decision before you make it."
*Simulate. Understand. Decide.*

An AI-assisted, statistics-first business decision-support platform. A business
owner describes a decision ("What if I increase my price by 10%?"), and the
app runs a **real Monte Carlo simulation** — parameterized from their actual
historical data, or from explicit, labeled assumptions in New Business Mode —
to produce Conservative / Expected / Optimistic outcomes, a transparent risk
score, a confidence score, and an explainable recommendation.

An LLM (optional, provider-agnostic) is only ever used to parse natural
language into structured parameters and to reword explanations. **It never
generates the numbers.** With no AI provider configured, the app still works
end-to-end via a deterministic rule-based fallback.

## Table of contents
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Data integrity principles](#data-integrity-principles)
- [Simulation methodology](#simulation-methodology)
- [Project structure](#project-structure)
- [Setup](#setup)
- [Environment variables](#environment-variables)
- [Running tests](#running-tests)
- [API summary](#api-summary)
- [What was verified in the build sandbox vs. what needs your machine](#what-was-verified)
- [Limitations & next steps](#limitations)

## Architecture

```
React (Vite, Tailwind, Recharts)
        │  Axios (JWT bearer)
        ▼
FastAPI REST API
        │
        ▼
Service layer (auth, business, business_data, simulation, insight)
        │
        ├──► Simulation Engine (NumPy/Pandas/SciPy/scikit-learn, pure Python —
        │     no DB or network dependency)
        │
        └──► SQLAlchemy ORM
                │
                ▼
           PostgreSQL
```

AI (optional): `decision_parser.py` calls `ai_service.py`, which is a thin,
provider-agnostic wrapper. With `AI_PROVIDER=none` (the default), decisions
are parsed with transparent keyword rules instead — the app never blocks on
an API key.

## Tech stack

**Frontend:** React, Vite, Tailwind CSS, React Router, Axios, Lucide React, Recharts
**Backend:** Python 3.12, FastAPI, Pydantic, SQLAlchemy, PostgreSQL, psycopg2-binary
**Data/ML:** NumPy, Pandas, SciPy, scikit-learn (XGBoost listed as an optional dependency; the shipped engine deliberately uses the simplest adequate method — percentile-based Monte Carlo plus a linear-regression demand-elasticity fit — rather than forcing a heavier model where it isn't justified by the data)
**Testing:** plain-Python assertion tests for the simulation engine (no framework dependency); pytest-compatible

## Data integrity principles

This project follows a strict rule, enforced end-to-end:

> **Real user data → real dashboard data. No user data → no business numbers. Never fake data to make the UI look full.**

Concretely:
- The dashboard shows literal **"No data yet"** for every metric until the business has stored records — never zeros, never placeholders.
- CSV upload validates every row; invalid rows are rejected and reported, never silently zero-filled.
- Every simulation result, insight, and recommendation carries a **data source note** ("Based on 36 historical records" / "New Business Mode — estimated assumptions").
- New Business Mode assumptions are labeled `estimated` (not `historical`) everywhere, including in the DB (`SimulationAssumption.source`).
- Synthetic demo CSVs (`data/*.csv`) are separate files, explicitly labeled `Synthetic Demo Data`, and are never auto-loaded into a real account.
- Demand elasticity is only computed from data when ≥6 clean historical records exist; otherwise a clearly labeled assumption band ("Demand sensitivity is estimated because insufficient historical data was available") is used instead — see `data_analysis.py` / `engine.py`.

## Simulation methodology

1. **Historical analysis** (`app/simulation/data_analysis.py`): computes average revenue/customers/order value, growth rate (log-linear fit), volatility (coefficient of variation), profit margin, marketing efficiency, and demand elasticity (log-log regression, only with ≥6 records) — purely from the records in the database. Also computes a 0–100 data quality score from completeness, record count, and date coverage.
2. **Decision translation** (`app/simulation/engine.py::_decision_deltas`): converts the structured decision (pricing / marketing / hiring / expansion / product_launch / cost_reduction) into explicit multipliers/deltas applied to price, customer demand, marketing spend, and fixed costs.
3. **Monte Carlo** (10,000 iterations by default, configurable via `SIMULATION_ITERATIONS`): samples customers (lognormal, bounded ≥0), price (small lognormal noise), and costs (lognormal) from distributions parameterized by the historical volatility (or a wider band in New Business Mode), applies the accounting identity `profit = revenue − variable_cost − fixed_cost − marketing_spend`, and takes the 10th / 50th / 90th percentiles as Conservative / Expected / Optimistic.
4. **Risk score** (0–100): weighted combination of outcome volatility, downside probability, downside magnitude, parameter uncertainty (elasticity estimated vs. measured), and data quality penalty.
5. **Confidence score** (0–100): weighted combination of data quality, whether elasticity was measured or assumed, outcome volatility, and a New Business Mode penalty.
6. **Explainability**: positive/negative/uncertain factors are derived directly from which levers moved (price, demand response, marketing, fixed costs) — not generated freeform.
7. **Recommendation**: a deterministic decision tree over risk score and expected-vs-baseline profit (`Proceed` / `Proceed cautiously` / `Test on a smaller scale` / `Gather more data` / `Avoid for now`).
8. **Reproducibility**: an optional `seed` produces identical results — verified in `backend/tests/test_simulation_engine.py`.

## Project structure

```
decision-simulator/
├── frontend/                  React + Vite + Tailwind app
│   └── src/{components,layouts,pages,services,context}
├── backend/
│   ├── app/
│   │   ├── main.py            FastAPI app, CORS, startup, global error handler
│   │   ├── config.py          env-driven settings (no hardcoded secrets)
│   │   ├── database.py        SQLAlchemy engine/session/init
│   │   ├── models/            User, Business, BusinessData, Simulation(+Assumption/Result), Insight, Notification
│   │   ├── schemas/            Pydantic request/response models
│   │   ├── routers/           auth, business, business_data, simulations, insights, compare, reports, notifications
│   │   ├── services/           business logic (kept out of routers)
│   │   ├── simulation/         data_analysis.py, engine.py — the numerical core, DB-free
│   │   ├── ai/                 decision_parser.py, ai_service.py — optional, provider-agnostic
│   │   └── utils/              security.py (JWT/bcrypt), deps.py (auth dependency)
│   ├── tests/test_simulation_engine.py   runnable with plain `python3`, no DB
│   ├── init_db.py              one-shot table creation
│   ├── requirements.txt
│   └── .env.example
├── data/                       3 synthetic demo CSVs, clearly labeled, never auto-seeded
└── README.md (this file)
```

## Password hashing (bcrypt, not passlib)

Passwords are hashed by calling the `bcrypt` package directly
(`app/utils/security.py`) — **not** via `passlib.CryptContext`. Passlib is
unmaintained (last release 2020) and has an unresolved incompatibility with
modern `bcrypt` releases: passlib's one-time backend self-test hashes an
over-length probe string to detect bcrypt's behavior, and that probe raises
an uncaught `ValueError` on bcrypt >=4.0 — surfacing as
`"password cannot be longer than 72 bytes, truncate manually if necessary"`
on the *first* password hash of the process, regardless of the real
password's length. Pinning an older bcrypt version does not reliably fix
this. If you ever see that error again, `passlib` has likely been
reintroduced somewhere — run `backend/check_auth_env.py` to check what's
actually active in your environment.

Passwords are validated for UTF-8 byte length (bcrypt's 72-byte limit) in
`app/utils/password_validation.py` and rejected (never truncated) both at
the Pydantic schema layer (`app/schemas/auth.py`, giving a clean 422) and,
as defense-in-depth, inside `hash_password`/`verify_password` themselves.

To verify what's really installed and working in your virtual environment:
```bash
cd backend
python3 check_auth_env.py
```



### 1. PostgreSQL
```bash
createdb decision_simulator
```

### 2. Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python3 -c "import secrets; print(secrets.token_hex(32))"   # paste into JWT_SECRET in .env
python3 init_db.py               # creates tables
uvicorn app.main:app --reload    # http://localhost:8000, docs at /docs
```

### 3. Frontend
```bash
cd frontend
npm install
cp .env.example .env             # VITE_API_URL=http://localhost:8000/api
npm run dev                      # http://localhost:5173
```

### 4. Try it
Register → choose "I'm already running a business" → go to **Business Data**
→ upload `data/sample_retail_business.csv` (label it demo data when asked) →
**Dashboard** now shows real metrics → **New Simulation** → "What if I
increase my product price by 10%?" → review extracted parameters → **Run
Simulation** → **Results**.

## Environment variables

**Backend (`backend/.env`)**
| Variable | Required | Notes |
|---|---|---|
| `DATABASE_URL` | yes | `postgresql://user:pass@host:5432/db` |
| `JWT_SECRET` | yes | generate with `secrets.token_hex(32)`; app refuses to start without it |
| `JWT_EXPIRE_MINUTES` | no | default 1440 |
| `AI_PROVIDER` | no | `none` (default) or `anthropic` |
| `AI_API_KEY` | no | required only if `AI_PROVIDER != none` |
| `AI_MODEL` | no | e.g. `claude-sonnet-4-6` |
| `SIMULATION_ITERATIONS` | no | default 10000 |
| `CORS_ORIGINS` | no | default `http://localhost:5173` |

**Frontend (`frontend/.env`)**
| Variable | Notes |
|---|---|
| `VITE_API_URL` | default `http://localhost:8000/api` |

## Running tests

```bash
# Simulation engine — no DB, no FastAPI needed, only numpy/pandas/scipy/sklearn:
cd backend
python3 tests/test_simulation_engine.py
# or, if pytest is installed:
pytest tests/ -v
```
20 checks cover: empty-data handling, historical-stats correctness, no
negative revenue/customers, scenario ordering, seeded reproducibility, New
Business Mode confidence penalties, and insufficient-data flags. All pass —
this was verified in the environment this project was built in.

## API summary

```
POST   /api/auth/register            POST   /api/auth/login          GET  /api/auth/me
GET    /api/business                 POST   /api/business            PUT  /api/business/{id}
GET    /api/business-data            POST   /api/business-data       PUT  /api/business-data/{id}   DELETE /api/business-data/{id}
GET    /api/business-data/summary    POST   /api/business-data/upload
POST   /api/simulations/parse-decision
POST   /api/simulations              GET    /api/simulations         GET  /api/simulations/{id}
POST   /api/simulations/{id}/run     GET    /api/simulations/{id}/results
GET    /api/insights
POST   /api/compare
GET    /api/reports/{simulation_id}
GET    /api/notifications            PUT    /api/notifications/{id}/read
GET    /api/health
```
Interactive docs at `/docs` (Swagger) and `/redoc` once the backend is running.

## What was verified in the build sandbox vs. what needs your machine

This project was built in a sandboxed environment **without internet access
or a PostgreSQL server**. That meant:
- ✅ The simulation engine (`app/simulation/`) was actually run here — 20/20
  tests pass, and a live demo (36 months of synthetic data, seed=42,
  10,000 iterations) produced self-consistent, reproducible output.
- ✅ Every backend/frontend file was written against the real target
  dependency versions and reviewed for correctness; frontend JS/JSX passed a
  bracket-balance sanity check.
- ❌ `pip install -r requirements.txt`, `npm install`, `uvicorn app.main:app`,
  and `npm run dev` were **not** run here — there was no network access to
  fetch packages and no Postgres instance to connect to. Please run the
  [Setup](#setup) steps above on your machine (or via Claude Code, which has
  real terminal/network access) to boot the full app and catch any
  integration issues that only surface with real dependencies installed.

## Limitations

- XGBoost is listed as a dependency but not wired into the current engine —
  the percentile-based Monte Carlo + linear demand-elasticity fit was judged
  sufficient for the data sizes this MVP targets (per spec section 38: "do
  not blindly use XGBoost everywhere").
- PDF export for Reports is architected (the `/api/reports/{id}` payload is
  export-ready) but not implemented — add a PDF renderer (e.g. the project's
  `pdf` skill, or WeasyPrint) on top of that endpoint.
- Notifications are stored/read via a real CRUD API but nothing currently
  writes to that table automatically (e.g. "simulation completed"); wiring
  simulation completion to auto-create a notification is a natural next
  step.
- No automated frontend tests yet (backend simulation engine has the test
  suite described above).

## Future improvements
- Auto-create notifications on simulation completion / low confidence / risk changes.
- PDF report export.
- XGBoost-backed demand forecasting once a business accumulates enough history (the engine already gates on `sufficient_for_ml`, so this is a drop-in extension point in `data_analysis.py`).
- Multi-business switching UI polish (currently defaults to the first business).
