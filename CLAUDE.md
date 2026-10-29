# HotelSense - guide for Claude Code

University Time Series Data Analysis (TSDA) project by two students: multi-horizon hotel occupancy,
ADR and RevPAR forecasting with decision support, on Qatar Tourism accommodation data.
Both students must be able to explain every line in a viva, so **keep code plain, commented and simple**.

## Hard rules
- No database, authentication, cloud infrastructure, deep learning, TypeScript or UI framework.
- Never hard-code forecast numbers, metrics or insight text in the frontend: everything comes from the API.
- Do not remove the honest "low confidence / no better than last year" signalling.
- Do not change API response shapes without agreement; prefer fixing the frontend.
- Do not edit `data/accommodation_data.csv`.
- Keep dependencies minimal. Show a diff or explain before large changes; ask when something is ambiguous.
- If a Python run fails because of the environment, give the exact command to fix it instead of guessing.

## Commands (Windows; Git Bash paths shown, PowerShell uses `.venv\Scripts\...`)
```bash
# one-time setup
python -m venv .venv
.venv/Scripts/python -m pip install -r backend/requirements.txt
cd frontend && npm install

# pipeline (run from the repo root, in order)
.venv/Scripts/python backend/data_loader.py
.venv/Scripts/python scripts/01_data_audit.py         # reports/data_audit.md, data/clean_accommodation.csv
.venv/Scripts/python scripts/02_eda.py                # figures, tables, reports/eda_summary.md
.venv/Scripts/python scripts/03_model_comparison.py   # full SARIMA grid, several minutes (--fast for a quick check)
.venv/Scripts/python scripts/04_build_calibration.py  # backend/models/calibration.json
.venv/Scripts/python scripts/05_smoke_test.py         # every segment x metric x horizon + HTTP layer (expect 0 failed)
.venv/Scripts/python scripts/06_test_decision_rules.py  # synthetic tests for decision rules + frontend label keys
.venv/Scripts/python scripts/07_validate_change_rule.py # reports/change_rule_validation.md (out-of-sample check of R1)

# run the app (two terminals)
cd backend && ../.venv/Scripts/python -m uvicorn main:app --reload --port 8000   # API docs: http://localhost:8000/docs
cd frontend && npm run dev                                                        # http://localhost:5173
cd frontend && npm run build                                                      # production build check
```
`.claude/launch.json` defines `backend` and `frontend` configurations for the desktop app's Browser pane.
Re-run `04_build_calibration.py` after every `03_model_comparison.py` run. `03` re-selects SARIMA orders
automatically if the cached `sarima_config.json` was built with a different grid (`"_meta": {"grid": ...}`).

## Data
`data/accommodation_data.csv`, **semicolon-delimited**, State of Qatar Open Data (CC BY).
945 rows = 7 segments x 135 months (2014-01 to 2025-03). Segments: 1 & 2 Star Hotels+, 3 Star Hotels+,
4 Star Hotels+, 5 Star Hotels+, Deluxe Apartments+, Standard Apartments+, Qatar+ (national total, not an exact sum).
Metrics used: occupancy (%), ADR (QAR), RevPAR (QAR). Future forecasts start 2025-04.
- No missing months, duplicates or nulls.
- 3 occupancy values > 100 (1 & 2 Star Hotels+: 2024-01, 2024-11, 2025-02): kept as published, capped at 100 for modelling.
- FIFA World Cup (2022-11, 2022-12) ADR/RevPAR spikes are real: imputed **only in the training series** for ADR/RevPAR; scoring always uses published values.
- COVID (2020-03 to 2021-12) is a structural break and stays in training data (documented limitation).

