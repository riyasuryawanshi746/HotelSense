"""
04_build_calibration.py  (HotelSense - Phase 4)
Run AFTER scripts/03_model_comparison.py:   python scripts/04_build_calibration.py
Writes backend/models/calibration.json and prints in-sample coverage before/after calibration.
"""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
import calibration as C  # noqa: E402

bt = pd.read_csv(ROOT / "reports" / "tables" / "backtest_predictions.csv", parse_dates=["origin", "target"])
cal = C.build_calibration(bt)
C.CAL_PATH.parent.mkdir(parents=True, exist_ok=True)
C.CAL_PATH.write_text(json.dumps(cal, indent=2))

rows = []
for (seg, met, model), g in bt.groupby(["segment", "metric", "model"]):
    widths = C._band_widths(cal[f"{seg}|{met}|{model}"])
    if widths is None:
        continue
    q = g["step"].map(lambda s: widths[C.band_of(int(s))])
    cov_after = ((g["actual"] - g["pred"]).abs() <= q).mean() * 100
    cov_before = ((g["actual"] >= g["lower"]) & (g["actual"] <= g["upper"])).mean() * 100
    rows.append({"model": model, "before": cov_before, "after": cov_after})
r = pd.DataFrame(rows).groupby("model").mean().round(1)
print("Mean in-sample coverage of the nominal 80% interval (%)")
print(r.to_string())
print(f"\nSaved {C.CAL_PATH}")
