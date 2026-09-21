"""Build a simplified, web-sized GeoJSON of US states for the site's
choropleth map, annotated with our comparison metrics for the 10 states
we have data for (all other states render as "no data" background).

Input: data/raw/census/cb_2023_us_state_20m.shp (via pull_census_shapes.py)
       data/cost_comparison_v1.csv
Output: docs/data/state_map.geojson

Excludes AK, HI, and non-state territories (PR, GU, VI, AS, MP) -- keeping
the map to the contiguous 48 + DC avoids Alaska's antimeridian-wrap
rendering headaches and Hawaii's disconnected-islands layout for a simple
single-projection SVG map. As of the 51-state (50+DC) expansion, AK and HI
DO have real market-layer data (see data/cost_comparison_v1.csv) -- they're
just not plotted here. The full comparison table on the site covers them;
only this map's rendering excludes them. See docs/index.html's map section
caption.
"""

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DOCS_DATA_DIR = Path(__file__).resolve().parent.parent / "docs" / "data"
CENSUS_SHP = DATA_DIR / "raw" / "census" / "cb_2023_us_state_20m.shp"

EXCLUDED = {"AK", "HI", "PR", "GU", "VI", "AS", "MP"}
SIMPLIFY_TOLERANCE = 0.01  # degrees; ~1km, fine for a page-sized map


def cheapest_per_state(comparison: pd.DataFrame) -> pd.DataFrame:
    priced = comparison.dropna(subset=["cost_per_fcc_median_mbps_usd"])
    priced = priced[priced["cost_per_fcc_median_mbps_usd"] != float("inf")]
    idx = priced.groupby("state_usps")["cost_per_fcc_median_mbps_usd"].idxmin()
    cheapest = priced.loc[idx, ["state_usps", "technology_label", "cost_per_fcc_median_mbps_usd"]]
    return cheapest.rename(
        columns={
            "technology_label": "cheapest_technology",
            "cost_per_fcc_median_mbps_usd": "cheapest_cost_per_mbps_usd",
        }
    )


def leo_satellite_per_state(comparison: pd.DataFrame) -> pd.DataFrame:
    leo = comparison[comparison["technology_label"] == "LEO Satellite"]
    return leo[["state_usps", "cost_per_fcc_median_mbps_usd", "locations_served"]].rename(
        columns={
            "cost_per_fcc_median_mbps_usd": "leo_cost_per_mbps_usd",
            "locations_served": "leo_locations_served",
        }
    )


def main() -> None:
    states = gpd.read_file(CENSUS_SHP)
    states = states[~states["STUSPS"].isin(EXCLUDED)].copy()
    states["geometry"] = states["geometry"].simplify(SIMPLIFY_TOLERANCE, preserve_topology=True)
    states = states[["STUSPS", "NAME", "geometry"]].rename(columns={"STUSPS": "state_usps"})

    comparison = pd.read_csv(DATA_DIR / "cost_comparison_v1.csv")
    cheapest = cheapest_per_state(comparison)
    leo = leo_satellite_per_state(comparison)
    bead = pd.read_csv(DATA_DIR / "bead_allocation_v1.csv")[
        ["state_usps", "bead_allocation_usd", "bead_usd_per_gso_location"]
    ]

    merged = (
        states.merge(cheapest, on="state_usps", how="left")
        .merge(leo, on="state_usps", how="left")
        .merge(bead, on="state_usps", how="left")
    )
    merged["has_data"] = merged["state_usps"].isin(comparison["state_usps"].unique())

    DOCS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DOCS_DATA_DIR / "state_map.geojson"
    geojson = json.loads(merged.to_json())
    with open(out_path, "w") as f:
        json.dump(geojson, f, separators=(",", ":"))  # compact, no pretty-print bloat

    size_kb = out_path.stat().st_size / 1024
    covered = merged["has_data"].sum()
    print(f"Wrote {out_path} ({size_kb:.0f} KB, {covered}/{len(merged)} states have data)")


if __name__ == "__main__":
    main()
