"""Build a simplified, web-sized GeoJSON of US states for the site's
choropleth map, annotated with our comparison metrics. As of the v2 BEAD
rebuild (verified "Benefit of the Bargain" provisional awards, all 50
states + DC), every mapped state has real data -- no more grey "no data"
states within the map's coverage.

Input: data/raw/census/cb_2023_us_state_20m.shp (via pull_census_shapes.py)
       data/cost_comparison_v1.csv
       data/bead_allocation_v2.csv
Output: docs/data/state_map.geojson

Excludes only non-state territories (PR, GU, VI, AS, MP) -- the site's
d3.geoAlbersUsa() projection (docs/index.html) natively repositions AK and
HI as bottom-left insets specifically to solve the antimeridian-wrap /
disconnected-islands problem, so there's no reason to filter them out of
the source geometry; AlbersUSA has no equivalent inset handling for the
non-contiguous territories, which is why those stay excluded. All 50
states + DC are plotted.
"""

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DOCS_DATA_DIR = Path(__file__).resolve().parent.parent / "docs" / "data"
CENSUS_SHP = DATA_DIR / "raw" / "census" / "cb_2023_us_state_20m.shp"

EXCLUDED = {"PR", "GU", "VI", "AS", "MP"}
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
    bead = pd.read_csv(DATA_DIR / "bead_allocation_v2.csv")[
        ["state_usps", "provisional_award_usd", "provisional_usd_per_gso_location"]
    ].rename(
        columns={
            "provisional_award_usd": "bead_allocation_usd",
            "provisional_usd_per_gso_location": "bead_usd_per_gso_location",
        }
    )

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
