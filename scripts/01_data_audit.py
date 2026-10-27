"""
01_data_audit.py  (HotelSense - Phase 1)
Run from the project root:   python scripts/01_data_audit.py
Writes: reports/data_audit.md and data/clean_accommodation.csv
"""
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from data_loader import load_raw, load_clean, AGGREGATE_SEGMENT  # noqa: E402

raw, df = load_raw(), load_clean()
out = []
def h(t): out.append(f"\n## {t}\n")
def p(t=""): out.append(str(t))

p("# HotelSense - Data Audit Report")

h("1. Shape and types")
p(f"- Rows: {len(raw)}, columns: {raw.shape[1]}")
p(f"- Missing values (total): {int(raw.isna().sum().sum())}")
p(f"- Duplicate (segment, date) rows: {int(df.duplicated(['segment','date']).sum())}")
p(f"- Segments: {', '.join(sorted(df.segment.unique()))}")

h("2. Date continuity per segment")
rows = []
for s, g in df.groupby("segment"):
    full = pd.date_range(g.date.min(), g.date.max(), freq="MS")
    miss = full.difference(g.date)
    rows.append(dict(segment=s, start=g.date.min().strftime("%Y-%m"),
                     end=g.date.max().strftime("%Y-%m"), n_obs=len(g),
                     expected=len(full), missing_months=len(miss)))
p(pd.DataFrame(rows).to_markdown(index=False))

h("3. Occupancy anomalies (> 100%)")
a = df[df.flag_occ_over_100][["segment", "date", "supply", "demand", "occupancy"]]
p(a.assign(date=a.date.dt.strftime("%Y-%m")).to_markdown(index=False) if len(a) else "None")
p("\nDemand exceeds supply in these rows, which is physically impossible for room-nights "
  "but is how the source published them (likely survey/reporting timing). "
  "Decision: keep the raw value, and use `occupancy_capped` (max 100) for modelling.")

h("4. Internal consistency checks")
occ_calc = df.demand / df.supply * 100
p(f"- Occupancy vs Demand/Supply, rows differing by >0.5 pt: {int((abs(occ_calc-df.occupancy)>0.5).sum())}")
rp_calc = df.adr * df.occupancy / 100
bad = df[abs(rp_calc - df.revpar) > 1]
p(f"- RevPAR vs ADR x Occupancy, rows differing by >1 QAR: {len(bad)}")
for _, r in bad.iterrows():
    p(f"  - {r.segment} {r.date:%Y-%m}: published {r.revpar}, computed {r.adr*r.occupancy/100:.2f} (rounding)")
p(f"- Rows with demand > supply: {int((df.demand > df.supply).sum())}")

h("5. Extreme values / events")
top = df.nlargest(6, "adr")[["segment", "date", "occupancy", "adr", "revpar"]]
p(top.assign(date=top.date.dt.strftime("%Y-%m")).to_markdown(index=False))
p("\nAll top ADR values are Nov-Dec 2022 (FIFA World Cup). These are real events, not errors: "
  "flag them, do not delete them.")

h("6. Is Qatar+ the sum of the other segments?")
piv = df.pivot(index="date", columns="segment", values="supply")
diff = (piv[AGGREGATE_SEGMENT] - piv.drop(columns=AGGREGATE_SEGMENT).sum(axis=1)).abs()
p(f"- Max |Qatar+ supply - sum of 6 segments|: {diff.max():.0f} room-nights "
  f"(mean {diff.mean():.0f}). Not an exact sum, so treat Qatar+ as its own national series.")

h("7. Descriptive statistics")
p(df[["supply", "demand", "occupancy", "adr", "revpar"]].describe().round(2).to_markdown())

(ROOT / "reports").mkdir(exist_ok=True)
(ROOT / "reports" / "data_audit.md").write_text("\n".join(out), encoding="utf-8")
df.to_csv(ROOT / "data" / "clean_accommodation.csv", index=False)
print("\n".join(out))
print("\nSaved reports/data_audit.md and data/clean_accommodation.csv")
