"""Pull the US Census Bureau's cartographic boundary shapefile for states.

Public, no auth needed: https://www2.census.gov/geo/tiger/GENZ2023/
Used by scripts/load_ookla_regional.py for a real point-in-polygon state
join (replaces the old bounding-box approximation).

Usage:
    python scripts/pull_census_shapes.py
"""

import zipfile
from pathlib import Path

import requests

URL = "https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_state_20m.zip"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "census"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = OUT_DIR / "cb_states.zip"
    shp_path = OUT_DIR / "cb_2023_us_state_20m.shp"

    if shp_path.exists():
        print(f"Already have {shp_path}")
        return

    print(f"Downloading {URL}")
    resp = requests.get(URL, timeout=60)
    resp.raise_for_status()
    zip_path.write_bytes(resp.content)

    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(OUT_DIR)
    print(f"Extracted to {OUT_DIR}")


if __name__ == "__main__":
    main()
