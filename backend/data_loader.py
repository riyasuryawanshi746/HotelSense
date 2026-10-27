"""
data_loader.py  (HotelSense - Phase 1)
Single place where the raw CSV is read and turned into clean, typed data.
Everything else (EDA, models, API) must load data through this module.
"""
from pathlib import Path
import pandas as pd

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "accommodation_data.csv"

# Raw column name -> clean snake_case name
COLUMN_MAP = {
    "Segment": "segment",
    "Date": "date",
    "Supply": "supply",                       # available room-nights
    "Demand": "demand",                       # sold room-nights
    "Occupancy Rate": "occupancy",            # % (as published)
    "Average Daily Rate": "adr",              # QAR
    "Revenue per Available Room": "revpar",   # QAR
    "Sample Properties": "sample_properties",
    "Sample Rooms": "sample_rooms",
    "Census Properties": "census_properties",
    "Census Rooms": "census_rooms",
}

# User-facing metric name -> column
METRICS = {"occupancy": "occupancy", "adr": "adr", "revpar": "revpar"}

# Qatar+ is the national aggregate, the other six are individual segments
AGGREGATE_SEGMENT = "Qatar+"


def load_raw(path: Path = DATA_PATH) -> pd.DataFrame:
    """Read the CSV exactly as published (note: semicolon-delimited)."""
    return pd.read_csv(path, sep=";")


def load_clean(path: Path = DATA_PATH) -> pd.DataFrame:
    """
    Clean long-format table, sorted by segment and date.
    Values are NOT altered; anomalies are only flagged:
      flag_occ_over_100  : published occupancy > 100 (demand > supply)
      occupancy_capped   : occupancy clipped at 100 (use for modelling)
      flag_world_cup     : Nov-Dec 2022 (FIFA World Cup, ADR/RevPAR spike)
    """
    df = load_raw(path).rename(columns=COLUMN_MAP)
    df["segment"] = df["segment"].str.strip()
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m")
    df = df.sort_values(["segment", "date"]).reset_index(drop=True)

    df["flag_occ_over_100"] = df["occupancy"] > 100
    df["occupancy_capped"] = df["occupancy"].clip(upper=100)
    df["flag_world_cup"] = df["date"].isin(pd.to_datetime(["2022-11-01", "2022-12-01"]))
    return df


def list_segments(df: pd.DataFrame) -> list[str]:
    return sorted(df["segment"].unique())


def get_series(df: pd.DataFrame, segment: str, metric: str = "occupancy",
               capped: bool = True) -> pd.Series:
    """
    Monthly series with a proper DatetimeIndex (freq='MS') for one segment.
    Raises if the series has gaps, so models never silently run on broken data.
    """
    if metric not in METRICS:
        raise ValueError(f"metric must be one of {list(METRICS)}")
    col = "occupancy_capped" if (metric == "occupancy" and capped) else METRICS[metric]
    g = df[df["segment"] == segment].set_index("date")[col].sort_index()
    if g.empty:
        raise ValueError(f"Unknown segment: {segment}")
    full = pd.date_range(g.index.min(), g.index.max(), freq="MS")
    if len(full) != len(g):
        raise ValueError(f"{segment}: {len(full) - len(g)} missing months")
    g = g.asfreq("MS")
    g.name = f"{segment} | {metric}"
    return g


if __name__ == "__main__":
    d = load_clean()
    print(d.shape, list_segments(d))
    print(get_series(d, "5 Star Hotels+", "occupancy").tail())
