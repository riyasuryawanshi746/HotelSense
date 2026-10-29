"""
decision_support.py  (HotelSense - Phase 4)
Transparent, rule-based planning signals computed from the ACTUAL forecasts.
No text here is hard-coded with numbers: every figure comes from the forecast, the history
or the backtest. Output is framed as planning prompts, not guaranteed decisions, and the data
is segment-level, so nothing here applies to a specific hotel.

Rules (all documented so they can be explained in the viva):
  R1 Level change   Question: is the AVERAGE over the forecast months materially different from the
                    same calendar months last year (same segment, same metric)?
                    change = mean(forecast) - mean(last year's published values for those months).
                    Last year's values are known, so the only uncertainty is the error of the forecast
                    AVERAGE. We measure it directly from the rolling-origin backtest: the 80th percentile
                    of |mean error over steps 1..h| across origins (calibration.average_error_quantile).
                    This keeps the real correlation between monthly errors (no sqrt(h) shortcut).
                    Status "increase"/"decrease" needs BOTH |change| > that uncertainty (statistical)
                    AND |change| >= MATERIAL[metric] (business relevance); otherwise "inconclusive".
                    With too few backtest origins the wider single-month half-width is used instead.
  R2 Capacity       peak forecast month vs the segment's normal range (P90 of non-COVID months,
                    occupancy only), or upper bound >= 95%.
  R3 Soft demand    lowest forecast month <= the segment's P10.
  R4 Pricing        combines the R1 statuses of occupancy, ADR and RevPAR (see _pricing_signal);
                    it never suggests a price move from occupancy alone and only prompts a review.
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
    """Backtest scores in `row` are for ONE horizon h (steps 1..h pooled); the text says which."""
    skill = float(row["skill_vs_snaive_pct"])
    scope = f"{int(row['horizon'])}-month horizon"
    if bool(row["beats_baseline"]):
        return {"level": "model-supported", "skill_pct": round(skill, 1), "mape": round(float(row["MAPE"]), 1),
                "text": (f"{row['best_model']} had {skill:.0f}% lower RMSE than simply repeating last year's "
                         f"values in the backtest ({scope}, MAPE {float(row['MAPE']):.1f}%).")}
    return {"level": "baseline-level", "skill_pct": round(skill, 1), "mape": round(float(row["MAPE"]), 1),
            "text": ("No model beat simply repeating last year's values by at least 5% in the backtest "
                     f"({scope}; best: {row['best_model']}, MAPE {float(row['MAPE']):.1f}%). Treat this as a rough "
                     "seasonal guide with wide uncertainty.")}


# Smallest change we treat as relevant for planning: occupancy in percentage points, ADR and RevPAR in % of
# last year's level. PROVISIONAL BUSINESS ASSUMPTIONS, not statistically validated or optimised thresholds;
# change them only after agreeing new values with the people who use the dashboard.
MATERIAL = {"occupancy": 2.0, "adr": 3.0, "revpar": 3.0}
EPS = 1e-9
# Every value R1 can return; the frontend (DecisionPanel.jsx) has a label for each, checked by tests.
STATUSES = ("increase", "decrease", "inconclusive")
REASONS = ("supported", "within_uncertainty", "below_materiality", "baseline_forecast", "missing_data", "zero_baseline")


def _change(metric: str, hist: dict, frame: pd.DataFrame, avg_q=None, model: str = "") -> dict:
    """
    R1 for one metric. frame = calibrated forecast (mean, lower, upper) for the horizon.
    avg_q = (q, n) from calibration.average_error_quantile, in the metric's own units (q may be None).
    """
    ly = hist[metric].reindex(frame.index - pd.DateOffset(months=12)).to_numpy(dtype=float)
    fc = frame["mean"].to_numpy(dtype=float)
    m_f = float(np.mean(fc)) if np.all(np.isfinite(fc)) else float("nan")
    m_ly = float(np.mean(ly)) if np.all(np.isfinite(ly)) else float("nan")
    hw = float(((frame["upper"] - frame["lower"]) / 2).mean())  # mean single-month 80% half-width
    is_occ = metric == "occupancy"
    out = {"forecast_mean": None, "last_year_mean": None, "delta": None, "unit": "pts" if is_occ else "%",
           "typical_error": None, "clear": False, "direction": "none", "status": "inconclusive", "reason": "",
           "uncertainty": None, "uncertainty_method": "", "n_backtest_origins": 0, "materiality": MATERIAL[metric]}

    # guard: every month needs a finite forecast and a published value 12 months earlier
    if not (np.isfinite(m_f) and np.isfinite(m_ly)):
        out["reason"] = "missing_data"
        return out
    # guard: a % change needs a non-zero base
    if not is_occ and abs(m_ly) < EPS:
        out["reason"] = "zero_baseline"
        return out

    q, n = avg_q if avg_q else (None, 0)
    if q is not None and np.isfinite(q):
        unc, method = q, f"80% range of the {len(fc)}-month average error over {n} backtest origins"
    else:  # too little history for the average: fall back to the (wider) single-month half-width
        unc, method = hw, "single-month 80% half-width (too few backtest origins for the average)"
    delta = (m_f - m_ly) if is_occ else (m_f / m_ly - 1) * 100
    unc_u = unc if is_occ else unc / m_ly * 100
    hw_u = hw if is_occ else hw / m_ly * 100

    supported, material = abs(delta) > unc_u, abs(delta) >= MATERIAL[metric]
    if supported and material:
        status, reason = ("increase" if delta > 0 else "decrease"), "supported"
    elif model == "Seasonal Naive":
        status, reason = "inconclusive", "baseline_forecast"  # forecast = last year by construction
    elif not supported:
        status, reason = "inconclusive", "within_uncertainty"
    else:
        status, reason = "inconclusive", "below_materiality"
    out.update({"forecast_mean": round(m_f, 2), "last_year_mean": round(m_ly, 2), "delta": round(delta, 2),
                "typical_error": round(hw_u, 2), "clear": status != "inconclusive",
                "direction": "up" if delta > 0 else "down" if delta < 0 else "none",
                "status": status, "reason": reason, "uncertainty": round(unc_u, 2),
                "uncertainty_method": method, "n_backtest_origins": int(n)})
    return out


def _fmt_change(c: dict) -> str:
    """'+4.1 pts (±3.2)' style text, or 'not available' when the change could not be computed."""
    if c["delta"] is None:
        return "not available"
    return f"{c['delta']:+.1f} {c['unit']} (±{c['uncertainty']:.1f})"


def _normal_range(series: pd.Series) -> tuple[float, float]:
    s = series[~((series.index >= COVID[0]) & (series.index <= COVID[1]))]
    return float(s.quantile(0.10)), float(s.quantile(0.90))


def _pricing_signal(occ: dict, adr: dict, rev: dict) -> dict:
    """R4: uses only supported changes (status increase/decrease); prompts a review, never a price move."""
    o, a, r = occ["status"], adr["status"], rev["status"]
    txt = (f"Change vs the same months last year (± 80% uncertainty of the average): occupancy {_fmt_change(occ)}, "
           f"ADR {_fmt_change(adr)}, RevPAR {_fmt_change(rev)}.")
    base_note = (" The ADR forecast is the seasonal-naive baseline (no model beat it), so it repeats last year's "
                 "rates and cannot show a rate change." if adr["reason"] == "baseline_forecast" else "")
    if o == "increase" and a == "increase":
        return {"area": "pricing", "level": "info", "title": "Demand and rates both forecast higher",
                "text": txt + " Both rises exceed their uncertainty; no pricing concern is signalled."}
    if o == "increase":
        return {"area": "pricing", "level": "watch", "title": "Demand rising, rates not clearly following",
                "text": txt + " Occupancy shows a supported rise but ADR does not; review whether discounts are "
                              "still needed for these months." + base_note}
    if o == "decrease" and a == "increase":
        return {"area": "pricing", "level": "watch", "title": "Higher rates, falling occupancy",
                "text": txt + " RevPAR depends on which effect dominates; check price sensitivity before acting."}
    if o == "decrease":
        return {"area": "pricing", "level": "watch", "title": "Softening demand",
                "text": txt + " Occupancy shows a supported fall without an ADR offset; review promotions and "
                              "channel mix rather than cutting rates by default." + base_note}
    if a != "inconclusive":
        return {"area": "pricing", "level": "info", "title": f"ADR forecast {'higher' if a == 'increase' else 'lower'}",
                "text": txt + " ADR shows a supported change while occupancy does not; monitor whether demand responds."}
    if r != "inconclusive":
        return {"area": "pricing", "level": "info", "title": "RevPAR change",
                "text": txt + " Only RevPAR shows a supported change."}
    return {"area": "pricing", "level": "info", "title": "No supported revenue change",
            "text": txt + " None of these changes is both larger than its uncertainty and at least the planning "
                          f"threshold (occupancy {MATERIAL['occupancy']:.0f} pts, ADR and RevPAR {MATERIAL['adr']:.0f}%), "
                          "so no pricing review is signalled." + base_note}


def build_decision(segment: str, metric: str, horizon: int, hist: dict, frames: dict, rows: dict,
                   last_observed: pd.Timestamp, avg_q: dict | None = None) -> dict:
    """
    hist   : metric -> published monthly series
    frames : metric -> DataFrame(mean, lower, upper) for the horizon (calibrated)
    rows   : metric -> best-model row from best_models.csv
    avg_q  : metric -> (q, n), uncertainty of the horizon average (calibration.average_error_quantile)
    """
    avg_q = avg_q or {}
    ch = {m: _change(m, hist, frames[m], avg_q.get(m), rows[m]["best_model"]) for m in frames}
    sel, rel = ch[metric], reliability(rows[metric])
    label = METRIC_NAME[metric]
    unit_txt = "pts" if sel["unit"] == "pts" else "%"
    fr = frames[metric]
    suffix = "%" if metric == "occupancy" else " QAR"

    # R1: level change for the selected metric
    why_not = {
        "within_uncertainty": f"the difference is within the 80% uncertainty of the average (±{sel['uncertainty'] or 0:.1f} {unit_txt})",
        "below_materiality": (f"the difference exceeds the uncertainty (±{sel['uncertainty'] or 0:.1f} {unit_txt}) but is "
                              f"below the planning threshold of {sel['materiality']:.0f} {unit_txt}"),
        "baseline_forecast": "the forecast is last year's values (seasonal-naive baseline), so it cannot show a change",
        "missing_data": "the comparison could not be computed because data is missing",
        "zero_baseline": "last year's level is zero, so a % change is undefined",
    }
    if sel["status"] in ("increase", "decrease"):
        verdict = (f"a supported {sel['status']}, larger than the 80% uncertainty of the average "
                   f"(±{sel['uncertainty']:.1f} {unit_txt}) and the planning threshold ({sel['materiality']:.0f} {unit_txt})")
    else:
        verdict = f"inconclusive: {why_not.get(sel['reason'], 'no supported change')}"
    if sel["delta"] is None:
        outlook = f"{label} outlook for {_span(fr.index)}: {verdict}."
    else:
        outlook = (f"{label} is forecast to average {sel['forecast_mean']:.1f}{suffix} over {_span(fr.index)}, "
                   f"{sel['delta']:+.1f} {unit_txt} vs the same months last year ({sel['last_year_mean']:.1f}{suffix}): "
                   f"{verdict}.")
    signals = [{"area": "forecast", "level": "watch" if sel["clear"] else "info", "title": f"{label} outlook",
                "status": sel["status"], "text": outlook}]

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
        "A 'supported' change means the forecast average differs from last year by more than past errors of such "
        "averages; in the out-of-sample check (reports/change_rule_validation.md) these calls were often wrong, "
        "so treat them as prompts to investigate, not as predictions.",
    ]
    if rel["level"] == "baseline-level":
        caveats.insert(0, rel["text"])
    headline = f"{label}: {verdict}. " + ("Model-supported forecast." if rel["level"] == "model-supported"
                                          else "Low-confidence forecast (no better than last year's values).")
    return {"segment": segment, "metric": metric, "horizon": horizon, "headline": headline,
            "reliability": rel, "signals": signals, "caveats": caveats, "changes": ch,
            "normal_range_occupancy": {"p10": round(p10, 1), "p90": round(p90, 1)}}