## Architecture
```
data/            raw CSV (+ generated clean_accommodation.csv)
backend/
  data_loader.py       the single place data is loaded and cleaned
  preprocessing.py     actual vs World-Cup-adjusted series
  analysis.py          STL decomposition, ADF/KPSS, trend/seasonal strength
  eda.py               dataset summary, quality checks (same as 01_data_audit), EDA tables, computed key findings
  forecasting.py       4 models + forecast_future()
  evaluation.py        rolling-origin backtest, metrics, skill, best-model selection
  calibration.py       empirical 80% intervals from backtest errors
  decision_support.py  rule-based planning signals (R1-R5, documented at the top of the file)
  service.py           all app logic, framework-independent (tested by 05_smoke_test.py)
  main.py              thin FastAPI wrapper around service.py
  models/              sarima_config.json, calibration.json (generated, committed)
scripts/         01-05 pipeline scripts, 06 decision-rule tests, 07 change-rule validation (see Commands)
reports/         data_audit.md, eda_summary.md, model_comparison.md, figures/, tables/ (backend reads tables/)
docs/            scope.md, data_dictionary.md, methodology.md
frontend/        React 18 + Vite, plain JSX, Plotly (plotly.js-basic-dist-min), react-router-dom
  src/api.js           fetch wrapper + useApi() hook; the only place that calls the backend
  src/selection.jsx    shared segment/metric/horizon state + /api/meta
  src/format.js        number formatting, model colours
  src/components/      Chart (Plotly wrapper), Controls, DecisionPanel, Eda (Overview sections), ui (Card, Badge, Async...)
  src/pages/           Overview, TrendExplorer, Forecast, ModelComparison
```
Vite proxies `/api` to `http://127.0.0.1:8000`, so the browser uses a single origin in development.

### API (all GET; `segment` must be URL-encoded because names contain `&` and `+`)
| Endpoint | Params | Used by |
|---|---|---|
| `/api/health` | – | – |
| `/api/meta` | – | segments, metrics, horizons, date range |
| `/api/overview` | metric | Overview (latest 12 months by segment) |
| `/api/eda` | metric | Overview (dataset at a glance, key findings, EDA charts; `backend/eda.py`) |
| `/api/history` | segment, metric | Trend explorer (history, stats, seasonal profile, events) |
| `/api/decomposition` | segment, metric | Trend explorer (STL, strength, ADF/KPSS) |
| `/api/forecast` | segment, metric, horizon (3/6/12), model (`best` or a name) | Forecast |
| `/api/evaluation` | segment, metric, horizon | Model comparison |
| `/api/model-summary` | – | Model comparison (all 21 series); `scope` states each field's scope (see below) |
| `/api/decision` | segment, metric, horizon | Forecast (DecisionPanel) |
Errors: 400 bad metric/horizon, 404 unknown segment, 503 missing report tables; body `{"detail": "..."}`.

### Metric scopes (keep API fields and UI labels in agreement)
A "horizon h" result always pools forecast steps 1..h (6-month horizon = months 1-6 ahead). UI labels come from
`frontend/src/format.js`: `horizonLabel(h)` -> "6-month horizon", `ALL_HORIZONS` -> "All horizons".
`/api/model-summary` fields:
- By horizon (keyed "3"/"6"/"12"): `wins_by_horizon`, `median_skill_vs_baseline_pct`, `raw_interval_coverage_pct` (mean),
  `median_mape_by_metric_and_horizon` ({h: {metric: {model: MAPE}}}), `pct_series_where_model_beats_baseline_by_horizon` ({h: {metric: pct}}).
- All horizons (median/share over 7 segments x 3 horizons): `median_mape_by_metric`, `pct_series_where_model_beats_baseline`.
  Never show these under a single-horizon label; if a horizon-specific value is missing, show "not available" instead.
- The two `..._by_horizon` fields and `scope` were added (additive, no existing field changed); `05_smoke_test.py` checks them.
Elsewhere: `/api/evaluation` `table` rows and `reliability.mape` are per horizon; the `/api/evaluation` `backtest` chart is
step h only (not 1..h); `/api/overview` `best_model_6m` is the 6-month horizon.

## Key design decisions (do not silently change)
- **Models:** Seasonal Naive (baseline); Holt-Winters (additive ETS via statsmodels `ETSModel`, optional damped
  trend chosen by AICc); SARIMA (order chosen from a grid by validation RMSE on the last 12 months of the
  training window, because ADF and KPSS disagree due to level shifts); Combination (mean of Holt-Winters and SARIMA).
- **Evaluation:** rolling-origin, expanding window; first training cut-off 2022-12, a new origin every 2 months,
  forecasts up to 12 months. Horizon-h metrics pool steps 1..h from origins that have h months of future data;
  all models are scored on identical cells. Metrics: MAE, RMSE, MAPE, raw 80% interval coverage, and
  skill vs Seasonal Naive = 1 - RMSE / RMSE_snaive. A winner only counts as a real improvement if skill >= 5%.
