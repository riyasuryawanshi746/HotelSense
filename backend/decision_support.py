"""
decision_support.py  (HotelSense - Phase 4)
Transparent, rule-based planning signals computed from the ACTUAL forecasts.
No text here is hard-coded with numbers: every figure comes from the forecast, the history
or the backtest. Output is framed as planning prompts, not guaranteed decisions, and the data
is segment-level, so nothing here applies to a specific hotel.

Rules (all documented so they can be explained in the viva):
  R1 Level change   forecast mean vs the same months last year; called "clear" only if the change
                    is larger than the typical forecast error (calibrated 80% half-width).
  R2 Capacity       peak forecast month vs the segment's normal range (P90 of non-COVID months,
                    occupancy only), or upper bound >= 95%.
  R3 Soft demand    lowest forecast month <= the segment's P10.
  R4 Pricing        occupancy change vs ADR change (see _pricing_signal).
  R5 Reliability    does the winning model beat "same as last year" by >= 5% RMSE in backtest?
"""
from __future__ import annotations
import numpy as np
import pandas as pd

COVID = (pd.Timestamp("2020-03-01"), pd.Timestamp("2021-12-01"))
METRIC_NAME = {"occupancy": "Occupancy", "adr": "ADR", "revpar": "RevPAR"}


def _mon(d) -> str:
    return pd.Timestamp(d).strftime("%b %Y")


def _span(idx) -> str:
    return _mon(idx[0]) if len(idx) == 1 else f"{_mon(idx[0])} to {_mon(idx[-1])}"


def reliability(row: dict) -> dict:
    skill = float(row["skill_vs_snaive_pct"])
    if bool(row["beats_baseline"]):
        return {"level": "model-supported", "skill_pct": round(skill, 1), "mape": round(float(row["MAPE"]), 1),
                "text": (f"{row['best_model']} had {skill:.0f}% lower RMSE than simply repeating last year's "
                         f"values in the backtest (MAPE {float(row['MAPE']):.1f}%).")}
    return {"level": "baseline-level", "skill_pct": round(skill, 1), "mape": round(float(row["MAPE"]), 1),
            "text": ("No model beat simply repeating last year's values by at least 5% in the backtest "
                     f"(best: {row['best_model']}, MAPE {float(row['MAPE']):.1f}%). Treat this as a rough "
                     "seasonal guide with wide uncertainty.")}


def _change(metric: str, hist: dict, frame: pd.DataFrame) -> dict:
    ly = hist[metric].reindex(frame.index - pd.DateOffset(months=12)).to_numpy(dtype=float)
    m_ly, m_f = float(np.nanmean(ly)), float(frame["mean"].mean())
    hw = float(((frame["upper"] - frame["lower"]) / 2).mean())
    if metric == "occupancy":
        delta, hw_u, unit = m_f - m_ly, hw, "pts"
    else:
        delta, hw_u, unit = (m_f / m_ly - 1) * 100, hw / m_ly * 100, "%"
    return {"forecast_mean": round(m_f, 2), "last_year_mean": round(m_ly, 2), "delta": round(delta, 2),
            "unit": unit, "typical_error": round(hw_u, 2), "clear": bool(abs(delta) > hw_u),
            "direction": "up" if delta > 0 else "down"}


def _normal_range(series: pd.Series) -> tuple[float, float]:
    s = series[~((series.index >= COVID[0]) & (series.index <= COVID[1]))]
    return float(s.quantile(0.10)), float(s.quantile(0.90))


def _pricing_signal(occ: dict, adr: dict, rev: dict) -> dict:
    o_up, o_dn = occ["clear"] and occ["direction"] == "up", occ["clear"] and occ["direction"] == "down"
    a_up = adr["clear"] and adr["direction"] == "up"
    if o_up and not a_up:
        return {"area": "pricing", "level": "watch", "title": "Demand rising, rates not following",
                "text": (f"Occupancy is forecast {occ['delta']:+.1f} pts vs last year while ADR changes "
                         f"{adr['delta']:+.1f}%. Consider reviewing rate floors and discounting for these months.")}
    if o_dn and a_up:
        return {"area": "pricing", "level": "watch", "title": "Higher rates, falling occupancy",
                "text": (f"ADR is forecast {adr['delta']:+.1f}% while occupancy changes {occ['delta']:+.1f} pts. "
                         f"RevPAR ({rev['delta']:+.1f}%) depends on which effect dominates; check price sensitivity.")}
    if o_dn:
        return {"area": "pricing", "level": "watch", "title": "Softening demand",
                "text": (f"Occupancy is forecast {occ['delta']:+.1f} pts vs last year without an ADR offset "
                         f"({adr['delta']:+.1f}%). RevPAR change {rev['delta']:+.1f}%. Review promotions and channel mix.")}
    if rev["clear"]:
        return {"area": "pricing", "level": "info", "title": "RevPAR change",
                "text": f"RevPAR is forecast {rev['delta']:+.1f}% vs the same months last year, a change larger than the typical forecast error."}
    return {"area": "pricing", "level": "info", "title": "No clear revenue change",
            "text": "Occupancy, ADR and RevPAR changes are all within typical forecast error, so no pricing action is signalled."}


