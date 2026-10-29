"""
service.py  (HotelSense - Phase 4)
All application logic, independent of the web framework (so it can be tested without FastAPI).
main.py only wraps these functions in HTTP endpoints.
"""
from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

import analysis as A
import calibration as C
import decision_support as D
import forecasting as F
from data_loader import AGGREGATE_SEGMENT, METRICS, get_series, list_segments, load_clean
from preprocessing import prepare

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "reports" / "tables"
HORIZONS = (3, 6, 12)
METRIC_LABELS = {"occupancy": "Occupancy rate (%)", "adr": "ADR (QAR)", "revpar": "RevPAR (QAR)"}


class ServiceError(Exception):
    def __init__(self, msg: str, status: int = 400):
        super().__init__(msg)
        self.status = status


# ------------------------------------------------------------------ helpers
def _num(x, nd=2):
    if x is None:
        return None
    x = float(x)
    return None if np.isnan(x) else round(x, nd)


def _list(s, nd=2):
    return [_num(v, nd) for v in s]


def _dates(idx):
    return [d.strftime("%Y-%m") for d in idx]


def _tbl(df: pd.DataFrame) -> dict:
    return {str(i): {str(c): _num(v, 1) for c, v in r.items()} for i, r in df.iterrows()}


@lru_cache(maxsize=1)
def store() -> dict:
    needed = ("model_comparison.csv", "best_models.csv", "backtest_predictions.csv")
    missing = [n for n in needed if not (TABLES / n).exists()]
    if missing:
        raise ServiceError(f"Missing {missing}. Run scripts/03_model_comparison.py first.", 503)
    cal = json.loads(C.CAL_PATH.read_text()) if C.CAL_PATH.exists() else {}
    return {"df": load_clean(),
            "res": pd.read_csv(TABLES / "model_comparison.csv"),
            "best": pd.read_csv(TABLES / "best_models.csv"),
            "bt": pd.read_csv(TABLES / "backtest_predictions.csv", parse_dates=["origin", "target"]),
            "cal": cal, "cfg": F.load_config()}


def _check(segment=None, metric=None, horizon=None):
    s = store()
    if segment is not None and segment not in list_segments(s["df"]):
        raise ServiceError(f"Unknown segment '{segment}'", 404)
    if metric is not None and metric not in METRICS:
        raise ServiceError(f"metric must be one of {list(METRICS)}", 400)
    if horizon is not None and horizon not in HORIZONS:
        raise ServiceError(f"horizon must be one of {list(HORIZONS)}", 400)


def _best_row(segment, metric, horizon) -> dict:
    b = store()["best"]
    r = b[(b.segment == segment) & (b.metric == metric) & (b.horizon == horizon)]
    if r.empty:
        raise ServiceError(f"No evaluation available for {segment} / {metric} / {horizon}m", 404)
    return r.iloc[0].to_dict()


@lru_cache(maxsize=64)
def _future(segment: str, metric: str) -> dict:
    """12-month forecasts from every model, fitted on all data. Cached per series."""
    s = store()
    return F.forecast_future(s["df"], segment, metric, 12, config=s["cfg"])


def _calibrated(segment, metric, model, h):
    fcs = _future(segment, metric)
    if model not in fcs:
        model = "Seasonal Naive"
    fc = fcs[model]
    lo, up, method = C.calibrated_interval(fc, store()["cal"], segment, metric, model, h)
    return pd.DataFrame({"mean": fc.mean.iloc[:h], "lower": lo, "upper": up}), model, method


# ------------------------------------------------------------------ endpoints' logic
def meta() -> dict:
    df = store()["df"]
    return {"segments": list_segments(df), "aggregate_segment": AGGREGATE_SEGMENT,
            "metrics": [{"id": m, "label": METRIC_LABELS[m]} for m in METRICS],
            "horizons": list(HORIZONS), "first_date": df.date.min().strftime("%Y-%m"),
            "last_date": df.date.max().strftime("%Y-%m")}


def history(segment: str, metric: str) -> dict:
    _check(segment, metric)
    s = store()
    ser = get_series(s["df"], segment, metric)
    _, adj = prepare(s["df"], segment, metric)
    nc = adj[~((adj.index >= A.COVID_START) & (adj.index <= A.COVID_END))]
    prof = nc.groupby(nc.index.month).mean()
    last12, prev12 = ser.iloc[-12:].mean(), ser.iloc[-24:-12].mean()
    return {"segment": segment, "metric": metric, "label": METRIC_LABELS[metric],
            "dates": _dates(ser.index), "values": _list(ser),
            "stats": {"n": int(len(ser)), "mean": _num(ser.mean()), "std": _num(ser.std()),
                      "min": _num(ser.min()), "max": _num(ser.max()),
                      "latest_date": ser.index[-1].strftime("%Y-%m"), "latest": _num(ser.iloc[-1]),
                      "last12_mean": _num(last12), "prev12_mean": _num(prev12),
                      "yoy_change_pct": _num((last12 / prev12 - 1) * 100)},
            "seasonal_profile": {"months": list(range(1, 13)), "values": _list(prof),
                                 "note": "Monthly mean excluding COVID months (2020-03 to 2021-12)"},
            "events": [{"label": "COVID-19", "start": "2020-03", "end": "2021-12"},
                       {"label": "FIFA World Cup", "start": "2022-11", "end": "2022-12"}]}


def decomposition(segment: str, metric: str) -> dict:
    _check(segment, metric)
    _, adj = prepare(store()["df"], segment, metric)
    res = A.decompose(adj)
    return {"segment": segment, "metric": metric, "dates": _dates(adj.index),
            "observed": _list(adj), "trend": _list(res.trend), "seasonal": _list(res.seasonal),
            "resid": _list(res.resid), "strength": A.strength(res),
            "stationarity": A.stationarity_report(adj),
            "note": "STL (period 12, robust). ADR/RevPAR use the World-Cup-adjusted series."}


