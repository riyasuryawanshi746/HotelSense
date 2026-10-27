# HotelSense
Multi-horizon hotel occupancy and revenue forecasting with decision support (TSDA project).

## Setup
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
```

## Phase 1: data audit
```bash
python backend/data_loader.py
python scripts/01_data_audit.py
```
Outputs: `reports/data_audit.md`, `data/clean_accommodation.csv`.

Data: Qatar Tourism via State of Qatar Open Data, licence CC BY.

## Phase 2: EDA, decomposition, stationarity
```bash
python scripts/02_eda.py
```
Outputs: `reports/figures/*.png`, `reports/tables/*.csv`, `reports/eda_summary.md`.
Reusable functions live in `backend/analysis.py` (STL, ADF/KPSS, period summaries).

## Phase 3: model comparison
```bash
python scripts/03_model_comparison.py --fast      # quick check
python scripts/03_model_comparison.py             # full run (several minutes)
```
Outputs: `reports/model_comparison.md`, `reports/tables/*.csv`, `backend/models/sarima_config.json`.
See `docs/methodology.md` for the evaluation design.
