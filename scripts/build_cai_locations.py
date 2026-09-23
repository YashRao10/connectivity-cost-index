"""Build a web-sized point dataset of BEAD-funded Community Anchor
Institutions (CAIs) for the site's point-density map -- schools, libraries,
health clinics, fire/public-safety, public housing, and government
buildings that will receive BEAD-funded broadband service, each with a real
lat/lon.

Input source: same NTIA BEAD Final Proposal bulk download used by
build_bead_final_proposal.py (broadbandexpanded.com/funding/
beadfinalproposaldata), specifically CAI_20260827.csv -- one row per funded
CAI site, with entity_name/address/city/state/zip, lat/lon, the technology
planned for it, and a single-letter `type` code.

Type-code labels below are INFERRED from entity_name patterns (checked a
random sample of ~8 names per code), not from an official published
codebook -- broadbandexpanded.com's own funding page has no data
dictionary for this field, and a search turned up no bundled one either.
The mapping is a confident best-guess matching NTIA's standard 8-category
CAI taxonomy (school/library/health/public-safety/housing/government/
community-support/higher-ed), not a verified 1:1 decode -- flagged as such
in the site copy too, not just here.

Excludes: rows with null lat/lon (3,015 of 25,909) or an exact (0,0)
placeholder (21 more) -- neither is a real, usable coordinate. Also
excludes non-state territories (AS, GU) from the point-map output for the
same reason build_state_map_data.py excludes PR/GU/VI/AS/MP from the
choropleth: d3.geoAlbersUsa() only repositions AK/HI, not the other
territories, so plotting AS/GU coordinates through it would place them
somewhere wrong on the map rather than just failing loudly. Their counts
are still surfaced in the summary stats, just not on the map itself.

Output:
    docs/data/cai_locations.json (compact [lat, lon, type_code, state_usps]
        arrays, not objects -- name/address/technology omitted, not needed
        for a density map and meaningfully larger)
"""

import json
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DOCS_DATA_DIR = Path(__file__).resolve().parent.parent / "docs" / "data"
RAW_DIR = DATA_DIR / "raw" / "bead"

# Non-state territories AlbersUSA can't place correctly (see module docstring).
MAP_EXCLUDED_TERRITORIES = {"AS", "GU"}

TYPE_LABELS = {
    "S": "School",
    "L": "Library",
    "H": "Health clinic",
    "F": "Public safety (fire/police)",
    "P": "Public housing",
    "G": "Government building",
    "C": "Community support org",
}

# Rounding to 4 decimal places (~11m precision) is plenty for a page-scale
# point map and meaningfully shrinks the output vs. full float precision.
COORD_DECIMALS = 4


def load_cai_locations(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    df = pd.read_csv(
        raw_dir / "CAI_20260827.csv",
        usecols=["type", "state", "latitude", "longitude"],
    )
    df = df.dropna(subset=["latitude", "longitude", "type"])
    df = df[(df["latitude"] != 0.0) | (df["longitude"] != 0.0)]
    return df


def build_point_records(cai: pd.DataFrame) -> list:
    # Output is [lat, lon, type_code, state_usps] -- the human-readable
    # label lives once in TYPE_LABELS (included in the JSON payload) rather
    # than repeated on all ~23K rows.
    mappable = cai[~cai["state"].isin(MAP_EXCLUDED_TERRITORIES)].copy()
    mappable["latitude"] = mappable["latitude"].round(COORD_DECIMALS)
    mappable["longitude"] = mappable["longitude"].round(COORD_DECIMALS)
    return mappable[["latitude", "longitude", "type", "state"]].values.tolist()


def build_summary(cai: pd.DataFrame) -> dict:
    type_counts = cai["type"].map(TYPE_LABELS).fillna(cai["type"]).value_counts().to_dict()
    territory_counts = (
        cai[cai["state"].isin(MAP_EXCLUDED_TERRITORIES)]["state"].value_counts().to_dict()
    )
    return {
        "total_usable_points": len(cai),
        "mapped_points": len(cai[~cai["state"].isin(MAP_EXCLUDED_TERRITORIES)]),
        "type_counts": type_counts,
        "territories_excluded_from_map": territory_counts,
        "states_covered": sorted(cai["state"].unique().tolist()),
    }


def main() -> None:
    raw = pd.read_csv(RAW_DIR / "CAI_20260827.csv", usecols=["type"])
    total_rows = len(raw)

    cai = load_cai_locations()
    points = build_point_records(cai)
    summary = build_summary(cai)

    DOCS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DOCS_DATA_DIR / "cai_locations.json"
    payload = {"type_labels": TYPE_LABELS, "points": points, "summary": summary}
    with open(out_path, "w") as f:
        json.dump(payload, f, separators=(",", ":"))

    size_kb = out_path.stat().st_size / 1024
    excluded_no_coords = total_rows - len(cai)
    print(
        f"Wrote {out_path} ({size_kb:.0f} KB, {len(points)} mappable points, "
        f"{excluded_no_coords} rows excluded for missing/placeholder coordinates, "
        f"{sum(summary['territories_excluded_from_map'].values())} more excluded "
        f"as non-state territories not plottable via AlbersUSA)"
    )
    print(f"Type breakdown: {summary['type_counts']}")


if __name__ == "__main__":
    main()
