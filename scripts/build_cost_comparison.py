"""v1 deliverable: cost-per-Mbps by technology, combining published pricing
with FCC's real per-state median advertised speeds (not just marketing copy).

Inputs:
    data/pricing_snapshot.csv       -- published plan pricing (manual research)
    data/fcc_technology_summary.csv -- output of scripts/load_fcc_broadband.py

Output:
    data/cost_comparison_v1.csv

Note on methodology: pricing_snapshot's advertised_mbps_down is what the
provider's marketing page lists for that specific plan. fcc_technology_summary's
median_max_down_mbps is the FCC BDC median across every location a provider
reports serving that technology in a state -- these can diverge (e.g. FCC LEO
Satellite showed 280/30 Mbps across all 3 states, higher than any individual
Starlink residential tier in pricing_snapshot, likely reflecting a plan/tier
not yet captured there, or FCC's own reporting methodology). Both columns are
kept in the output so the gap is visible rather than silently resolved.
"""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Map pricing_snapshot's technology slugs to fcc_technology_summary's labels.
TECH_TO_FCC_LABEL = {
    "leo_satellite": "LEO Satellite",
    "gso_satellite": "GSO Satellite",
    "cable": "Cable",
    "fiber": "Fiber",
    "dsl": "DSL (Copper)",
    "fixed_wireless": "Fixed Wireless",
    # direct_to_cell has no FCC fixed-broadband counterpart -- it's a mobile
    # add-on, not a fixed technology, so it's excluded from this join.
}


def load_pricing_by_technology() -> pd.DataFrame:
    pricing = pd.read_csv(DATA_DIR / "pricing_snapshot.csv")
    pricing = pricing.dropna(subset=["monthly_price_usd", "advertised_mbps_down"])
    pricing["technology_label"] = pricing["technology"].map(TECH_TO_FCC_LABEL)
    pricing = pricing.dropna(subset=["technology_label"])
    # Use the cheapest plan per technology as the representative price point
    # (a household picks the cheapest plan that meets their needs, not the
    # average of every tier a provider offers).
    idx = pricing.groupby("technology_label")["monthly_price_usd"].idxmin()
    return pricing.loc[
        idx,
        [
            "technology_label",
            "provider",
            "plan",
            "monthly_price_usd",
            "advertised_mbps_down",
            "cost_per_mbps_usd",
        ],
    ].rename(columns={"cost_per_mbps_usd": "cost_per_advertised_mbps_usd"})


def build_comparison() -> pd.DataFrame:
    pricing = load_pricing_by_technology()
    fcc = pd.read_csv(DATA_DIR / "fcc_technology_summary.csv")

    merged = fcc.merge(pricing, on="technology_label", how="left")
    merged["cost_per_fcc_median_mbps_usd"] = (
        merged["monthly_price_usd"] / merged["median_max_down_mbps"]
    ).round(3)
    return merged.sort_values(["state_usps", "cost_per_fcc_median_mbps_usd"])


if __name__ == "__main__":
    result = build_comparison()
    cols = [
        "state_usps",
        "technology_label",
        "provider",
        "monthly_price_usd",
        "median_max_down_mbps",
        "cost_per_fcc_median_mbps_usd",
        "unique_providers",
        "locations_served",
    ]
    print(result[cols].to_string(index=False))
    out_path = DATA_DIR / "cost_comparison_v1.csv"
    result.to_csv(out_path, index=False)
    print(f"\nWrote {out_path}")
