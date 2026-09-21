"""Filter Ookla Open Data performance tiles down to our comparison states
and summarize actual measured speeds vs. FCC's advertised medians.

Input: data/raw/ookla/{fixed,mobile}/*.parquet (from scripts/pull_ookla.py)
       data/raw/census/cb_2023_us_state_20m.shp (US Census cartographic
       boundary file, 20m resolution -- small enough to ship in the repo
       if desired, but currently gitignored under data/raw/)
Output: data/ookla_regional_summary.csv

Filtering approach: true point-in-polygon spatial join (geopandas sjoin,
predicate="within") of each tile's centroid against real Census state
boundaries -- replaces the earlier v1 bounding-box approximation, which
could misattribute border tiles to the wrong state. Shapely 2.x's vectorized
point construction keeps this fast even at nationwide scale (~6-7M tiles).
"""

from pathlib import Path

import geopandas as gpd
import pandas as pd
import pyarrow.parquet as pq

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_DIR = DATA_DIR / "raw" / "ookla"
CENSUS_SHP = DATA_DIR / "raw" / "census" / "cb_2023_us_state_20m.shp"

# States covered by this comparison -- expand this list to scale the project;
# no code changes needed elsewhere, load_fcc_broadband.py and
# build_cost_comparison.py just need matching FCC downloads per new state.
COMPARISON_STATES = [
    "NJ", "NC", "MT", "CA", "TX", "NY", "OH", "FL", "WA", "CO",
    "AL", "AR", "AZ", "CT", "DE", "GA", "ID", "IL",
]


def load_state_boundaries() -> gpd.GeoDataFrame:
    states = gpd.read_file(CENSUS_SHP)[["STUSPS", "geometry"]]
    return states[states["STUSPS"].isin(COMPARISON_STATES)]


def load_and_filter(parquet_path: Path, states: gpd.GeoDataFrame) -> pd.DataFrame:
    pf = pq.ParquetFile(parquet_path)
    cols = ["tile_x", "tile_y", "avg_d_kbps", "avg_u_kbps", "avg_lat_ms", "tests"]
    frames = []
    for batch in pf.iter_batches(batch_size=1_000_000, columns=cols):
        chunk = batch.to_pandas()
        points = gpd.GeoDataFrame(
            chunk,
            geometry=gpd.points_from_xy(chunk["tile_x"], chunk["tile_y"]),
            crs=states.crs,
        )
        joined = gpd.sjoin(points, states, how="inner", predicate="within")
        if not joined.empty:
            frames.append(joined.rename(columns={"STUSPS": "state_usps"}))
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
    states = load_state_boundaries()
    results = []
    for net_type in ("fixed", "mobile"):
        files = sorted((RAW_DIR / net_type).glob("*.parquet"))
        if not files:
            print(f"No {net_type} parquet files found, skipping")
            continue
        if len(files) > 1:
            # Silently picking files[0] here would pick whichever quarter
            # sorts first alphabetically, not necessarily the one intended --
            # a real risk once more than one quarter's file is present
            # locally (e.g. while building a time series). Fail loud instead.
            raise SystemExit(
                f"Multiple {net_type} parquet files found in {RAW_DIR / net_type}: "
                f"{[f.name for f in files]}. Remove the ones you don't want "
                "summarized, or use build_ookla_timeseries.py for multi-quarter runs."
            )
        raw = load_and_filter(files[0], states)
        if raw.empty:
            print(f"No {net_type} tiles matched any state boundary")
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
