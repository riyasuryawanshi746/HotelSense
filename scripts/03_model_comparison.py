"""
03_model_comparison.py  (HotelSense - Phase 3)
Run from project root:
    python scripts/03_model_comparison.py              # full run
    python scripts/03_model_comparison.py --fast       # smaller SARIMA grid, quick check
    python scripts/03_model_comparison.py --segments "Qatar+" --metrics occupancy

Writes:
    backend/models/sarima_config.json        chosen SARIMA specs (used by the API later)
    reports/tables/model_comparison.csv      every model x segment x metric x horizon
    reports/tables/best_models.csv           winner per segment x metric x horizon
    reports/tables/backtest_predictions.csv  actual vs predicted for every backtest cell
    reports/model_comparison.md              readable summary
    reports/figures/07_*.png, 08_*.png
"""
import argparse
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from data_loader import load_clean, list_segments  # noqa: E402
from preprocessing import prepare                  # noqa: E402
import forecasting as F                            # noqa: E402
import evaluation as E                             # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--step", type=int, default=2, help="months between forecast origins")
ap.add_argument("--first-origin", default="2022-12-01", help="first training cut-off")
ap.add_argument("--fast", action="store_true", help="smaller SARIMA grid")
ap.add_argument("--reselect", action="store_true", help="ignore cached SARIMA config")
ap.add_argument("--segments", nargs="*")
ap.add_argument("--metrics", nargs="*")
args = ap.parse_args()

FIG = ROOT / "reports" / "figures"; FIG.mkdir(parents=True, exist_ok=True)
TAB = ROOT / "reports" / "tables"; TAB.mkdir(parents=True, exist_ok=True)

df = load_clean()
segs = args.segments or list_segments(df)
metrics = args.metrics or ["occupancy", "adr", "revpar"]
first_origin = pd.Timestamp(args.first_origin)
cfg = F.load_config()

all_bt, all_res = [], []
t0 = time.time()
for s in segs:
    for m in metrics:
        actual, adj = prepare(df, s, m)
        key = F.config_key(s, m)
        if key not in cfg or args.reselect:
            # order chosen using data up to the first origin only (no test-period leakage)
            cfg[key] = F.select_sarima(adj.loc[:first_origin], fast=args.fast)
        bt = E.rolling_origin_backtest(actual, adj, m, first_origin, args.step, 12, cfg[key], args.fast)
        bt.insert(0, "metric", m); bt.insert(0, "segment", s)
        res = E.metrics_table(bt)
        res.insert(0, "metric", m); res.insert(0, "segment", s)
        all_bt.append(bt); all_res.append(res)
        print(f"[{time.time()-t0:6.0f}s] {s:22s} {m:10s} SARIMA {cfg[key]['order']}x{cfg[key]['seasonal_order']}", flush=True)

F.save_config(cfg)
bt = pd.concat(all_bt, ignore_index=True)
res = E.add_skill(pd.concat(all_res, ignore_index=True))
best = E.select_best(res)
num = ["MAE", "RMSE", "MAPE", "coverage80", "skill_vs_snaive_pct"]
res[num] = res[num].round(3); best[num] = best[num].round(3)
res.to_csv(TAB / "model_comparison.csv", index=False)
best.to_csv(TAB / "best_models.csv", index=False)
bt.to_csv(TAB / "backtest_predictions.csv", index=False)

# ------------------------------------------------------------ figures
# 07: example backtest (Qatar+ occupancy) from the origin closest to 2023-12
ex_seg = "Qatar+" if "Qatar+" in segs else segs[0]
ex_met = "occupancy" if "occupancy" in metrics else metrics[0]
ex = bt[(bt.segment == ex_seg) & (bt.metric == ex_met)]
origins = ex["origin"].drop_duplicates()
origin = origins.iloc[(origins - pd.Timestamp("2023-12-01")).abs().argmin()]
actual, _ = prepare(df, ex_seg, ex_met)
fig, ax = plt.subplots(figsize=(11, 4.8))
hist = actual.loc[origin - pd.DateOffset(months=36): origin + pd.DateOffset(months=12)]
ax.plot(hist.index, hist.values, "k", lw=2, label="Actual")
ax.axvline(origin, color="grey", ls="--")
for name, g in ex[ex.origin == origin].groupby("model"):
    ax.plot(g.target, g.pred, lw=1.5, label=name)
