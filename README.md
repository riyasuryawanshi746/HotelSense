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
