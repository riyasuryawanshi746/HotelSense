"""
forecasting.py  (HotelSense - Phase 3)
Four forecasters with a common interface, all returning a point forecast and an
80% prediction interval:

  Seasonal Naive : value of the same month last year; interval from empirical
                   seasonal-difference errors (robust, widens each year).
  Holt-Winters   : additive ETS with additive error, additive seasonality and
                   either no trend or a damped additive trend (picked by AICc).
                   Equivalent to (damped) additive Holt-Winters, with analytic intervals.
  SARIMA         : SARIMAX, order picked by out-of-sample validation (last 12 months of
                   the training window) from a small grid. Differencing is chosen by
                   validation rather than unit-root tests because ADF/KPSS disagree
                   (structural breaks).
  Combination    : simple average of Holt-Winters and SARIMA (intervals averaged too,
                   which is approximate).

All functions take `train` only. Nothing here can see future data.
"""
from __future__ import annotations
import json
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm
from statsmodels.tsa.exponential_smoothing.ets import ETSModel
from statsmodels.tsa.statespace.sarimax import SARIMAX

SEASON = 12
ALPHA = 0.20  # 80% prediction interval
MODELS = ("Seasonal Naive", "Holt-Winters", "SARIMA", "Combination")
CONFIG_PATH = Path(__file__).resolve().parent / "models" / "sarima_config.json"


@dataclass
class Forecast:
    mean: pd.Series
    lower: pd.Series
    upper: pd.Series

    def frame(self) -> pd.DataFrame:
        return pd.DataFrame({"mean": self.mean, "lower": self.lower, "upper": self.upper})


# ---------------------------------------------------------------- helpers
def future_index(train: pd.Series, h: int) -> pd.DatetimeIndex:
    return pd.date_range(train.index[-1] + pd.offsets.MonthBegin(1), periods=h, freq="MS")


def _pack(train, h, mean, lower, upper, metric) -> Forecast:
    idx = future_index(train, h)
    hi = 100.0 if metric == "occupancy" else None
    def s(x):
        return pd.Series(np.clip(np.asarray(x, dtype=float), 0.0, hi), index=idx)
    return Forecast(s(mean), s(lower), s(upper))


# ---------------------------------------------------------------- Seasonal Naive
def seasonal_naive(train: pd.Series, h: int, metric: str, alpha: float = ALPHA) -> Forecast:
    last = train.iloc[-SEASON:].to_numpy()
    mean = np.array([last[i % SEASON] for i in range(h)])
    d = train.diff(SEASON).dropna().iloc[-36:].to_numpy()
    sd = 1.4826 * np.median(np.abs(d - np.median(d)))
    z = norm.ppf(1 - alpha / 2)
    k = np.ceil((np.arange(h) + 1) / SEASON)
    w = z * sd * np.sqrt(k)
    return _pack(train, h, mean, mean - w, mean + w, metric)


# ---------------------------------------------------------------- Holt-Winters (ETS)
def fit_ets(train: pd.Series):
    best = None
    for trend, damped in ((None, False), ("add", True)):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                res = ETSModel(train, error="add", trend=trend, damped_trend=damped,
                               seasonal="add", seasonal_periods=SEASON,
                               initialization_method="estimated").fit(disp=False)
            if np.isfinite(res.aicc) and (best is None or res.aicc < best.aicc):
                best = res
        except Exception:
            continue
    return best


def holt_winters(train: pd.Series, h: int, metric: str, alpha: float = ALPHA) -> Forecast:
    res = fit_ets(train)
    if res is None:
        raise RuntimeError("Holt-Winters failed to fit")
    sf = res.get_prediction(start=len(train), end=len(train) + h - 1).summary_frame(alpha=alpha)
    lo = [c for c in sf.columns if "lower" in c][0]
    up = [c for c in sf.columns if "upper" in c][0]
    return _pack(train, h, sf["mean"], sf[lo], sf[up], metric)


