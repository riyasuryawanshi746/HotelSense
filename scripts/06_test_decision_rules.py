"""
06_test_decision_rules.py  (HotelSense - tests for decision rules R1 and R4)
Synthetic series with known answers; real data is not touched.   Run:  python scripts/06_test_decision_rules.py
"""
import re
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
import calibration as C  # noqa: E402
import decision_support as D  # noqa: E402

fails, checks = [], 0
def check(cond, msg):
    global checks
    checks += 1
    if not cond:
        fails.append(msg)

HIST_IDX = pd.date_range("2023-01-01", "2024-12-01", freq="MS")
FUT_IDX = pd.date_range("2025-01-01", periods=3, freq="MS")


def hist_of(values):
    return pd.Series(values, index=HIST_IDX, dtype=float)


def frame_of(mean, half=15.0, idx=FUT_IDX):
    mean = np.asarray(mean, dtype=float) * np.ones(len(idx))
    return pd.DataFrame({"mean": mean, "lower": mean - half, "upper": mean + half}, index=idx)


def change(metric, hist, frame, q=None, n=10, model="SARIMA"):
    return D._change(metric, {metric: hist}, frame, None if q is None else (q, n), model)


# ---------------------------------------------------------------- R1 three states
flat = hist_of([60.0] * 24)
c = change("occupancy", flat, frame_of(70), q=5)
check(c["status"] == "increase" and c["clear"] and c["delta"] == 10, f"clear increase: {c}")
c = change("occupancy", flat, frame_of(50), q=5)
check(c["status"] == "decrease" and c["direction"] == "down", f"clear decrease: {c}")
c = change("occupancy", flat, frame_of(66), q=8)
check(c["status"] == "inconclusive" and c["reason"] == "within_uncertainty", f"wide uncertainty: {c}")
c = change("occupancy", flat, frame_of(61.5), q=1)
check(c["status"] == "inconclusive" and c["reason"] == "below_materiality", f"below materiality: {c}")
c = change("occupancy", flat, frame_of(60), q=1, model="Seasonal Naive")
check(c["reason"] == "baseline_forecast" and not c["clear"], f"seasonal-naive forecast: {c}")
# the uncertainty used must be the horizon-average one, not the single-month half-width (15 here)
c = change("occupancy", flat, frame_of(70), q=5)
check(c["uncertainty"] == 5 and c["typical_error"] == 15, f"uses average-error quantile: {c}")

# ---------------------------------------------------------------- seasonal baseline
seasonal = hist_of([50 + 20 * np.sin(2 * np.pi * (d.month - 1) / 12) for d in HIST_IDX])
same_months = seasonal.loc["2024-01":"2024-03"]
c = change("occupancy", seasonal, frame_of(same_months.to_numpy()), q=1)
check(abs(c["delta"]) < 1e-9 and c["status"] == "inconclusive",
      f"repeating last year's seasonal values gives zero change: {c}")
check(abs(c["last_year_mean"] - same_months.mean()) < 0.01, "last year = the same calendar months, not the annual mean")
c = change("occupancy", seasonal, frame_of(same_months.to_numpy() + 5), q=2)
check(abs(c["delta"] - 5) < 1e-6 and c["status"] == "increase", f"+5 on every month detected despite seasonality: {c}")

# ---------------------------------------------------------------- % metrics and denominators
adr = hist_of([500.0] * 24)
c = change("adr", adr, frame_of(550), q=20)
check(c["unit"] == "%" and abs(c["delta"] - 10) < 1e-9 and abs(c["uncertainty"] - 4) < 1e-9 and c["status"] == "increase",
      f"ADR change and uncertainty in % of last year: {c}")
c = change("adr", hist_of([0.0] * 24), frame_of(10), q=1)
check(c["reason"] == "zero_baseline" and c["delta"] is None and not c["clear"], f"zero denominator: {c}")
c = change("adr", hist_of([1e-12] * 24), frame_of(10), q=1)
check(c["reason"] == "zero_baseline", f"near-zero denominator: {c}")

# ---------------------------------------------------------------- missing / non-finite
gap = flat.copy(); gap.loc["2024-02-01"] = np.nan
c = change("occupancy", gap, frame_of(70), q=5)
check(c["reason"] == "missing_data" and c["status"] == "inconclusive", f"missing last-year month: {c}")
c = change("occupancy", flat.loc[:"2024-01-01"], frame_of(70), q=5)
check(c["reason"] == "missing_data", f"last-year months absent from history: {c}")
c = change("occupancy", flat, frame_of([70, np.nan, 70]), q=5)
check(c["reason"] == "missing_data", f"NaN in forecast: {c}")
c = change("occupancy", flat, frame_of([70, np.inf, 70]), q=5)
check(c["reason"] == "missing_data", f"inf in forecast: {c}")
c = change("occupancy", flat, frame_of(70), q=float("nan"))
check("single-month" in c["uncertainty_method"] and c["uncertainty"] == 15, f"non-finite q falls back: {c}")

