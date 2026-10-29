"""
calibration.py  (HotelSense - Phase 4)
The raw SARIMA / Holt-Winters 80% intervals covered only 61-70% of backtest outcomes (too narrow).
We replace them with EMPIRICAL intervals: half-width = 80th percentile of the absolute backtest
error, by model and horizon band (steps 1-3, 4-6, 7-12). Built by scripts/04_build_calibration.py.

Caveat (state it in the report): calibration uses the same backtest used for evaluation, so coverage
on genuinely new data may be a little lower.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

CAL_PATH = Path(__file__).resolve().parent / "models" / "calibration.json"
BANDS = {"1-3": (1, 3), "4-6": (4, 6), "7-12": (7, 12)}
LEVEL = 0.80
MIN_N = 8


def band_of(step: int) -> str:
    return "1-3" if step <= 3 else "4-6" if step <= 6 else "7-12"


def build_calibration(bt: pd.DataFrame, level: float = LEVEL) -> dict:
    bt = bt.assign(abs_err=(bt["actual"] - bt["pred"]).abs())
    cal = {}
    for (seg, met, model), g in bt.groupby(["segment", "metric", "model"]):
        entry = {}
        for name, (a, b) in BANDS.items():
            e = g[(g["step"] >= a) & (g["step"] <= b)]["abs_err"]
            entry[name] = ({"q": round(float(np.quantile(e, level)), 4), "n": int(len(e))}
                           if len(e) >= MIN_N else None)
        cal[f"{seg}|{met}|{model}"] = entry
    return cal


def _band_widths(entry: dict) -> dict | None:
    """Fill missing bands and force widths to be non-decreasing with horizon."""
    qs = [entry[b]["q"] if entry.get(b) else np.nan for b in BANDS]
    if all(np.isnan(qs)):
        return None
    qs = pd.Series(qs).bfill().ffill().cummax().tolist()
    return dict(zip(BANDS, qs))


MIN_N_AVG = 6  # fewest backtest origins we accept for a horizon-average quantile


def average_error_quantile(bt: pd.DataFrame, h: int, level: float = LEVEL, min_n: int = MIN_N_AVG):
    """
    Uncertainty of the AVERAGE over forecast months 1..h (used by the decision rules, not for the chart band).
    bt: backtest rows of ONE segment / metric / model (columns origin, step, avail, actual, pred).
    For every origin that has h months of future data, average its h errors, then take the `level`
    quantile of the absolute averages. Using whole origins keeps the real correlation between monthly
    errors (no independence / sqrt(h) assumption). Returns (q, n_origins); q is None if n < min_n.
    """
    sub = bt[(bt["avail"] >= h) & (bt["step"] <= h)]
    err = (sub["actual"] - sub["pred"]).groupby(sub["origin"])
    complete = err.count() == h  # only origins with a finite error for every one of the h steps
    avg_err = err.mean()[complete].dropna()
    n = int(len(avg_err))
    if n < min_n:
        return None, n
    return float(np.quantile(avg_err.abs(), level)), n


def calibrated_interval(fc, cal: dict, segment: str, metric: str, model: str, h: int):
    """Return (lower, upper, method) for the first h steps of forecast `fc`."""
    mean = fc.mean.iloc[:h]
    entry = cal.get(f"{segment}|{metric}|{model}")
    widths = _band_widths(entry) if entry else None
    if widths is None:
        return fc.lower.iloc[:h], fc.upper.iloc[:h], "model-based (uncalibrated)"
    q = np.array([widths[band_of(i + 1)] for i in range(h)])
    hi = 100.0 if metric == "occupancy" else None
    lower = pd.Series(np.clip(mean.to_numpy() - q, 0.0, hi), index=mean.index)
    upper = pd.Series(np.clip(mean.to_numpy() + q, 0.0, hi), index=mean.index)
    return lower, upper, "empirical 80% interval from backtest errors"
