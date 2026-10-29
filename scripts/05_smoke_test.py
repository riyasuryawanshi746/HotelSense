"""
05_smoke_test.py  (HotelSense - Phase 4/5)
Exercises every segment x metric x horizon through the service layer (and the HTTP layer if
fastapi + httpx are installed), plus error cases.   Run:  python scripts/05_smoke_test.py
"""
import re
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import service as S  # noqa: E402
import decision_support as D  # noqa: E402

fails, checks = [], 0
def check(cond, msg):
    global checks
    checks += 1
    if not cond:
        fails.append(msg)

def finite(xs):
    return all(x is not None and np.isfinite(x) for x in xs)

meta = S.meta()
for seg in meta["segments"]:
    for m in [x["id"] for x in meta["metrics"]]:
        S.history(seg, m); S.decomposition(seg, m)
        for h in meta["horizons"]:
            tag = f"{seg}|{m}|{h}"
            f = S.forecast(seg, m, h)
            for name, d in f["models"].items():
                check(len(d["mean"]) == h, f"{tag} {name}: wrong length")
                check(finite(d["mean"] + d["lower"] + d["upper"]), f"{tag} {name}: NaN in forecast")
                check(all(l <= mu + 1e-9 <= u + 2e-9 for l, mu, u in zip(d["lower"], d["mean"], d["upper"])),
                      f"{tag} {name}: interval does not bracket mean")
                if m == "occupancy":
                    check(all(0 <= v <= 100 for v in d["mean"] + d["lower"] + d["upper"]), f"{tag} {name}: occupancy out of 0-100")
                else:
                    check(all(v >= 0 for v in d["mean"] + d["lower"]), f"{tag} {name}: negative value")
            check(f["best_model"] in f["models"], f"{tag}: best model missing")
            e = S.evaluation(seg, m, h)
            check(len(e["table"]) >= 3, f"{tag}: evaluation table too small")
            d = S.decision(seg, m, h)
            check(len(d["signals"]) >= 4 and d["headline"], f"{tag}: decision incomplete")
            check(not re.search(r"\bnan\b|\binf\b", str(d).lower()), f"{tag}: NaN/inf in decision")
            for mm, ch in d["changes"].items():
                check(ch["status"] in D.STATUSES and ch["reason"] in D.REASONS, f"{tag} {mm}: unknown status/reason")
                check(ch["clear"] == (ch["status"] != "inconclusive"), f"{tag} {mm}: clear disagrees with status")
            check(d["signals"][0]["status"] == d["changes"][m]["status"], f"{tag}: outlook status != change status")
[S.overview(m) for m in ("occupancy", "adr", "revpar")]

# /api/eda: dataset summary agrees with the data, charts have one entry per segment, no NaN anywhere
raw, df_all = S.load_raw(), S.store()["df"]
for m in [x["id"] for x in meta["metrics"]]:
    e = S.eda(m)
    ds = e["dataset"]
    check(ds["raw"]["rows"] == len(raw) and ds["clean"]["rows"] == len(df_all), f"eda {m}: row counts")
    check(ds["clean"]["first_date"] == meta["first_date"] and ds["clean"]["last_date"] == meta["last_date"], f"eda {m}: dates")
    check(ds["clean"]["n_segments"] == len(meta["segments"]) and ds["clean"]["n_series"] == 21, f"eda {m}: segments/series")
    check(ds["quality"][0]["result"] == int(raw.isna().sum().sum()), f"eda {m}: missing-value count")
    check(len(ds["occupancy_over_100"]) == int((df_all.occupancy > 100).sum()), f"eda {m}: occupancy > 100 count")
    check(sorted(e["annual_means"]["series"]) == sorted(meta["segments"]), f"eda {m}: annual means per segment")
    check(sorted(e["seasonal_profile"]["series"]) == sorted(meta["segments"]), f"eda {m}: seasonal per segment")
    check(e["seasonal_profile"]["series"]["Qatar+"] == S.history("Qatar+", m)["seasonal_profile"]["values"],
          f"eda {m}: seasonal profile differs from Trend explorer")
    check(all(len(v) == len(e["annual_means"]["years"]) for v in e["annual_means"]["series"].values()), f"eda {m}: years")
    check(all(d["q1"] <= d["median"] <= d["q3"] and d["min"] <= d["q1"] and d["q3"] <= d["max"]
              for d in e["distribution"].values()), f"eda {m}: quartiles out of order")
    check(len(e["key_findings"]) >= 6, f"eda {m}: key findings missing")
    check(not re.search(r"\bnan\b|\binf\b|None", str(e["key_findings"]) + str(ds["cleaning_steps"])), f"eda {m}: NaN in text")
    check(e["outliers"] is not None and e["outliers"]["total"] > 0, f"eda {m}: outlier table not loaded")
try:
    S.eda("profit"); check(False, "eda bad metric: no error raised")
except S.ServiceError as err:
    check(err.status == 400, "eda bad metric: wrong status")

# model-summary: horizon-specific tables exist for every horizon and agree with model_comparison.csv
ms = S.model_summary()
for key in ("median_mape_by_metric", "pct_series_where_model_beats_baseline",
            "median_mape_by_metric_and_horizon", "pct_series_where_model_beats_baseline_by_horizon"):
    check(key in ms and key in ms["scope"], f"model-summary: {key} or its scope missing")
res = S.store()["res"]
for h in meta["horizons"]:
    check(str(h) in ms["median_mape_by_metric_and_horizon"], f"model-summary: MAPE for horizon {h} missing")
    check(str(h) in ms["pct_series_where_model_beats_baseline_by_horizon"], f"model-summary: beats for horizon {h} missing")
    for (m, model), v in res[res.horizon == h].groupby(["metric", "model"])["MAPE"].median().items():
        got = ms["median_mape_by_metric_and_horizon"][str(h)][m][model]
        check(abs(got - round(v, 1)) < 1e-9, f"model-summary: MAPE {m}/{model}/{h} = {got}, expected {v:.1f}")
f6 = S.forecast("Qatar+", "occupancy", 6)
check("6-month horizon" in f6["reliability"]["text"], "reliability text does not name its horizon")

for args, label in [(("Nowhere", "occupancy", 6), "bad segment"), (("Qatar+", "profit", 6), "bad metric"),
                    (("Qatar+", "occupancy", 5), "bad horizon")]:
    try:
        S.forecast(*args); check(False, f"{label}: no error raised")
    except S.ServiceError as e:
        check(e.status in (400, 404), f"{label}: wrong status {e.status}")

try:
    from fastapi.testclient import TestClient
    import main
    c = TestClient(main.app)
    for url, code in [("/api/health", 200), ("/api/meta", 200), ("/api/overview?metric=revpar", 200),
                      ("/api/forecast?segment=Qatar%2B&metric=occupancy&horizon=6", 200),
                      ("/api/decision?segment=Qatar%2B&metric=adr&horizon=12", 200),
                      ("/api/eda?metric=adr", 200), ("/api/eda?metric=profit", 400),
                      ("/api/forecast?segment=Nope&metric=occupancy&horizon=6", 404),
                      ("/api/forecast?segment=Qatar%2B&metric=occupancy&horizon=7", 400)]:
        r = c.get(url); check(r.status_code == code, f"HTTP {url}: got {r.status_code}, expected {code}")
    print("HTTP layer tested")
except ImportError:
    print("fastapi/httpx not installed: HTTP layer skipped")

print(f"\n{checks} checks, {len(fails)} failed")
for f in fails[:40]:
    print("  FAIL:", f)
sys.exit(1 if fails else 0)
