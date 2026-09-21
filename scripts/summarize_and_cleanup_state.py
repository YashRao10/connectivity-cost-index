"""Process one state's downloaded FCC zip files into a technology summary,
then delete the raw zips/CSVs immediately -- used when disk space is tight
and holding all 10 states' raw location-level data at once isn't feasible.

Appends to (or creates) data/fcc_technology_summary.csv rather than
overwriting, so states can be processed one at a time and the file
accumulates across runs.

Usage:
    python scripts/summarize_and_cleanup_state.py NY data/raw/fcc/ny_fixed
"""

import sys
import zipfile
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SUMMARY_PATH = DATA_DIR / "fcc_technology_summary.csv"

TECH_CODE_LABELS = {
    10: "DSL (Copper)",
    40: "Cable",
    50: "Fiber",
    60: "GSO Satellite",
    61: "LEO Satellite",
    70: "Unlicensed Fixed Wireless",
    71: "Licensed Fixed Wireless",
    72: "LBR Fixed Wireless",
}

USECOLS = ["technology", "max_advertised_download_speed", "max_advertised_upload_speed", "brand_name"]
DTYPES = {
    "technology": "int8",
    "max_advertised_download_speed": "float32",
    "max_advertised_upload_speed": "float32",
    "brand_name": "category",
}


def process_state(state_usps: str, state_dir: Path) -> pd.DataFrame:
    zips = sorted(state_dir.glob("*.zip"))
    if not zips:
        raise SystemExit(f"No zip files found in {state_dir}")

    frames = []
    extracted_csvs = []
    for zpath in zips:
        with zipfile.ZipFile(zpath) as zf:
            names = [n for n in zf.namelist() if n.endswith(".csv")]
            zf.extractall(state_dir, members=names)
            for n in names:
                extracted_csvs.append(state_dir / n)

    for csv_path in extracted_csvs:
        df = pd.read_csv(csv_path, usecols=USECOLS, dtype=DTYPES)
        frames.append(df)

    all_df = pd.concat(frames, ignore_index=True)
    all_df["technology_label"] = all_df["technology"].map(TECH_CODE_LABELS).fillna("Other")

    summary = (
        all_df.groupby("technology_label", observed=True)
        .agg(
            locations_served=("technology_label", "count"),
            unique_providers=("brand_name", "nunique"),
            median_max_down_mbps=("max_advertised_download_speed", "median"),
            median_max_up_mbps=("max_advertised_upload_speed", "median"),
        )
        .reset_index()
    )
    summary.insert(0, "state_usps", state_usps)

    # Clean up raw files immediately -- this is the whole point of processing
    # one state at a time rather than downloading all 10 states first.
    for zpath in zips:
        zpath.unlink()
    for csv_path in extracted_csvs:
        csv_path.unlink()
    try:
        state_dir.rmdir()
    except OSError:
        pass  # not empty for some reason, leave it rather than force-delete

    return summary


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python scripts/summarize_and_cleanup_state.py <STATE_USPS> <state_dir>")
    state_usps, state_dir = sys.argv[1], Path(sys.argv[2])

    new_summary = process_state(state_usps, state_dir)

    if SUMMARY_PATH.exists():
        existing = pd.read_csv(SUMMARY_PATH)
        existing = existing[existing["state_usps"] != state_usps]  # replace if rerun
        combined = pd.concat([existing, new_summary], ignore_index=True)
    else:
        combined = new_summary

    combined = combined.sort_values(["state_usps", "locations_served"], ascending=[True, False])
    combined.to_csv(SUMMARY_PATH, index=False)
    print(new_summary.sort_values("locations_served", ascending=False).to_string(index=False))
    print(f"\nAppended {state_usps} to {SUMMARY_PATH}, raw files deleted")
