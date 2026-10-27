"""
02_eda.py  (HotelSense - Phase 2)
Run from project root:   python scripts/02_eda.py
Writes figures to reports/figures/ and tables to reports/eda_summary.md + reports/tables/*.csv
"""
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from data_loader import load_clean, get_series, list_segments, AGGREGATE_SEGMENT  # noqa: E402
import analysis as A  # noqa: E402

FIG = ROOT / "reports" / "figures"; FIG.mkdir(parents=True, exist_ok=True)
TAB = ROOT / "reports" / "tables"; TAB.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"figure.dpi": 110, "axes.grid": True, "grid.alpha": .3})

df = load_clean()
segs = list_segments(df)
metrics = {"occupancy": "Occupancy rate (%)", "adr": "ADR (QAR)", "revpar": "RevPAR (QAR)"}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

def shade(ax):
    ax.axvspan(A.COVID_START, A.COVID_END, color="red", alpha=.08, label="COVID period")
    ax.axvspan(pd.Timestamp("2022-11-01"), pd.Timestamp("2022-12-31"), color="gold", alpha=.35, label="World Cup")

# 1. Metrics over time, all segments
for m, label in metrics.items():
    fig, ax = plt.subplots(figsize=(11, 4.5))
    for s in segs:
        g = get_series(df, s, m, capped=False)
        ax.plot(g.index, g.values, lw=2.2 if s == AGGREGATE_SEGMENT else 1.1,
                color="black" if s == AGGREGATE_SEGMENT else None, label=s)
    shade(ax); ax.set_title(f"{label} by segment, 2014-2025"); ax.set_ylabel(label)
    ax.legend(ncol=4, fontsize=8, loc="upper center", bbox_to_anchor=(.5, -.08))
    fig.tight_layout(); fig.savefig(FIG / f"01_{m}_all_segments.png"); plt.close(fig)

# 2. Seasonal profile (pre-COVID years only, to avoid shock distortion)
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
for ax, (m, label) in zip(axes, metrics.items()):
    d = df[df.date < A.COVID_START]
    prof = d.groupby(["segment", d.date.dt.month])[m if m != "occupancy" else "occupancy_capped"].mean().unstack(0)
    prof.index = MONTHS
    prof.plot(ax=ax, lw=1.5, legend=False); ax.set_title(f"Avg {label} by month (2014-2019)")
axes[0].legend(fontsize=7, ncol=2)
fig.tight_layout(); fig.savefig(FIG / "02_seasonal_profile.png"); plt.close(fig)

# 3. Year x month heatmap for occupancy (Qatar+)
q = get_series(df, AGGREGATE_SEGMENT, "occupancy")
hm = q.to_frame("v").assign(y=q.index.year, m=q.index.month).pivot(index="y", columns="m", values="v")
fig, ax = plt.subplots(figsize=(9, 4.5))
im = ax.imshow(hm.values, aspect="auto", cmap="RdYlGn", vmin=20, vmax=90)
ax.set_xticks(range(12)); ax.set_xticklabels(MONTHS); ax.set_yticks(range(len(hm))); ax.set_yticklabels(hm.index)
ax.grid(False)
for i in range(hm.shape[0]):
    for j in range(12):
        if not np.isnan(hm.values[i, j]): ax.text(j, i, f"{hm.values[i,j]:.0f}", ha="center", va="center", fontsize=7)
fig.colorbar(im, label="Occupancy %"); ax.set_title("Qatar+ occupancy: year x month")
fig.tight_layout(); fig.savefig(FIG / "03_heatmap_qatar_occupancy.png"); plt.close(fig)

# 4. STL decomposition (occupancy) + strength table
rows = []
for s in segs:
    ser = get_series(df, s, "occupancy")
    res = A.decompose(ser)
    rows.append({"segment": s, **A.strength(res)})
    fig = res.plot(); fig.set_size_inches(10, 7); fig.suptitle(f"STL decomposition - {s} occupancy")
    fig.tight_layout(); fig.savefig(FIG / f"04_stl_{s.replace(' ', '_').replace('&', 'and').replace('+', 'plus')}.png"); plt.close(fig)
