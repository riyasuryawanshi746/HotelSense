"""
evaluation.py  (HotelSense - Phase 3)
Rolling-origin (expanding-window) backtest and error metrics.

For each origin month T (starting at `first_origin`, every `step` months):
  - train on data up to and including T only
  - forecast the next h <= 12 months
  - compare with what actually happened
Horizon-h metrics pool the first h steps of every origin that has h months of
future data available. All models are scored on exactly the same (origin, step) cells.
"""
import numpy as np
import pandas as pd
import forecasting as F

BASELINE = "Seasonal Naive"
HORIZONS = (3, 6, 12)


def _months_between(a: pd.Timestamp, b: pd.Timestamp) -> int:
    return (b.year - a.year) * 12 + (b.month - a.month)


def rolling_origin_backtest(actual: pd.Series, adjusted: pd.Series, metric: str,
                            first_origin, step: int = 2, max_h: int = 12,
                            sarima_cfg: dict | None = None, fast: bool = False) -> pd.DataFrame:
    last = actual.index[-1]
    cand = adjusted.index[(adjusted.index >= pd.Timestamp(first_origin)) & (adjusted.index < last)]
    rows = []
    for origin in cand[::step]:
        avail = _months_between(origin, last)
        h = min(max_h, avail)
        train = adjusted.loc[:origin]
        fcs = F.forecast_all(train, h, metric, sarima_cfg, fast=fast)
        for name, fc in fcs.items():
            for i, t in enumerate(fc.mean.index):
                rows.append({"origin": origin, "target": t, "step": i + 1, "avail": avail,
                             "model": name, "actual": float(actual.loc[t]),
                             "pred": float(fc.mean.iloc[i]),
                             "lower": float(fc.lower.iloc[i]), "upper": float(fc.upper.iloc[i])})
    return pd.DataFrame(rows)


def metrics_table(bt: pd.DataFrame, horizons=HORIZONS) -> pd.DataFrame:
    out = []
    for h in horizons:
        sub = bt[(bt["avail"] >= h) & (bt["step"] <= h)]
        if sub.empty:
            continue
        piv = sub.pivot_table(index=["origin", "step"], columns="model", values="pred")
        keys = piv.dropna().reset_index()[["origin", "step"]]  # cells where every model produced a forecast
        sub = sub.merge(keys, on=["origin", "step"])
        for m, g in sub.groupby("model"):
            e = g["actual"] - g["pred"]
            out.append({"model": m, "horizon": h,
                        "MAE": e.abs().mean(),
                        "RMSE": float(np.sqrt((e ** 2).mean())),
                        "MAPE": (e.abs() / g["actual"].abs()).mean() * 100,
                        "coverage80": ((g["actual"] >= g["lower"]) & (g["actual"] <= g["upper"])).mean() * 100,
                        "n": len(g), "n_origins": g["origin"].nunique()})
    return pd.DataFrame(out)


def add_skill(res: pd.DataFrame) -> pd.DataFrame:
    """Skill vs the seasonal-naive baseline: +20 means 20% lower RMSE than the baseline."""
    keys = ["segment", "metric", "horizon"]
    base = res[res["model"] == BASELINE].set_index(keys)["RMSE"].rename("base_rmse")
    res = res.join(base, on=keys)
    res["skill_vs_snaive_pct"] = (1 - res["RMSE"] / res["base_rmse"]) * 100
    return res.drop(columns="base_rmse")


def select_best(res: pd.DataFrame, min_skill: float = 5.0) -> pd.DataFrame:
    """Lowest RMSE per (segment, metric, horizon). `beats_baseline` needs >= min_skill % gain."""
    keys = ["segment", "metric", "horizon"]
    idx = res.groupby(keys)["RMSE"].idxmin()
    best = res.loc[idx].rename(columns={"model": "best_model"}).reset_index(drop=True)
    best["beats_baseline"] = (best["best_model"] != BASELINE) & (best["skill_vs_snaive_pct"] >= min_skill)
    return best