def build_decision(segment: str, metric: str, horizon: int, hist: dict, frames: dict, rows: dict,
                   last_observed: pd.Timestamp) -> dict:
    """
    hist   : metric -> published monthly series
    frames : metric -> DataFrame(mean, lower, upper) for the horizon (calibrated)
    rows   : metric -> best-model row from best_models.csv
    """
    ch = {m: _change(m, hist, frames[m]) for m in frames}
    sel, rel = ch[metric], reliability(rows[metric])
    label = METRIC_NAME[metric]
    unit_txt = "pts" if sel["unit"] == "pts" else "%"
    fr = frames[metric]
    suffix = "%" if metric == "occupancy" else " QAR"

    # R1: level change for the selected metric
    if sel["clear"]:
        verdict = (f"a meaningful {sel['direction']}ward change, larger than the typical forecast error "
                   f"(±{sel['typical_error']:.1f} {unit_txt})")
    else:
        verdict = (f"no clear change: the difference is within the typical forecast error "
                   f"(±{sel['typical_error']:.1f} {unit_txt})")
    signals = [{"area": "forecast", "level": "info", "title": f"{label} outlook",
                "text": (f"{label} is forecast to average {sel['forecast_mean']:.1f}{suffix} over "
                         f"{_span(fr.index)}, {sel['delta']:+.1f} {unit_txt} vs the same months last year "
                         f"({sel['last_year_mean']:.1f}{suffix}): {verdict}.")}]

    # R2 / R3: capacity and staffing (occupancy frame)
    oc = frames["occupancy"]
    p10, p90 = _normal_range(hist["occupancy"])
    peak, trough = oc["mean"].idxmax(), oc["mean"].idxmin()
    if oc.loc[peak, "mean"] >= p90 or oc["upper"].max() >= 95:
        signals.append({"area": "capacity", "level": "watch", "title": "Possible capacity pressure",
                        "text": (f"{_mon(peak)} is forecast at {oc.loc[peak, 'mean']:.0f}% occupancy (up to "
                                 f"{oc.loc[peak, 'upper']:.0f}% in the 80% range); this segment's high-demand level is "
                                 f"about {p90:.0f}%. Review available inventory, overbooking policy and peak staffing.")})
    else:
        signals.append({"area": "capacity", "level": "info", "title": "No capacity pressure signalled",
                        "text": (f"No month reaches this segment's high-demand level (~{p90:.0f}%). The busiest forecast "
                                 f"month is {_mon(peak)} at {oc.loc[peak, 'mean']:.0f}%.")})
    if oc.loc[trough, "mean"] <= p10:
        signals.append({"area": "staffing", "level": "watch", "title": "Soft-demand month",
                        "text": (f"{_mon(trough)} is forecast at {oc.loc[trough, 'mean']:.0f}%, in the lowest range "
                                 f"seen for this segment (≤{p10:.0f}%). Consider flexible rostering, maintenance "
                                 "scheduling or targeted promotions.")})
    else:
        signals.append({"area": "staffing", "level": "info", "title": "Staffing",
                        "text": (f"Lowest forecast month is {_mon(trough)} at {oc.loc[trough, 'mean']:.0f}%, not unusually low "
                                 f"for this segment (low range ≤{p10:.0f}%); no special staffing reduction is signalled.")})

    # R4: pricing across metrics
    signals.append(_pricing_signal(ch["occupancy"], ch["adr"], ch["revpar"]))

    caveats = [
        "Segment-level data only: these are planning signals, not recommendations for a specific property.",
        f"Data ends {_mon(last_observed)}. One-off events (such as the 2022 World Cup) are not predictable, "
        "and COVID-era months remain in the training data.",
        "Intervals are empirical 80% ranges from past backtest errors, so roughly 1 in 5 outcomes can fall outside.",
    ]
    if rel["level"] == "baseline-level":
        caveats.insert(0, rel["text"])
    headline = f"{label}: {verdict}. " + ("Model-supported forecast." if rel["level"] == "model-supported"
                                          else "Low-confidence forecast (no better than last year's values).")
    return {"segment": segment, "metric": metric, "horizon": horizon, "headline": headline,
            "reliability": rel, "signals": signals, "caveats": caveats, "changes": ch,
            "normal_range_occupancy": {"p10": round(p10, 1), "p90": round(p90, 1)}}