sg = ex[(ex.origin == origin) & (ex.model == "SARIMA")]
if len(sg):
    ax.fill_between(sg.target, sg.lower, sg.upper, alpha=.15, label="SARIMA 80% interval")
ax.set_title(f"{ex_seg} {ex_met}: forecasts made at {origin:%Y-%m} (training data ends there)")
ax.legend(ncol=3, fontsize=8); fig.tight_layout(); fig.savefig(FIG / "07_backtest_example.png"); plt.close(fig)

# 08: skill heatmap
fig, axes = plt.subplots(1, 3, figsize=(15, max(4, 0.35 * len(segs) * len(metrics))), sharey=True)
for ax, h in zip(axes, E.HORIZONS):
    p = res[(res.horizon == h) & (res.model != E.BASELINE)].pivot_table(
        index=["segment", "metric"], columns="model", values="skill_vs_snaive_pct")
    if p.empty:
        continue
    im = ax.imshow(p.values, cmap="RdYlGn", vmin=-50, vmax=50, aspect="auto")
    ax.set_xticks(range(p.shape[1])); ax.set_xticklabels(p.columns, rotation=30, ha="right", fontsize=8)
    ax.set_yticks(range(p.shape[0])); ax.set_yticklabels([f"{a} | {b}" for a, b in p.index], fontsize=8)
    ax.set_title(f"Horizon {h} months"); ax.grid(False)
    for i in range(p.shape[0]):
        for j in range(p.shape[1]):
            v = p.values[i, j]
            if not np.isnan(v): ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=7)
fig.suptitle("RMSE skill vs Seasonal Naive (%). Green = better than baseline, red = worse")
fig.tight_layout(); fig.savefig(FIG / "08_skill_heatmap.png"); plt.close(fig)

# ------------------------------------------------------------ markdown report
wins = best.groupby(["horizon", "best_model"]).size().unstack(fill_value=0)
med_skill = res[res.model != E.BASELINE].groupby(["horizon", "model"])["skill_vs_snaive_pct"].median().unstack().round(1)
cov = res.groupby(["horizon", "model"])["coverage80"].mean().unstack().round(1)
mape = res.groupby(["metric", "horizon", "model"])["MAPE"].median().unstack().round(1)
beats = best.groupby("horizon")["beats_baseline"].mean().mul(100).round(0)
bm = best.pivot_table(index=["segment", "metric"], columns="horizon", values="best_model", aggfunc="first")

md = [f"# HotelSense - Model Comparison\n",
      f"Rolling-origin backtest: first training cut-off {first_origin:%Y-%m}, a new origin every {args.step} months, "
      f"forecast up to 12 months ahead, 80% prediction intervals. Scored against published values.\n",
      "## Winning model count (lowest RMSE)\n", wins.to_markdown(),
      "\n\n## Median RMSE skill vs Seasonal Naive (%, positive = better than baseline)\n", med_skill.to_markdown(),
      "\n\n## % of series where the winner beats the baseline by at least 5%\n", beats.to_frame("pct").to_markdown(),
      "\n\n## Median MAPE (%) by metric, horizon and model\n", mape.to_markdown(),
      "\n\n## Mean empirical coverage of the nominal 80% interval (%)\n", cov.to_markdown(),
      "\n\n## Best model per segment, metric and horizon\n", bm.to_markdown(),
      "\n\n## Chosen SARIMA specifications\n",
      pd.DataFrame([{"series": k, "order": v["order"], "seasonal": v["seasonal_order"], "val_rmse": v["val_rmse"]}
                    for k, v in cfg.items() if k.split("|")[0] in segs]).to_markdown(index=False),
      "\n"]
(ROOT / "reports" / "model_comparison.md").write_text("\n".join(md), encoding="utf-8")
print("\n".join(md))
print(f"\nDone in {time.time()-t0:.0f}s. Figures 07, 08 and tables saved.")