# ---------------------------------------------------------------- SARIMA
def _grid(fast: bool):
    if fast:
        orders = [(1, d, q) for d in (0, 1) for q in (0, 1)]
        sorders = [(1, 0, 0), (0, 1, 1)]
    else:
        orders = [(p, d, q) for p in (0, 1, 2) for d in (0, 1) for q in (0, 1)]
        sorders = [(1, 0, 0), (1, 0, 1), (0, 1, 1), (1, 1, 0)]
    return [(o, (*so, SEASON)) for o in orders for so in sorders]


def _fit_sarima(y: pd.Series, order, sorder):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return SARIMAX(y, order=order, seasonal_order=sorder,
                       enforce_stationarity=False,
                       enforce_invertibility=False).fit(disp=False, maxiter=200)


def select_sarima(train: pd.Series, fast: bool = False, val: int = 12) -> dict:
    """Pick (order, seasonal_order) by RMSE on the last `val` months of `train`."""
    fit_part, val_part = train.iloc[:-val], train.iloc[-val:].to_numpy()
    best = None
    for order, sorder in _grid(fast):
        try:
            r = _fit_sarima(fit_part, order, sorder)
            fc = np.asarray(r.get_forecast(val).predicted_mean)
            rmse = float(np.sqrt(np.mean((val_part - fc) ** 2)))
        except Exception:
            continue
        if np.isfinite(rmse) and (best is None or rmse < best["val_rmse"]):
            best = {"order": list(order), "seasonal_order": list(sorder),
                    "val_rmse": round(rmse, 3)}
    if best is None:  # safe default
        best = {"order": [1, 0, 0], "seasonal_order": [0, 1, 1, SEASON], "val_rmse": None}
    return best


def sarima(train: pd.Series, h: int, metric: str, order, sorder, alpha: float = ALPHA) -> Forecast:
    r = _fit_sarima(train, tuple(order), tuple(sorder))
    pf = r.get_forecast(h)
    ci = np.asarray(pf.conf_int(alpha=alpha))
    return _pack(train, h, np.asarray(pf.predicted_mean), ci[:, 0], ci[:, 1], metric)


# ---------------------------------------------------------------- combination + dispatcher
def combine(a: Forecast, b: Forecast) -> Forecast:
    return Forecast((a.mean + b.mean) / 2, (a.lower + b.lower) / 2, (a.upper + b.upper) / 2)


def forecast_all(train: pd.Series, h: int, metric: str, sarima_cfg: dict | None = None,
                 alpha: float = ALPHA, fast: bool = False) -> dict[str, Forecast]:
    """Run every model on `train`. A model that fails is simply missing from the result."""
    out: dict[str, Forecast] = {"Seasonal Naive": seasonal_naive(train, h, metric, alpha)}
    try:
        out["Holt-Winters"] = holt_winters(train, h, metric, alpha)
    except Exception as e:
        warnings.warn(f"Holt-Winters failed: {e}")
    try:
        cfg = sarima_cfg or select_sarima(train, fast)
        out["SARIMA"] = sarima(train, h, metric, cfg["order"], cfg["seasonal_order"], alpha)
    except Exception as e:
        warnings.warn(f"SARIMA failed: {e}")
    if "Holt-Winters" in out and "SARIMA" in out:
        out["Combination"] = combine(out["Holt-Winters"], out["SARIMA"])
    return out


# ---------------------------------------------------------------- config persistence
def config_key(segment: str, metric: str) -> str:
    return f"{segment}|{metric}"


def load_config(path: Path = CONFIG_PATH) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


def save_config(cfg: dict, path: Path = CONFIG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg, indent=2))


# ---------------------------------------------------------------- production entry point
def forecast_future(df: pd.DataFrame, segment: str, metric: str, horizon: int,
                    config: dict | None = None, alpha: float = ALPHA) -> dict[str, Forecast]:
    """
    Forecast beyond the last observed month using ALL data (World-Cup-adjusted for
    ADR/RevPAR). Uses the SARIMA spec validated in the backtest; this is what the API calls.
    """
    from preprocessing import prepare
    _, adjusted = prepare(df, segment, metric)
    config = load_config() if config is None else config
    cfg = config.get(config_key(segment, metric))
    return forecast_all(adjusted, horizon, metric, cfg, alpha)