strength_df = pd.DataFrame(rows); strength_df.to_csv(TAB / "stl_strength_occupancy.csv", index=False)

# 5. Stationarity: every segment x metric
rows = []
for s in segs:
    for m in metrics:
        rows.append({"segment": s, "metric": m, **A.stationarity_report(get_series(df, s, m))})
stat_df = pd.DataFrame(rows); stat_df.to_csv(TAB / "stationarity_tests.csv", index=False)

# 6. ACF / PACF for Qatar+ occupancy (guides SARIMA orders)
fig, axes = plt.subplots(2, 2, figsize=(12, 7))
plot_acf(q, lags=36, ax=axes[0, 0], title="ACF - level"); plot_pacf(q, lags=36, ax=axes[0, 1], title="PACF - level", method="ywm")
dq = q.diff().diff(12).dropna()
plot_acf(dq, lags=36, ax=axes[1, 0], title="ACF - d=1, D=1"); plot_pacf(dq, lags=36, ax=axes[1, 1], title="PACF - d=1, D=1", method="ywm")
fig.suptitle("Qatar+ occupancy autocorrelation"); fig.tight_layout(); fig.savefig(FIG / "05_acf_pacf_qatar.png"); plt.close(fig)

# 7. Period comparison (structural change) + segment comparison
per_occ = A.period_summary(df.assign(o=df.occupancy_capped), "o"); per_occ.to_csv(TAB / "period_means_occupancy.csv")
per_adr = A.period_summary(df, "adr"); per_adr.to_csv(TAB / "period_means_adr.csv")
per_rp = A.period_summary(df, "revpar"); per_rp.to_csv(TAB / "period_means_revpar.csv")
cv = df.groupby("segment").occupancy_capped.agg(["mean", "std", "min", "max"]).round(1)
cv["cv_%"] = (cv["std"] / cv["mean"] * 100).round(1); cv.to_csv(TAB / "segment_comparison_occupancy.csv")

fig, ax = plt.subplots(figsize=(8, 4.5))
per_occ.plot.bar(ax=ax); ax.set_ylabel("Mean occupancy %"); ax.set_title("Mean occupancy by period"); plt.xticks(rotation=30, ha="right")
fig.tight_layout(); fig.savefig(FIG / "06_period_means.png"); plt.close(fig)

# 8. Outliers: robust z-score of STL residual (Qatar+ and all segments)
out = []
for s in segs:
    for m in metrics:
        res = A.decompose(get_series(df, s, m)); r = res.resid
        z = (r - r.median()) / (1.4826 * (r - r.median()).abs().median())
        for d, v in z[abs(z) > 4].items():
            out.append({"segment": s, "metric": m, "date": d.strftime("%Y-%m"), "robust_z": round(v, 1)})
out_df = pd.DataFrame(out).sort_values("robust_z", key=abs, ascending=False); out_df.to_csv(TAB / "outliers_stl_residual.csv", index=False)

# Markdown summary
md = ["# HotelSense - EDA Summary\n",
      "## STL strength (occupancy)\n", strength_df.to_markdown(index=False),
      "\n\n## Stationarity (ADF p-values; KPSS p<0.05 means non-stationary)\n", stat_df.to_markdown(index=False),
      "\n\n## Mean occupancy by period\n", per_occ.to_markdown(),
      "\n\n## Mean ADR by period (QAR)\n", per_adr.to_markdown(),
      "\n\n## Mean RevPAR by period (QAR)\n", per_rp.to_markdown(),
      "\n\n## Segment comparison (occupancy, capped)\n", cv.to_markdown(),
      f"\n\n## STL residual outliers (|robust z| > 4): {len(out_df)} found\n", out_df.head(25).to_markdown(index=False),
      "\n\nFigures are in reports/figures/.\n"]
(ROOT / "reports" / "eda_summary.md").write_text("\n".join(md), encoding="utf-8")
print("\n".join(md)); print("\nFigures:", len(list(FIG.glob('*.png'))))