# ---------------------------------------------------------------- multi-month uncertainty
def synth_bt(errors_by_origin, avail=12):
    """errors_by_origin: list of per-step error lists. pred = 100, actual = 100 + error."""
    rows = []
    for k, errs in enumerate(errors_by_origin):
        origin = pd.Timestamp("2022-12-01") + pd.DateOffset(months=2 * k)
        for s, e in enumerate(errs, start=1):
            rows.append({"origin": origin, "step": s, "avail": avail, "pred": 100.0, "actual": 100.0 + e})
    return pd.DataFrame(rows)

levels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
q, n = C.average_error_quantile(synth_bt([[e] * 3 for e in levels]), 3)
check(n == 10 and abs(q - np.quantile(levels, 0.8)) < 1e-9,
      f"perfectly correlated monthly errors: average uncertainty is NOT shrunk (q={q})")
check(q > np.quantile(levels, 0.8) / np.sqrt(3) + 1, "no sqrt(h) shrinkage for correlated errors")
q, _ = C.average_error_quantile(synth_bt([[e, -e, 0] for e in levels]), 3)
check(abs(q) < 1e-9, f"errors that cancel within the horizon give ~0 average uncertainty (q={q})")
q, n = C.average_error_quantile(synth_bt([[1, 1, 1]] * 4), 3)
check(q is None and n == 4, "too few origins -> None (caller falls back to the single-month width)")
bt_short = pd.concat([synth_bt([[1] * 3] * 8), synth_bt([[50] * 2] * 3, avail=2)])
q, n = C.average_error_quantile(bt_short, 3)
check(n == 8 and abs(q - 1) < 1e-9, f"origins without h months of future data are excluded (n={n}, q={q})")
bt12 = synth_bt([[1] * 12] * 8)
q3, _ = C.average_error_quantile(bt12, 3)
q12, _ = C.average_error_quantile(bt12[bt12.step <= 6], 12)
check(q3 == 1 and q12 is None, "horizon h uses steps 1..h only; missing later steps do not count as an origin")

# ---------------------------------------------------------------- R4 pricing
def st(status, metric="occupancy", reason=None):
    unit = "pts" if metric == "occupancy" else "%"
    delta = {"increase": 5.0, "decrease": -5.0, "inconclusive": 0.5}[status]
    return {"status": status, "clear": status != "inconclusive", "delta": delta, "unit": unit, "uncertainty": 2.0,
            "reason": reason or ("supported" if status != "inconclusive" else "within_uncertainty")}

p = D._pricing_signal(st("increase"), st("inconclusive", "adr"), st("inconclusive", "revpar"))
check(p["level"] == "watch" and "rising" in p["title"], f"occupancy up, ADR flat: {p['title']}")
p = D._pricing_signal(st("decrease"), st("inconclusive", "adr"), st("inconclusive", "revpar"))
check("rather than cutting rates" in p["text"], "occupancy-only evidence never recommends a rate cut")
p = D._pricing_signal(st("inconclusive"), st("increase", "adr"), st("inconclusive", "revpar"))
check(p["title"] == "ADR forecast higher" and p["level"] == "info", f"ADR-only change: {p['title']}")
p = D._pricing_signal(st("inconclusive"), st("inconclusive", "adr", "baseline_forecast"), st("inconclusive", "revpar"))
check(p["title"] == "No supported revenue change" and "seasonal-naive baseline" in p["text"],
      "all inconclusive -> honest no-signal, mentioning the ADR baseline")
p = D._pricing_signal(st("increase"), st("increase", "adr"), st("increase", "revpar"))
check(p["level"] == "info", "demand and rates both up is not a warning")

# ---------------------------------------------------------------- full build_decision on synthetic data
hist = {"occupancy": flat, "adr": adr, "revpar": hist_of([300.0] * 24)}
frames = {"occupancy": frame_of(70), "adr": frame_of(500, half=40), "revpar": frame_of(350, half=60)}
rows = {m: {"best_model": "SARIMA", "skill_vs_snaive_pct": 10.0, "beats_baseline": True, "MAPE": 8.0, "horizon": 3}
        for m in hist}
d = D.build_decision("Test+", "occupancy", 3, hist, frames, rows, HIST_IDX[-1],
                     {"occupancy": (5, 10), "adr": (10, 10), "revpar": (30, 10)})
check(d["signals"][0]["status"] == "increase" and "supported increase" in d["headline"], f"headline: {d['headline']}")
check(not re.search(r"\bnan\b|\binf\b|None", str([s["text"] for s in d["signals"]])), "no NaN/None in signal text")
check(all(c["status"] in D.STATUSES and c["reason"] in D.REASONS for c in d["changes"].values()), "known statuses only")

# ---------------------------------------------------------------- frontend labels match backend values
jsx = (ROOT / "frontend" / "src" / "components" / "DecisionPanel.jsx").read_text(encoding="utf-8")
def keys(name):
    block = re.search(name + r" = \{(.*?)\};", jsx, re.S).group(1)
    return set(re.findall(r"^\s*(\w+):", block, re.M))
check(keys("STATUS_LABEL") == set(D.STATUSES), f"STATUS_LABEL keys {keys('STATUS_LABEL')} != {set(D.STATUSES)}")
check(keys("REASON_LABEL") == set(D.REASONS), f"REASON_LABEL keys {keys('REASON_LABEL')} != {set(D.REASONS)}")

print(f"{checks} checks, {len(fails)} failed")
for f in fails:
    print("  FAIL:", f)
sys.exit(1 if fails else 0)
