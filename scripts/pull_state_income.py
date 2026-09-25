"""Pull median household income by state from FRED (St. Louis Fed).

Series MEHOINUS{ST}A646N: median household income in current dollars, from
the Census Bureau's Current Population Survey (CPS ASEC), annual. FRED's
graph CSV endpoint needs no API key (the Census API itself now does).
Used for the affordability layer: a plan's monthly price as a share of the
state's median monthly household income.

Output:
    data/state_median_income.csv  (state_usps, year, median_household_income_usd, series_id)

Usage:
    python scripts/pull_state_income.py
"""

import io
import time
from pathlib import Path

import pandas as pd
import requests

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"

STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA", "HI", "ID",
    "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO",
    "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA",
    "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
]


def latest_value(series: str) -> tuple[int, float]:
    resp = requests.get(URL.format(series=series), timeout=30)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text))
    df.columns = ["date", "value"]
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    row = df.dropna().iloc[-1]
    return int(str(row["date"])[:4]), float(row["value"])


def main() -> None:
    rows = []
    for st in STATES:
        series = f"MEHOINUS{st}A646N"
        year, value = latest_value(series)
        rows.append({"state_usps": st, "year": year, "median_household_income_usd": value, "series_id": series})
        time.sleep(0.3)
    out = pd.DataFrame(rows)
    out_path = DATA_DIR / "state_median_income.csv"
    out.to_csv(out_path, index=False)
    print(out["year"].value_counts().to_string())
    print(f"Wrote {out_path} ({len(out)} states)")


if __name__ == "__main__":
    main()
