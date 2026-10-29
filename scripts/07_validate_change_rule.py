"""
07_validate_change_rule.py  (HotelSense - decision rule R1 validation)
Run AFTER scripts/03_model_comparison.py:   python scripts/07_validate_change_rule.py
Writes reports/change_rule_validation.md.

Checks the uncertainty used by the "clear change" rule (decision_support R1) on the rolling-origin backtest:
  A. Coverage of the horizon-AVERAGE error: how often |mean error over steps 1..h| <= the threshold.
     - old threshold: mean single-month calibrated half-width (what R1 used before)
     - new threshold: 80% quantile of past horizon-average errors (calibration.average_error_quantile)
     In-sample uses every origin (as the app does). Out-of-sample is leak-free: for origin k, only
     origins whose WHOLE h-month window ended on or before k are used to set the threshold.
  B. Out-of-sample decisions: apply R1 (uncertainty + materiality) at each origin and check the call
     against what really happened (actual average vs the same months one year earlier).
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
import calibration as C  # noqa: E402
from data_loader import get_series, load_clean  # noqa: E402
from decision_support import MATERIAL  # noqa: E402

LEVEL = C.LEVEL
bt = pd.read_csv(ROOT / "reports" / "tables" / "backtest_predictions.csv", parse_dates=["origin", "target"])
best = pd.read_csv(ROOT / "reports" / "tables" / "best_models.csv")
df = load_clean()


def months(a, b):
    return (b.year - a.year) * 12 + (b.month - a.month)


def old_threshold(g, h, before=None):
    """Mean over steps 1..h of the banded single-month 80% quantile (optionally from targets <= `before`)."""
    cells = g if before is None else g[g["target"] <= before]
    widths = C._band_widths(C.build_calibration(cells).popitem()[1]) if len(cells) else None
    return None if widths is None else float(np.mean([widths[C.band_of(s)] for s in range(1, h + 1)]))


rows, calls = [], []
for (seg, met, model), g in bt.groupby(["segment", "metric", "model"]):
    hist = get_series(df, seg, met)
    for h in (3, 6, 12):
        sub = g[(g["avail"] >= h) & (g["step"] <= h)]
        if sub.empty:
            continue
        per = sub.groupby("origin").agg(err=("pred", lambda p: 0), n=("step", "size"))
        per["err"] = (sub["actual"] - sub["pred"]).groupby(sub["origin"]).mean()
        per["f_mean"] = sub.groupby("origin")["pred"].mean()
        per["a_mean"] = sub.groupby("origin")["actual"].mean()
        per["ly_mean"] = sub.groupby("origin")["target"].apply(
            lambda t: hist.reindex(t - pd.DateOffset(months=12)).mean())
        origins = list(per.index)

        # in-sample (all origins), the way the app uses them
        q_in, n_in = C.average_error_quantile(g, h)
        old_in = old_threshold(g, h)
        if q_in is not None:
            rows.append({"metric": met, "h": h, "model": model, "kind": "in-sample",
                         "cov_new": (per["err"].abs() <= q_in).mean() * 100,
                         "cov_old": (per["err"].abs() <= old_in).mean() * 100, "n": len(per),
                         "ratio": q_in / old_in})

        # out-of-sample, leak-free
        for k in origins:
            past = [j for j in origins if months(j, k) >= h]  # window of j ended on or before k
            q, n = C.average_error_quantile(g[g["origin"].isin(past)], h)
            if q is None:
                continue
            old = old_threshold(g, h, before=k)
            e = abs(per.loc[k, "err"])
            rows.append({"metric": met, "h": h, "model": model, "kind": "out-of-sample",
                         "cov_new": float(e <= q) * 100, "cov_old": float(e <= old) * 100 if old else np.nan,
                         "n": 1, "ratio": q / old if old else np.nan})
            # R1 decision at origin k
            fm, am, lm = per.loc[k, ["f_mean", "a_mean", "ly_mean"]]
            to_u = (lambda x: x) if met == "occupancy" else (lambda x: x / lm * 100)
            d_f = (fm - lm) if met == "occupancy" else (fm / lm - 1) * 100
            d_a = (am - lm) if met == "occupancy" else (am / lm - 1) * 100
            clear = abs(d_f) > to_u(q) and abs(d_f) >= MATERIAL[met]
            clear_old = old is not None and abs(d_f) > to_u(old)
            calls.append({"metric": met, "h": h, "model": model, "seg": seg, "clear": clear, "clear_old": clear_old,
                          "right_sign": np.sign(d_f) == np.sign(d_a),
                          "actual_material": abs(d_a) >= MATERIAL[met]})

R = pd.DataFrame(rows)
K = pd.DataFrame(calls)
cov = (R.groupby(["kind", "h"]).apply(lambda x: pd.Series({
    "cells": int(x["n"].sum()),
    "coverage_new_%": np.average(x["cov_new"], weights=x["n"]),
    "coverage_old_%": np.average(x["cov_old"].fillna(0), weights=x["n"]),
    "median_new/old_width": x["ratio"].median()})).round(1))
cov_metric = (R[R.kind == "out-of-sample"].groupby(["metric", "h"])[["cov_new", "cov_old"]].mean().round(1))
def decision_table(k):
    return k.groupby(["metric", "h"]).apply(lambda x: pd.Series({
        "origins_tested": len(x),
        "old_rule_calls": int(x["clear_old"].sum()),
        "old_correct_direction": int((x["clear_old"] & x["right_sign"]).sum()),
        "new_rule_calls": int(x["clear"].sum()),
        "new_correct_direction": int((x["clear"] & x["right_sign"]).sum()),
        "actual_material_change": int(x["actual_material"].sum())}))


dec = decision_table(K)
# the model the app actually uses for each series and horizon (chosen on the full backtest, so mildly optimistic)
used = best.rename(columns={"best_model": "model", "horizon": "h", "segment": "seg"})[["seg", "metric", "h", "model"]]
dec_best = decision_table(K.merge(used, on=["seg", "metric", "h", "model"]))

# ------------------------------------------------------------ summary (numbers computed above, not typed in)
def oos_cov(h):
    key = ("out-of-sample", h)
    return f"{cov.loc[key, 'coverage_new_%']:.1f}% ({int(cov.loc[key, 'cells'])} cells)" if key in cov.index else None


def direction(k, h):
    x = k[k["h"] == h]
    calls, right = int(x["clear"].sum()), int((x["clear"] & x["right_sign"]).sum())
    return f"{right} of {calls} calls" if len(x) else None


tested = [h for h in (3, 6, 12) if ("out-of-sample", h) in cov.index]
K_best = K.merge(used, on=["seg", "metric", "h", "model"])
summary = ["## Summary\n",
           "**Out-of-sample coverage** of the horizon-average error (nominal 80%): "
           + "; ".join(f"{h}-month horizon {oos_cov(h)}" for h in tested) + ".",
           "",
           "**Directional accuracy of 'supported' calls** (out-of-sample; the actual average moved the same way as "
           "the call): "
           + "; ".join(f"{h}-month horizon {direction(K_best, h)} for the model the app uses, "
                       f"{direction(K, h)} across all four models" for h in tested)
           + ". These are small numbers of calls, so the rates are very uncertain.",
           "",
           "**Not tested:** " + (", ".join(f"{h}-month" for h in (3, 6, 12) if h not in tested) or "none")
           + " horizon. There are not enough eligible historical forecast origins (each needs "
           f"{C.MIN_N_AVG} earlier origins whose whole window had already ended), so the 12-month rule and its "
           "directional calls remain unvalidated out of sample.",
           "",
           "### How to read the results",
           "- The figures are **indicative only**: origins are 2 months apart, so h-month forecast windows overlap and "
           "test cells are correlated; the hotel series are correlated with each other (Qatar+ contains the others); "
           "and the number of eligible origins is small.",
           "- The 'model the app uses' rows use the best model chosen on the full backtest, so they are mildly optimistic.",
           "- A **supported change is a prompt to investigate**, not an automatic pricing recommendation.",
           "- **No clear-change signal does not prove that performance will stay the same**; it only means the "
           "forecast change is not larger than past forecast errors of such averages (or is below the planning threshold).",
           f"- The planning thresholds (occupancy {MATERIAL['occupancy']:g} pts, ADR {MATERIAL['adr']:g}%, RevPAR "
           f"{MATERIAL['revpar']:g}%) are **provisional business assumptions**, not statistically validated or "
           "optimised values.",
           ""]

md = ["# HotelSense - Validation of the clear-change rule (R1)\n",
      *summary,
      "## Method\n",
      "Nominal level: 80%. 'old' = mean single-month calibrated half-width (previous rule); 'new' = 80% quantile "
      "of past horizon-average errors (current rule). All four models, all 21 series.\n",
      "Out-of-sample rows are leak-free: the threshold for origin k uses only origins whose whole h-month window "
      "ended on or before k, and needs at least "
      f"{C.MIN_N_AVG} such origins. That leaves no out-of-sample test for the 12-month horizon (origins run only "
      "from 2022-12, so too few complete 12-month windows exist).\n",
      "## A. Coverage of the horizon-average error (%)\n", cov.to_markdown(),
      "\n\n### Out-of-sample coverage by metric (%)\n", cov_metric.to_markdown(),
      "\n\n## B. Out-of-sample decisions (all models)\n",
      "'..._calls' = the rule says increase/decrease; '..._correct_direction' = the actual average moved the same "
      "way; 'actual_material_change' = the actual change was at least the planning threshold. "
      "The 12-month horizon has no rows because it could not be tested out of sample.\n",
      dec.to_markdown(),
      "\n\n### Only the best model per series and horizon (what the app shows)\n",
      dec_best.to_markdown(),
      "\n\nCaveats: origins are 2 months apart, so h-month windows overlap and test cells are correlated; "
      "series are also correlated with each other (Qatar+ contains the others). Treat the figures as indicative.\n"]
out = ROOT / "reports" / "change_rule_validation.md"
out.write_text("\n".join(md), encoding="utf-8")
print("\n".join(md))
