"""Load and summarize FCC National Broadband Map bulk CSV downloads.

No API key needed. Download source (manual, free, no registration):
    https://broadbandmap.fcc.gov/data-download -> pick state(s) + "Fixed Broadband"
    + as-of date -> download CSV (zipped per state).

Save the extracted per-state CSVs into data/raw/fcc/ before running this script,
e.g. data/raw/fcc/nc_fixed_broadband.csv

Technology codes (FCC BDC schema):
    10 = Copper (DSL)
    40 = Cable
    50 = Fiber to the premises
    60 = GSO Satellite (geostationary)
    61 = Non-GSO Satellite (LEO, e.g. Starlink)
    70 = Terrestrial Fixed Wireless

Key columns used here: technology, max_advertised_download_speed,
max_advertised_upload_speed, provider_id / brand_name, block_geoid.
Exact column names should be confirmed against the downloaded CSV header
(FCC has renamed a few fields across BDC vintages).
"""

from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "fcc"

TECH_CODE_LABELS = {
    10: "DSL (Copper)",
    40: "Cable",
    50: "Fiber",
    60: "GSO Satellite",
    61: "LEO Satellite",
    70: "Fixed Wireless",
}


def load_state_csvs() -> pd.DataFrame:
    files = sorted(RAW_DIR.glob("*.csv"))
    if not files:
        raise FileNotFoundError(
            f"No CSVs found in {RAW_DIR}. Download state files from "
            "https://broadbandmap.fcc.gov/data-download and place them there first."
        )
    frames = [pd.read_csv(f) for f in files]
    return pd.concat(frames, ignore_index=True)


def summarize_by_technology(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["technology_label"] = df["technology"].map(TECH_CODE_LABELS).fillna("Other")
    return (
        df.groupby("technology_label")
        .agg(
            locations_served=("technology", "count"),
            median_max_down_mbps=("max_advertised_download_speed", "median"),
            median_max_up_mbps=("max_advertised_upload_speed", "median"),
        )
        .reset_index()
        .sort_values("locations_served", ascending=False)
    )


if __name__ == "__main__":
    raw = load_state_csvs()
    summary = summarize_by_technology(raw)
    print(summary.to_string(index=False))
    out_path = RAW_DIR.parent.parent / "fcc_technology_summary.csv"
    summary.to_csv(out_path, index=False)
    print(f"\nWrote {out_path}")