def forecast(segment: str, metric: str, horizon: int, model: str = "best") -> dict:
    _check(segment, metric, horizon)
    s = store()
    row = _best_row(segment, metric, horizon)
    fcs = _future(segment, metric)
    if model != "best" and model not in fcs:
        raise ServiceError(f"model must be 'best' or one of {list(fcs)}", 400)
    best = row["best_model"] if row["best_model"] in fcs else "Seasonal Naive"
    models, method = {}, ""
    for name in fcs:
        fr, _, method = _calibrated(segment, metric, name, horizon)
        models[name] = {"dates": _dates(fr.index), "mean": _list(fr["mean"]),
                        "lower": _list(fr["lower"]), "upper": _list(fr["upper"])}
    ser = get_series(s["df"], segment, metric)
    return {"segment": segment, "metric": metric, "label": METRIC_LABELS[metric], "horizon": horizon,
            "last_observed": ser.index[-1].strftime("%Y-%m"),
            "best_model": best, "chosen_model": best if model == "best" else model,
            "models": models, "interval_method": method,
            "history": {"dates": _dates(ser.index[-36:]), "values": _list(ser.iloc[-36:])},
            "reliability": D.reliability(row)}


def evaluation(segment: str, metric: str, horizon: int) -> dict:
    _check(segment, metric, horizon)
    s = store()
    res = s["res"][(s["res"].segment == segment) & (s["res"].metric == metric)]
    best = s["best"][(s["best"].segment == segment) & (s["best"].metric == metric)]
    bt = s["bt"][(s["bt"].segment == segment) & (s["bt"].metric == metric) & (s["bt"].step == horizon)]
    cols = ["model", "horizon", "MAE", "RMSE", "MAPE", "coverage80", "skill_vs_snaive_pct", "n", "n_origins"]
    table = [{k: (_num(v, 3) if isinstance(v, (float, np.floating)) else (v.item() if hasattr(v, "item") else v))
              for k, v in r.items()} for r in res[cols].to_dict("records")]
    dates = sorted(bt["target"].unique())
    actual = bt.drop_duplicates("target").set_index("target")["actual"].reindex(dates)
    preds = {m: _list(g.set_index("target")["pred"].reindex(dates)) for m, g in bt.groupby("model")}
    return {"segment": segment, "metric": metric, "horizon": horizon, "table": table,
            "best": {int(r.horizon): {"model": r.best_model, "skill_vs_snaive_pct": _num(r.skill_vs_snaive_pct),
                                      "beats_baseline": bool(r.beats_baseline)} for r in best.itertuples()},
            "backtest": {"description": f"Forecasts made {horizon} months ahead vs what happened",
                         "dates": [pd.Timestamp(d).strftime("%Y-%m") for d in dates],
                         "actual": _list(actual), "models": preds},
            "note": "Raw model intervals under-cover (see coverage80); the app shows calibrated intervals."}


def model_summary() -> dict:
    s = store()
    best, res = s["best"], s["res"]
    wins = best.groupby(["horizon", "best_model"]).size().unstack(fill_value=0).astype(float)
    skill = (res[res.model != "Seasonal Naive"].groupby(["horizon", "model"])["skill_vs_snaive_pct"]
             .median().unstack())
    cov = res.groupby(["horizon", "model"])["coverage80"].mean().unstack()
    mape = res.groupby(["metric", "model"])["MAPE"].median().unstack()
    beats = best.groupby("metric")["beats_baseline"].mean().mul(100).to_frame("pct_series_beating_baseline")
    return {"wins_by_horizon": _tbl(wins), "median_skill_vs_baseline_pct": _tbl(skill),
            "raw_interval_coverage_pct": _tbl(cov), "median_mape_by_metric": _tbl(mape),
            "pct_series_where_model_beats_baseline": _tbl(beats)}


def overview(metric: str = "occupancy") -> dict:
    _check(metric=metric)
    s = store()
    rows = []
    for seg in list_segments(s["df"]):
        ser = get_series(s["df"], seg, metric)
        l12, p12 = ser.iloc[-12:].mean(), ser.iloc[-24:-12].mean()
        b = s["best"][(s["best"].segment == seg) & (s["best"].metric == metric) & (s["best"].horizon == 6)]
        rows.append({"segment": seg, "latest_date": ser.index[-1].strftime("%Y-%m"), "latest": _num(ser.iloc[-1]),
                     "last12_mean": _num(l12), "prev12_mean": _num(p12),
                     "change_pct": _num((l12 / p12 - 1) * 100),
                     "best_model_6m": None if b.empty else b.iloc[0]["best_model"],
                     "beats_baseline_6m": None if b.empty else bool(b.iloc[0]["beats_baseline"])})
    return {"metric": metric, "label": METRIC_LABELS[metric], "segments": rows}


def decision(segment: str, metric: str, horizon: int) -> dict:
    _check(segment, metric, horizon)
    s = store()
    frames, rows = {}, {}
    for m in METRICS:
        row = _best_row(segment, m, horizon)
        frames[m], used, _ = _calibrated(segment, m, row["best_model"], horizon)
        row["best_model"] = used
        rows[m] = row
    hist = {m: get_series(s["df"], segment, m) for m in METRICS}
    last = hist[metric].index[-1]
    out = D.build_decision(segment, metric, horizon, hist, frames, rows, last)
    out["models_used"] = {m: rows[m]["best_model"] for m in METRICS}
    return out
