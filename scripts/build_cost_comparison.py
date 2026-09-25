"""v1 deliverable: cost-per-Mbps by technology, combining published pricing
with FCC's real per-state median advertised speeds (not just marketing copy).

Inputs:
    data/pricing_snapshot.csv       -- published plan pricing (manual research)
    data/fcc_technology_summary.csv -- output of scripts/load_fcc_broadband.py
    data/state_top_providers.csv    -- largest Fiber/Cable/DSL provider per state
    data/provider_pricing.csv       -- that provider's cheapest published plan

Fiber, Cable, and DSL are priced from each state's own largest provider for
that technology (price_basis = "state_provider"). Those are the technologies
where the provider, and so the price, genuinely changes from state to state.
If the state's top provider has no published price (e.g. AT&T, which stopped
selling DSL to new customers in 2023), the national cheapest plan is used
instead (price_basis = "national"). Satellite and licensed fixed wireless
(Starlink, Viasat, Verizon 5G Home, T-Mobile) are sold at one national price,
so they always use the national plan.

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
# Fixed wireless is split into licensed/unlicensed/LBR (FCC codes 71/70/72) --
# an earlier version collapsed these into one "fixed_wireless" slug and
# compared Verizon 5G Home / T-Mobile Home Internet pricing (both licensed
# spectrum) against the wrong, much smaller FCC population (unlicensed only).
# Licensed dwarfs the other two by 100-1000x in all 3 states, so keeping them
# split matters, not just for completeness.
TECH_TO_FCC_LABEL = {
    "leo_satellite": "LEO Satellite",
    "gso_satellite": "GSO Satellite",
    "cable": "Cable",
    "fiber": "Fiber",
    "dsl": "DSL (Copper)",
    "licensed_fixed_wireless": "Licensed Fixed Wireless",
    "unlicensed_fixed_wireless": "Unlicensed Fixed Wireless",
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


STATE_PRICED_TECHS = {"Fiber", "Cable", "DSL (Copper)"}


def load_state_provider_pricing() -> pd.DataFrame:
    """One row per (state, technology) for the state-priced technologies,
    only where the state's top provider has a published price."""
    top = pd.read_csv(DATA_DIR / "state_top_providers.csv")
    prices = pd.read_csv(DATA_DIR / "provider_pricing.csv")
    prices = prices.rename(columns={"technology": "technology_label"})
    merged = top.rename(columns={"technology": "technology_label"}).merge(
        prices[["provider", "technology_label", "plan", "monthly_price_usd", "advertised_mbps_down"]],
        on=["provider", "technology_label"],
        how="left",
    )
    merged = merged[merged["technology_label"].isin(STATE_PRICED_TECHS)]
    return merged.dropna(subset=["monthly_price_usd"])[
        ["state_usps", "technology_label", "provider", "plan", "monthly_price_usd", "advertised_mbps_down"]
    ]


def build_comparison() -> pd.DataFrame:
    pricing = load_pricing_by_technology()
    fcc = pd.read_csv(DATA_DIR / "fcc_technology_summary.csv")

    merged = fcc.merge(pricing, on="technology_label", how="left")
    merged["price_basis"] = merged["monthly_price_usd"].notna().map({True: "national", False: None})
    state = load_state_provider_pricing().set_index(["state_usps", "technology_label"])
    key = pd.MultiIndex.from_frame(merged[["state_usps", "technology_label"]])
    hit = key.isin(state.index)
    for col in ["provider", "plan", "monthly_price_usd", "advertised_mbps_down"]:
        merged.loc[hit, col] = state.loc[key[hit], col].to_numpy()
    merged.loc[hit, "price_basis"] = "state_provider"
    merged["cost_per_advertised_mbps_usd"] = (
        merged["monthly_price_usd"] / merged["advertised_mbps_down"]
    ).round(3)
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
        "price_basis",
    ]
    print(result[cols].to_string(index=False))
    out_path = DATA_DIR / "cost_comparison_v1.csv"
    result.to_csv(out_path, index=False)
    print(f"\nWrote {out_path}")
