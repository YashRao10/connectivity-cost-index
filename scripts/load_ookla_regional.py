"""Filter Ookla Open Data performance tiles down to our 3 comparison states
(NJ/NC/MT) and summarize actual measured speeds vs. FCC's advertised medians.

Input: data/raw/ookla/{fixed,mobile}/*.parquet (from scripts/pull_ookla.py)
Output: data/ookla_regional_summary.csv

Filtering approach: bounding-box on tile centroid (tile_x/tile_y = lon/lat),
not a true point-in-polygon state boundary check. This is a v1 approximation
-- each bbox can pick up slivers of neighboring states near the border (e.g.
NJ's bbox touches parts of NY/PA/DE). Good enough to see fixed-vs-mobile and
actual-vs-advertised gaps at a glance; not precise enough for a per-state
number anyone should cite as exact. A real fix would spatially join against
US Census state boundary shapefiles (e.g. via geopandas), left as a TODO if
this needs to be tighter.
"""

from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_DIR = DATA_DIR / "raw" / "ookla"

# Approximate bounding boxes (lon_min, lon_max, lat_min, lat_max).
STATE_BBOX = {
    "NJ": (-75.6, -73.9, 38.9, 41.4),
    "NC": (-84.3, -75.4, 33.8, 36.6),
    "MT": (-116.1, -104.0, 44.4, 49.0),
}


def load_and_filter(parquet_path: Path) -> pd.DataFrame:
    pf = pq.ParquetFile(parquet_path)
    cols = ["tile_x", "tile_y", "avg_d_kbps", "avg_u_kbps", "avg_lat_ms", "tests"]
    frames = []
    for batch in pf.iter_batches(batch_size=1_000_000, columns=cols):
        chunk = batch.to_pandas()
        for state, (lon_min, lon_max, lat_min, lat_max) in STATE_BBOX.items():
            mask = (
                chunk["tile_x"].between(lon_min, lon_max)
                & chunk["tile_y"].between(lat_min, lat_max)
            )
            if mask.any():
                sub = chunk.loc[mask].copy()
                sub["state_usps"] = state
                frames.append(sub)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def summarize(df: pd.DataFrame, net_type: str) -> pd.DataFrame:
    df = df.copy()
    df["down_mbps"] = df["avg_d_kbps"] / 1000
    df["up_mbps"] = df["avg_u_kbps"] / 1000
    summary = (
        df.groupby("state_usps")
        .agg(
            tiles=("state_usps", "count"),
            total_tests=("tests", "sum"),
            median_down_mbps=("down_mbps", "median"),
            median_up_mbps=("up_mbps", "median"),
            median_latency_ms=("avg_lat_ms", "median"),
        )
        .reset_index()
    )
    summary["network_type"] = net_type
    return summary


if __name__ == "__main__":
    results = []
    for net_type in ("fixed", "mobile"):
        files = sorted((RAW_DIR / net_type).glob("*.parquet"))
        if not files:
            print(f"No {net_type} parquet files found, skipping")
            continue
        raw = load_and_filter(files[0])
        if raw.empty:
            print(f"No {net_type} tiles matched any state bbox")
            continue
        results.append(summarize(raw, net_type))

    if not results:
        raise SystemExit("No Ookla data processed -- check data/raw/ookla/")

    out = pd.concat(results, ignore_index=True).sort_values(
        ["state_usps", "network_type"]
    )
    cols = [
        "state_usps",
        "network_type",
        "median_down_mbps",
        "median_up_mbps",
        "median_latency_ms",
        "tiles",
        "total_tests",
    ]
    print(out[cols].to_string(index=False))
    out_path = DATA_DIR / "ookla_regional_summary.csv"
    out.to_csv(out_path, index=False)
    print(f"\nWrote {out_path}")
