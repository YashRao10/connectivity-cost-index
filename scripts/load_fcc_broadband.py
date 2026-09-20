"""Load and summarize FCC National Broadband Map bulk CSV downloads.

No API key needed. Download source (manual, free, no registration):
    https://broadbandmap.fcc.gov/data-download -> pick state(s) + "Fixed Broadband"
    + as-of date -> download CSV (zipped per state).

The FCC data-download portal does NOT give one combined "Fixed Broadband" CSV
per state -- it gives one zip per technology per state (e.g. 8 files per
state: Cable, Copper, Fiber, GSO Satellite, Licensed/Unlicensed/LBR Fixed
Wireless, NGSO Satellite). Extract them all under data/raw/fcc/ in nested
per-state subfolders, e.g.:
    data/raw/fcc/nj_fixed/bdc_34_NGSOSatellite_fixed_broadband_D25_*.csv
    data/raw/fcc/nc_fixed/bdc_34_Cable_fixed_broadband_D25_*.csv
    data/raw/fcc/mt_fixed/...
This script globs recursively so the exact subfolder layout doesn't matter,
as long as everything is unzipped under RAW_DIR.

Technology codes (FCC BDC schema) -- confirmed against a real header:
    10 = Copper (DSL)
    40 = Cable
    50 = Fiber to the premises
    60 = GSO Satellite (geostationary)
    61 = Non-GSO Satellite (LEO, e.g. Starlink)
    70 = Unlicensed Fixed Wireless
    71 = Licensed Fixed Wireless
    72 = Licensed-by-Rule (LBR) Fixed Wireless

Fixed wireless is NOT one category -- 70/71/72 are three separate FCC codes
with very different population sizes (in NJ/NC/MT: 71 dwarfs 70 and 72 by
100-1000x -- Licensed Fixed Wireless is Verizon 5G Home / T-Mobile Home
Internet, i.e. the actual consumer 5G-home-internet technology, while 70 is
small WISP-style unlicensed service). An earlier version of this script only
mapped 70 and let 71/72 fall into "Other", which silently misrepresented
"Other" as noise when it was actually the largest fixed-wireless population
by far. Kept split (not collapsed into one "Fixed Wireless" bucket) because
licensed vs. unlicensed spectrum has real performance/reliability
implications worth keeping visible.

Confirmed columns (from bdc_34_NGSOSatellite_fixed_broadband_D25_15sep2026.csv,
NJ): frn, provider_id, brand_name, location_id, technology,
max_advertised_download_speed, max_advertised_upload_speed, low_latency,
business_residential_code, state_usps, block_geoid, h3_res8_id.
The `technology` column is populated per-row (not just implied by filename),
so grouping by it directly is reliable.
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
    70: "Unlicensed Fixed Wireless",
    71: "Licensed Fixed Wireless",
    72: "LBR Fixed Wireless",
}


# Only pull the columns the summary actually needs -- the full files also
# carry frn, location_id, h3_res8_id, low_latency, business_residential_code,
# block_geoid, provider_id, which roughly double the row width for no benefit
# here and were what blew memory on a 61M-row concat (crashed with a
# MemoryError on df.copy() inside summarize_by_technology, desktop had enough
# disk but not enough RAM to hold the full frame plus a copy of it).
USECOLS = [
    "technology",
    "max_advertised_download_speed",
    "max_advertised_upload_speed",
    "brand_name",
    "state_usps",
]
DTYPES = {
    "technology": "int8",
    "max_advertised_download_speed": "float32",
    "max_advertised_upload_speed": "float32",
    "brand_name": "category",
    "state_usps": "category",
}


def load_state_csvs() -> pd.DataFrame:
    files = sorted(RAW_DIR.rglob("*.csv"))
    if not files:
        raise FileNotFoundError(
            f"No CSVs found under {RAW_DIR}. Download + unzip per-technology "
            "state files from https://broadbandmap.fcc.gov/data-download first."
        )
    frames = []
    for f in files:
        header = pd.read_csv(f, nrows=0).columns
        usecols = [c for c in USECOLS if c in header]
        dtypes = {c: DTYPES[c] for c in usecols if c != "state_usps"}
        df = pd.read_csv(f, usecols=usecols, dtype=dtypes)
        if "state_usps" not in df.columns:
            # Fall back to the parent folder name (e.g. "nj_fixed") if a
            # future vintage drops the state_usps column.
            df["state_usps"] = f.parent.name.split("_")[0].upper()
        df["state_usps"] = df["state_usps"].astype("category")
        frames.append(df)
    # concat with categoricals: pandas unions categories automatically here
    return pd.concat(frames, ignore_index=True)


def summarize_by_technology(df: pd.DataFrame) -> pd.DataFrame:
    # No .copy() -- this column assignment doesn't need one, and copying the
    # full frame is what exhausted memory on the 61M-row concat.
    df["technology_label"] = df["technology"].map(TECH_CODE_LABELS).fillna("Other")
    return (
        df.groupby(["state_usps", "technology_label"], observed=True)
        .agg(
            locations_served=("technology", "count"),
            unique_providers=("brand_name", "nunique"),
            median_max_down_mbps=("max_advertised_download_speed", "median"),
            median_max_up_mbps=("max_advertised_upload_speed", "median"),
        )
        .reset_index()
        .sort_values(["state_usps", "locations_served"], ascending=[True, False])
    )


if __name__ == "__main__":
    raw = load_state_csvs()
    summary = summarize_by_technology(raw)
    print(summary.to_string(index=False))
    out_path = RAW_DIR.parent.parent / "fcc_technology_summary.csv"
    summary.to_csv(out_path, index=False)
    print(f"\nWrote {out_path}")
