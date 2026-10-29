"""
main.py  (HotelSense - Phase 4)  FastAPI app.
Run from the backend folder:   uvicorn main:app --reload --port 8000
Docs (auto):                   http://localhost:8000/docs
"""
import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

import service as S

app = FastAPI(title="HotelSense API", version="1.0",
              description="Occupancy / ADR / RevPAR forecasting with decision support (Qatar Tourism data, CC BY).")

origins = os.getenv("HOTELSENSE_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"])


def run(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except S.ServiceError as e:
        raise HTTPException(status_code=e.status, detail=str(e))
    except Exception as e:  # unexpected: do not leak a stack trace to the client
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/meta")
def meta():
    return run(S.meta)


@app.get("/api/overview")
def overview(metric: str = "occupancy"):
    return run(S.overview, metric)


@app.get("/api/history")
def history(segment: str, metric: str = "occupancy"):
    return run(S.history, segment, metric)


@app.get("/api/decomposition")
def decomposition(segment: str, metric: str = "occupancy"):
    return run(S.decomposition, segment, metric)


@app.get("/api/forecast")
def forecast(segment: str, metric: str = "occupancy", horizon: int = Query(6), model: str = "best"):
    return run(S.forecast, segment, metric, horizon, model)


@app.get("/api/evaluation")
def evaluation(segment: str, metric: str = "occupancy", horizon: int = Query(6)):
    return run(S.evaluation, segment, metric, horizon)


@app.get("/api/model-summary")
def model_summary():
    return run(S.model_summary)


@app.get("/api/decision")
def decision(segment: str, metric: str = "occupancy", horizon: int = Query(6)):
    return run(S.decision, segment, metric, horizon)


@app.get("/api/eda")
def eda(metric: str = "occupancy"):
    return run(S.eda, metric)
