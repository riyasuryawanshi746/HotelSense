"""
preprocessing.py  (HotelSense - Phase 3)
Builds the modelling series for a (segment, metric).

Two versions are returned:
  actual   : values as published (occupancy capped at 100). Used for SCORING.
  adjusted : same, but the FIFA World Cup months (2022-11, 2022-12) are replaced by
             linear interpolation for ADR and RevPAR. Used for TRAINING only, because
             those months are one-off events (robust z up to ~190 in the EDA) that
             would distort level/seasonal estimates. Occupancy is not adjusted.
COVID months are NOT adjusted (documented limitation).
"""
import numpy as np
import pandas as pd
from data_loader import get_series

WORLD_CUP_MONTHS = pd.to_datetime(["2022-11-01", "2022-12-01"])
ADJUSTED_METRICS = ("adr", "revpar")


def adjust_world_cup(series: pd.Series, metric: str) -> pd.Series:
    s = series.copy()
    if metric not in ADJUSTED_METRICS:
        return s
    s[s.index.isin(WORLD_CUP_MONTHS)] = np.nan
    return s.interpolate(method="linear", limit_direction="both")


def prepare(df: pd.DataFrame, segment: str, metric: str):
    """Return (actual, adjusted) monthly series."""
    actual = get_series(df, segment, metric)
    return actual, adjust_world_cup(actual, metric)