- Post-COVID-only training was rejected: only 12 months exist between 2022-01 and the first cut-off.
- **Intervals:** raw model intervals under-cover (about 61-70% for a nominal 80%), so the app shows calibrated
  intervals: half-width = 80th percentile of absolute backtest error per model and horizon band (1-3, 4-6, 7-12),
  forced non-decreasing, clipped to 0-100 for occupancy. Caveat for the report: calibration uses the same
  backtest that is used for evaluation, so real coverage may be a little lower.
- **Decision support, R1 (level change):** compares the forecast AVERAGE over the h months with the published
  average of the same calendar months last year. Its uncertainty is the 80th percentile of |mean error over steps
  1..h| across rolling-origin backtest origins for that series and model (`calibration.average_error_quantile`),
  which keeps the real correlation between monthly errors (no sqrt(h) assumption). Status is
  `increase`/`decrease` only if |change| > that uncertainty AND |change| >= `MATERIAL` (2 pts occupancy, 3% ADR/RevPAR:
  PROVISIONAL business assumptions, not statistically validated or optimised; do not change without agreement);
  else `inconclusive` with a `reason`. Fewer than 6 usable origins -> falls back to
  the wider single-month half-width. The chart's calibrated per-month band is unchanged.
  Before this (until 2026-10) R1 compared the change of an average with the single-month half-width, which
  overstated the uncertainty of the average (the measured width is a median 0.3-0.9x of it per metric and
  horizon); it fired 0/63 times, now 2/63. A Seasonal Naive forecast equals last year by construction,
  so it is always `inconclusive` (`baseline_forecast`). `reports/change_rule_validation.md` (script 07): out-of-sample
  coverage 77.8% (3-month horizon) and 90.1% (6-month) for a nominal 80%; directional accuracy of "supported" calls
  is weak and based on few calls; the 12-month rule is untested out of sample (too few eligible origins). So the UI
  words supported changes as prompts to investigate, never as pricing recommendations, and "inconclusive" does
  not mean "no change".
- **Decision support, other rules:** capacity / soft-demand flags use each segment's own P90 / P10 occupancy
  (excluding COVID months); the pricing signal combines the R1 statuses of occupancy, ADR and RevPAR and only
  prompts a review (never a price move from occupancy alone); a reliability label says whether
  the winning model beats "same as last year" by >= 5%. Everything is framed as planning signals for a
  segment, never as decisions for a specific hotel.

## Current results (full SARIMA grid, from reports/model_comparison.md and /api/model-summary)
Figures below are "3-month / 6-month / 12-month horizon" unless marked "All horizons".
- Wins (lowest RMSE), 3 / 6 / 12-month horizon: Combination 10 / 9 / 8, Seasonal Naive 8 / 8 / 8, SARIMA 2 / 3 / 4, Holt-Winters 1 / 1 / 1.
- Median skill vs Seasonal Naive, 3 / 6 / 12-month horizon: Combination +7.2 / +4.3 / +5.4%; Holt-Winters -0.2 / -5.0 / -2.2%; SARIMA -1.7 / -2.5 / -0.5%.
- The winner beats the baseline by >= 5% in only 52 / 48 / 52% of the 21 series (3 / 6 / 12-month horizon).
- By metric, winner beats the baseline by >= 5%: occupancy 86 / 86 / 86%, RevPAR 57 / 43 / 57%, ADR 14 / 14 / 14%
  of segments (3 / 6 / 12-month horizon); All horizons: occupancy 86%, RevPAR 52%, ADR 14%. ADR is essentially "same as last year".
- Median MAPE, occupancy, 3-month horizon: Holt-Winters 12.0%, Combination 12.2%, Seasonal Naive 13.3%, SARIMA 14.9%.
  The All-horizons occupancy medians (Combination 12.4%, Holt-Winters 12.5%, Seasonal Naive 14.6%, SARIMA 15.2%) are
  not any single horizon's values.
- These numbers supersede an earlier fast-grid run (where Seasonal Naive won most series). Re-check them after any re-run;
  the UI reads them live from the API, but CLAUDE.md and the report text do not.

## Known limitations / things to mention in the report
- COVID break in training data; World Cup not forecastable; segment-level data only.
- Calibration and evaluation share the same backtest.
- Only 13 backtest origins (2022-12 onwards), so metrics per series are based on few cells (see the `n` column).
