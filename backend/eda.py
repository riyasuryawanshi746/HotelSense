"""
eda.py  (HotelSense - Overview page: dataset summary and EDA highlights)
Pure functions that summarise the data for /api/eda. Every number is computed here from the
published CSV (via data_loader) or read from the EDA outputs of scripts/02_eda.py; nothing is typed in.
The data-quality checks repeat the ones in scripts/01_data_audit.py so the page and the audit agree.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

import analysis as A
from data_loader import AGGREGATE_SEGMENT, DATA_PATH, list_segments
from preprocessing import ADJUSTED_METRICS, WORLD_CUP_MONTHS

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
SHORT_NAME = {"occupancy": "occupancy", "adr": "ADR", "revpar": "RevPAR"}


def _r(x, nd=2):
    """Round to a JSON-safe float (None for NaN)."""
    return None if x is None or not np.isfinite(x) else round(float(x), nd)


def _col(metric: str) -> str:
    """Column used for analysis: occupancy is capped at 100 exactly as in modelling."""
    return "occupancy_capped" if metric == "occupancy" else metric


def _is_covid(dates: pd.Series) -> pd.Series:
    return (dates >= A.COVID_START) & (dates <= A.COVID_END)


# ------------------------------------------------------------------ dataset at a glance
def dataset_summary(raw: pd.DataFrame, df: pd.DataFrame, metric_labels: dict) -> dict:
    """Raw file -> cleaned table: size, coverage, frequency, data quality and the cleaning steps."""
    segs = list_segments(df)
    # frequency and gaps: every segment should have one row per calendar month
    gaps, steps = 0, set()
    for _, g in df.groupby("segment"):
        full = pd.date_range(g.date.min(), g.date.max(), freq="MS")
        gaps += len(full.difference(g.date))
        steps |= set(((g.date.dt.year * 12 + g.date.dt.month).diff().dropna()).astype(int))
    frequency = "monthly" if steps == {1} else f"irregular (gaps of {sorted(steps)} months)"

    over = df[df.flag_occ_over_100]
    occ_calc = df.demand / df.supply * 100
    rp_bad = df[(df.adr * df.occupancy / 100 - df.revpar).abs() > 1]
    piv = df.pivot(index="date", columns="segment", values="supply")
    agg_gap = (piv[AGGREGATE_SEGMENT] - piv.drop(columns=AGGREGATE_SEGMENT).sum(axis=1)).abs()
    n_wc = int(df.flag_world_cup.sum())
    n_covid = int(_is_covid(df.date).sum())
    n_months = df.date.nunique()

    quality = [
        {"check": "Missing values (all columns)", "result": int(raw.isna().sum().sum())},
        {"check": "Duplicate segment-month rows", "result": int(df.duplicated(["segment", "date"]).sum())},
        {"check": "Missing months inside a segment's date range", "result": int(gaps)},
        {"check": "Occupancy above 100% (demand > supply)", "result": int(len(over))},
        {"check": "Occupancy differs from demand / supply by > 0.5 pts", "result": int(((occ_calc - df.occupancy).abs() > 0.5).sum())},
        {"check": "RevPAR differs from ADR x occupancy by > 1 QAR", "result": int(len(rp_bad))},
    ]
    cleaning = [
        f"Read {len(raw)} rows × {raw.shape[1]} columns from {Path(DATA_PATH).name} (semicolon-delimited).",
        "Renamed columns to short names, trimmed segment names, parsed YYYY-MM dates and sorted by segment and date.",
        f"No rows were removed and no published value was changed: {len(df)} rows after cleaning.",
        f"Flagged {len(over)} occupancy values above 100%; they are kept as published and capped at 100 for modelling.",
        f"Flagged {n_wc} World Cup rows ({', '.join(d.strftime('%Y-%m') for d in WORLD_CUP_MONTHS)}). For "
        f"{' and '.join(SHORT_NAME[m] for m in ADJUSTED_METRICS)} these months are interpolated in the training "
        f"series only ({n_wc * len(ADJUSTED_METRICS)} values); scores use published values.",
        f"COVID months ({A.COVID_START:%Y-%m} to {A.COVID_END:%Y-%m}, {n_covid} rows) are kept unchanged.",
    ]
    return {
        "raw": {"file": Path(DATA_PATH).name, "rows": int(len(raw)), "columns": int(raw.shape[1]),
                "column_names": [str(c).strip().lstrip("﻿") for c in raw.columns]},
        "clean": {"rows": int(len(df)), "first_date": df.date.min().strftime("%Y-%m"),
                  "last_date": df.date.max().strftime("%Y-%m"), "months": int(n_months),
                  "frequency": frequency, "segments": segs, "n_segments": len(segs),
                  "aggregate_segment": AGGREGATE_SEGMENT,
                  "metrics": [{"id": m, "label": lbl} for m, lbl in metric_labels.items()],
                  "n_series": len(segs) * len(metric_labels),
                  "rows_per_segment": int(df.groupby("segment").size().iloc[0]) if df.groupby("segment").size().nunique() == 1 else None},
        "quality": quality,
        "occupancy_over_100": [{"segment": r.segment, "date": r.date.strftime("%Y-%m"), "occupancy": _r(r.occupancy, 1),
                                "supply": int(r.supply), "demand": int(r.demand)} for r in over.itertuples()],
        "aggregate_check": {"max_abs_supply_gap": _r(agg_gap.max(), 0), "mean_abs_supply_gap": _r(agg_gap.mean(), 0),
                            "text": f"{AGGREGATE_SEGMENT} supply is not an exact sum of the other segments "
                                    f"(largest monthly gap {agg_gap.max():,.0f} room-nights), so it is treated "
                                    "as its own national series."},
        "cleaning_steps": cleaning,
        "flags": {"world_cup_rows": n_wc, "covid_rows": n_covid},
    }


# ------------------------------------------------------------------ EDA for one metric
def annual_means(df: pd.DataFrame, metric: str) -> dict:
    """Mean per calendar year and segment; years without all 12 months are left out (and listed)."""
    col = _col(metric)
    d = df.assign(year=df.date.dt.year)
    counts = d.groupby("year").date.nunique()
    full_years = [int(y) for y, n in counts.items() if n == 12]
    partial = [f"{int(y)} ({n} months)" for y, n in counts.items() if n != 12]
    tab = d[d.year.isin(full_years)].groupby(["segment", "year"])[col].mean().unstack()
    wc_year = WORLD_CUP_MONTHS[0].year
    note = (f"Published values; the {wc_year} average includes the World Cup months."
            if metric in ADJUSTED_METRICS else "Published values (occupancy capped at 100).")
    return {"years": full_years, "series": {s: [_r(v) for v in tab.loc[s]] for s in tab.index},
            "excluded_partial_years": partial, "note": note}


def distribution(df: pd.DataFrame, metric: str) -> dict:
    """Five-number summary per segment over all months (COVID and World Cup months included)."""
    col = _col(metric)
    out = {}
    for s, g in df.groupby("segment"):
        q = g[col].quantile([0, .25, .5, .75, 1]).to_numpy()
        out[s] = {"min": _r(q[0]), "q1": _r(q[1]), "median": _r(q[2]), "q3": _r(q[3]), "max": _r(q[4]),
                  "mean": _r(g[col].mean()), "std": _r(g[col].std()),
                  "cv_pct": _r(g[col].std() / g[col].mean() * 100, 1)}
    return out


def period_means(df: pd.DataFrame, metric: str) -> dict:
    """Mean per segment for the pre-COVID, COVID and post-COVID periods (analysis.period_summary)."""
    tab = A.period_summary(df.assign(v=df[_col(metric)]), "v")
    return {"periods": list(tab.columns), "segments": list(tab.index),
            "values": {s: [_r(v, 1) for v in tab.loc[s]] for s in tab.index}}


def occupancy_adr_relationship(df: pd.DataFrame) -> dict:
    """Pearson correlation of monthly occupancy and ADR per segment, World Cup months excluded."""
    d = df[~df.flag_world_cup]
    rows, points = [], {}
    for s, g in d.groupby("segment"):
        rows.append({"segment": s, "r": _r(g.occupancy_capped.corr(g.adr)), "n": int(len(g))})
        points[s] = {"occupancy": [_r(v, 1) for v in g.occupancy_capped], "adr": [_r(v) for v in g.adr]}
    return {"correlations": rows, "points": points,
            "note": "Pearson r of monthly occupancy (capped) and ADR, excluding the World Cup months. "
                    "A descriptive association, not evidence of cause."}


def outlier_summary(path: Path, metric: str) -> dict | None:
    """Counts of STL-residual outliers (|robust z| > 4, from scripts/02_eda.py) by metric and period."""
    if not path.exists():
        return None
    o = pd.read_csv(path)
    dt = pd.to_datetime(o["date"])
    o["period"] = np.where(dt.isin(WORLD_CUP_MONTHS), "World Cup months",
                           np.where(_is_covid(dt), "COVID period", "Other months"))
    counts = o.groupby(["metric", "period"]).size().unstack(fill_value=0)
    top = o[o.metric == metric].reindex(o[o.metric == metric].robust_z.abs().sort_values(ascending=False).index).head(8)
    return {"total": int(len(o)),
            "by_metric_and_period": {m: {p: int(v) for p, v in r.items()} for m, r in counts.iterrows()},
            "top_for_metric": [{"segment": r.segment, "date": r.date, "robust_z": _r(r.robust_z, 1),
                                "period": r.period} for r in top.itertuples()],
            "note": "Months whose STL remainder is more than 4 robust standard deviations from typical "
                    "(scripts/02_eda.py). Flagged for attention, not removed."}


# ------------------------------------------------------------------ key findings (computed text)
def key_findings(df: pd.DataFrame, ds: dict, seasonal_aggregate: list, outliers_path: Path) -> list[dict]:
    """Short, evidence-based statements. Each one is built from the numbers it quotes."""
    out = []
    c, q = ds["clean"], [x["result"] for x in ds["quality"]]  # order: missing, duplicates, gaps, ...
    out.append({"topic": "Data quality",
                "text": f"{c['rows']} monthly records ({c['n_segments']} segments × {c['months']} months, "
                        f"{c['first_date']} to {c['last_date']}) with {q[0]} missing values, {q[1]} duplicate rows "
                        f"and {q[2]} missing months."})

    top = df.nlargest(10, "adr")
    n_wc_top = int(top.flag_world_cup.sum())
    out.append({"topic": "World Cup",
                "text": f"{n_wc_top} of the 10 highest monthly ADR values are World Cup months (Nov-Dec 2022); the "
                        f"highest is {top.iloc[0].adr:,.0f} QAR ({top.iloc[0].segment}, {top.iloc[0].date:%Y-%m}). "
                        "These are real published values, adjusted only in the training series."})

    per = A.period_summary(df.assign(v=df.occupancy_capped), "v").loc[AGGREGATE_SEGMENT]
    pre, cov, post = per.iloc[0], per.iloc[1], per.iloc[2]
    out.append({"topic": "COVID period",
                "text": f"{AGGREGATE_SEGMENT} mean occupancy was {pre:.1f}% before COVID, {cov:.1f}% during the COVID "
                        f"period ({A.COVID_START:%Y-%m} to {A.COVID_END:%Y-%m}) and {post:.1f}% afterwards. "
                        "The period stays in the training data as a structural break."})

    prof = pd.Series(seasonal_aggregate, index=MONTHS)
    hi, lo = prof.nlargest(2), prof.nsmallest(2)
    out.append({"topic": "Seasonality",
                "text": f"{AGGREGATE_SEGMENT} occupancy is typically highest in {hi.index[0]} ({hi.iloc[0]:.1f}%) and "
                        f"{hi.index[1]} ({hi.iloc[1]:.1f}%) and lowest in {lo.index[0]} ({lo.iloc[0]:.1f}%) and "
                        f"{lo.index[1]} ({lo.iloc[1]:.1f}%) (monthly means excluding COVID months). The data does "
                        "not show why."})

    occ = df.groupby("segment").occupancy_capped.mean()
    adr = df.groupby("segment").adr.median()
    out.append({"topic": "Segments",
                "text": f"Mean occupancy ranges from {occ.min():.1f}% ({occ.idxmin()}) to {occ.max():.1f}% "
                        f"({occ.idxmax()}); median ADR ranges from {adr.min():,.0f} QAR ({adr.idxmin()}) to "
                        f"{adr.max():,.0f} QAR ({adr.idxmax()})."})

    rel = occupancy_adr_relationship(df)["correlations"]
    rs = [c["r"] for c in rel if c["r"] is not None]
    out.append({"topic": "Occupancy and ADR",
                "text": f"Monthly occupancy and ADR are only weakly to moderately related within segments "
                        f"(Pearson r from {min(rs):+.2f} to {max(rs):+.2f}, World Cup months excluded), so a busy "
                        "month does not reliably mean a higher rate."
                        if max(abs(r) for r in rs) < 0.7 else
                        f"Pearson r between monthly occupancy and ADR ranges from {min(rs):+.2f} to {max(rs):+.2f} "
                        "across segments (World Cup months excluded)."})

    n_over = len(ds["occupancy_over_100"])
    out.append({"topic": "Occupancy above 100%",
                "text": f"{n_over} published occupancy values exceed 100% (all "
                        f"{', '.join(sorted({o['segment'] for o in ds['occupancy_over_100']}))}), where reported demand "
                        "exceeds supply. They are kept as published and capped at 100 for modelling."
                        if n_over else "No published occupancy value exceeds 100%."})

    if outliers_path.exists():
        o = pd.read_csv(outliers_path)
        dt = pd.to_datetime(o["date"])
        n_event = int((dt.isin(WORLD_CUP_MONTHS) | _is_covid(dt)).sum())
        out.append({"topic": "Unusual months",
                    "text": f"{n_event} of the {len(o)} STL-residual outliers fall in the COVID period or the World Cup "
                            f"months ({n_event / len(o) * 100:.0f}%); the rest are spread over other months."})
    return out
