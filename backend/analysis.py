"""
analysis.py  (HotelSense - Phase 2)
Reusable TSDA helpers: decomposition, stationarity tests, period summaries.
Used by scripts/02_eda.py now, and by the FastAPI backend later.
"""
import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.stattools import adfuller, kpss

COVID_START = pd.Timestamp("2020-03-01")
COVID_END = pd.Timestamp("2021-12-01")


def decompose(series: pd.Series, period: int = 12):
    """STL decomposition (robust to the COVID / World Cup outliers)."""
    return STL(series, period=period, robust=True).fit()


def strength(res) -> dict:
    """Trend and seasonal strength in [0, 1] (Hyndman & Athanasopoulos)."""
    r = res.resid
    ft = max(0.0, 1 - np.var(r) / np.var(res.trend + r))
    fs = max(0.0, 1 - np.var(r) / np.var(res.seasonal + r))
    return {"trend_strength": round(float(ft), 3), "seasonal_strength": round(float(fs), 3)}


def adf(series: pd.Series) -> dict:
    s = series.dropna()
    stat, p, lags, nobs, crit, _ = adfuller(s, autolag="AIC")
    return {"adf_stat": round(stat, 3), "p_value": round(p, 4), "lags": lags}


def kpss_test(series: pd.Series) -> dict:
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        stat, p, *_ = kpss(series.dropna(), regression="c", nlags="auto")
    return {"kpss_stat": round(stat, 3), "kpss_p": round(p, 4)}


def stationarity_report(series: pd.Series, alpha: float = 0.05) -> dict:
    """ADF on level, first difference and seasonal difference (lag 12) + conclusion."""
    lvl = adf(series)
    d1 = adf(series.diff())
    d12 = adf(series.diff(12))
    k = kpss_test(series)
    if lvl["p_value"] < alpha:
        verdict = "stationary (level)"
    elif d1["p_value"] < alpha and d12["p_value"] < alpha:
        verdict = "non-stationary; d=1 and D=1 both work"
    elif d1["p_value"] < alpha:
        verdict = "non-stationary; use d=1"
    elif d12["p_value"] < alpha:
        verdict = "non-stationary; use D=1"
    else:
        verdict = "non-stationary; needs d=1 and D=1"
    return {"adf_level_p": lvl["p_value"], "adf_diff1_p": d1["p_value"],
            "adf_seasdiff12_p": d12["p_value"], "kpss_level_p": k["kpss_p"],
            "verdict": verdict}


def period_label(ts: pd.Timestamp) -> str:
    if ts < COVID_START:
        return "1. Pre-COVID (2014-01 to 2020-02)"
    if ts <= COVID_END:
        return "2. COVID (2020-03 to 2021-12)"
    return "3. Post-COVID (2022-01 on)"


def period_summary(df: pd.DataFrame, col: str) -> pd.DataFrame:
    d = df.copy()
    d["period"] = d["date"].map(period_label)
    return d.pivot_table(index="segment", columns="period", values=col, aggfunc="mean").round(1)
