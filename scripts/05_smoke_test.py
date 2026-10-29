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
S.model_summary(); [S.overview(m) for m in ("occupancy", "adr", "revpar")]

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
