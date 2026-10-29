# HotelSense
Multi-horizon hotel occupancy and revenue forecasting with decision support (TSDA project).

Forecasts occupancy, ADR and RevPAR for 7 Qatar accommodation segments at 3-, 6- and 12-month horizons,
compares four models fairly (Seasonal Naive, Holt-Winters, SARIMA, Combination) with a rolling-origin backtest,
and turns the forecasts into planning signals. A FastAPI backend serves everything to a React frontend.

Data: Qatar Tourism via State of Qatar Open Data, licence CC BY (`data/accommodation_data.csv`, 2014-01 to 2025-03).

## Requirements
- Python 3.12 (tested with 3.12.10)
- Node.js 22 and npm (tested with Node 22.14.0, npm 11.5.2)
- Windows commands are shown; on macOS/Linux use `.venv/bin/...` instead of `.venv\Scripts\...`.

## Setup (once)
Run from the project root.
```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r backend/requirements.txt
cd frontend
npm install
cd ..
```
In Git Bash use forward slashes: `.venv/Scripts/python -m pip install -r backend/requirements.txt`.

## Run the app
The generated model files and report tables are committed, so the app runs straight after setup.
Use two terminals and **start the backend first**.

**Terminal 1: backend** (API on http://localhost:8000, interactive docs at http://localhost:8000/docs)
```powershell
cd backend
..\.venv\Scripts\python -m uvicorn main:app --reload --port 8000
```
Wait for `Application startup complete.`

**Terminal 2: frontend** (http://localhost:5173)
```powershell
cd frontend
npm run dev
```
Open http://localhost:5173. The frontend forwards `/api/...` requests to the backend on port 8000.
If the page says "The backend did not respond", the backend is not running or was still starting:
start it (Terminal 1) and reload the page. The page does not retry on its own.

Production build check: `cd frontend` then `npm run build` (output in `frontend/dist/`, not committed).

## Tests and validation
Run from the project root with the backend virtualenv (the backend server does not need to be running).
```powershell
.venv\Scripts\python scripts/05_smoke_test.py            # every segment x metric x horizon + HTTP layer; expect "0 failed"
.venv\Scripts\python scripts/06_test_decision_rules.py   # synthetic tests for the decision rules; expect "0 failed"
.venv\Scripts\python scripts/07_validate_change_rule.py  # rewrites reports/change_rule_validation.md
```

## Rebuild the analysis (optional)
These scripts regenerate the committed reports, tables and model files. Run them in order.
```powershell
.venv\Scripts\python backend/data_loader.py
.venv\Scripts\python scripts/01_data_audit.py         # reports/data_audit.md, data/clean_accommodation.csv
.venv\Scripts\python scripts/02_eda.py                # reports/figures, reports/tables, reports/eda_summary.md
.venv\Scripts\python scripts/03_model_comparison.py   # full SARIMA grid, several minutes: model_comparison.md, tables, sarima_config.json
.venv\Scripts\python scripts/04_build_calibration.py  # backend/models/calibration.json (always re-run after 03)
.venv\Scripts\python scripts/07_validate_change_rule.py
```
`03_model_comparison.py --fast` uses a smaller SARIMA grid for a quick check, but it **overwrites** the
committed full-grid results; re-run without `--fast` (then 04 and 07) before reporting any numbers.

## Project layout
```
data/        raw CSV (semicolon-delimited) + generated clean CSV
backend/     data loading, analysis, models, backtest, calibration, decision rules, service.py, main.py (FastAPI)
  models/    sarima_config.json, calibration.json (generated)
scripts/     01-04 pipeline, 05 smoke test, 06 decision-rule tests, 07 change-rule validation
reports/     data_audit.md, eda_summary.md, model_comparison.md, change_rule_validation.md, figures/, tables/
docs/        scope.md, data_dictionary.md, methodology.md
frontend/    React + Vite (plain JSX), Plotly charts; pages: Overview, Trend explorer, Forecast, Model comparison
```
See `docs/methodology.md` for the evaluation design and `reports/` for results.

## Reading the results honestly
- The simple "same as last year" baseline (Seasonal Naive) is hard to beat, especially for ADR; the app labels
  forecasts that do not beat it by at least 5% as "No better than last year".
- Backtest scores are per horizon (a 6-month horizon pools months 1-6 ahead). "All horizons" figures pool the
  3-, 6- and 12-month results and are labelled separately.
- Decision-support signals are planning prompts for a whole segment, not recommendations for a specific hotel.
  A "supported change" is a prompt to investigate; "inconclusive" does not mean nothing will change. The planning
  thresholds (2 pts occupancy, 3% ADR/RevPAR) are provisional business assumptions, and the 12-month change rule
  has not been validated out of sample (see `reports/change_rule_validation.md`).
- Limitations: COVID (2020-03 to 2021-12) stays in the training data, the 2022 World Cup cannot be forecast,
  and the backtest window (2023-2025) is short.
