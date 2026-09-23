"""v3 BEAD/policy layer: implied BEAD dollars per GSO-satellite-served
location, by state -- now using per-state provisional awards verified
against NTIA's own official Final Proposal overview PDFs wherever possible,
replacing v2's single telecompetitor.com secondary compilation (which
checked out as unreliable: only 12 of 27 spot-checked states matched NTIA's
real numbers within 2%, and Hawaii was 3x overstated -- $94.87M vs. the
real $30.67M). See scripts/build_bead_provisional_awards.py for the full
sourcing methodology (NTIA-PDF-verified > granular-layer fallback >
telecompetitor.com legacy fallback, in that priority order) and
docs/BEAD_LAYER_SCOPE.md for how this was discovered.

The original 2023 June allocation (ORIGINAL_ALLOCATION_USD below) is
unaffected by this fix -- spot-checked against the same NTIA PDFs and found
accurate within ~0.1% (a simpler, more stable figure than the post-
restructuring provisional award), so it's kept as the same hand-compiled
dict v1/v2 used.

Methodology: GSO Satellite locations_served (from fcc_technology_summary.csv)
is used as a proxy for "underserved" locations, not a precise BEAD-eligibility
count -- see docs/BEAD_LAYER_SCOPE.md for the full reasoning and caveats.

Also adds a Starlink-cost cross-reference: how many months of the cheapest
current Starlink residential plan (sourced from data/pricing_snapshot.csv,
same "cheapest plan" selection build_cost_comparison.py uses) the per-location
provisional award figure is worth. This is explicitly NOT a claim that BEAD
money could or should just buy Starlink subscriptions instead -- BEAD funds
permanent infrastructure, not a recurring service, and the location-count
denominator is already a loose proxy (see above). It's a scale sanity-check
on a number that's otherwise hard to interpret in isolation, nothing more --
see docs/BEAD_LAYER_SCOPE.md and the site's caveat text for the full framing.

Output: data/bead_allocation_v2.csv (filename kept for site/script
continuity even though the provisional-award sourcing is now v3 --
renaming would touch every downstream reference for no functional gain).
"""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_cheapest_starlink_monthly_usd() -> float:
    pricing = pd.read_csv(DATA_DIR / "pricing_snapshot.csv")
    starlink = pricing[
        (pricing.technology == "leo_satellite") & (pricing.provider == "Starlink")
    ].dropna(subset=["monthly_price_usd"])
    return float(starlink["monthly_price_usd"].min())


# June 2023 initial BEAD allocation, in USD. Compiled 2026-09 from
# telecompetitor.com's comprehensive list; spot-checked against NTIA's own
# per-state overview PDFs during the 2026-09-22/23 provisional-award
# investigation and found accurate within ~0.1% (e.g. Alabama: $1,400,000,000
# here vs. NTIA's own $1,401,221,902) -- unlike the provisional award, this
# figure did not need replacing.
ORIGINAL_ALLOCATION_USD = {
    "AL": 1_400_000_000, "AK": 1_000_000_000, "AZ": 993_000_000, "AR": 1_000_000_000,
    "CA": 1_900_000_000, "CO": 827_000_000, "CT": 144_000_000, "DE": 108_000_000,
    "FL": 1_160_000_000, "GA": 1_310_000_000, "HI": 149_000_000, "ID": 583_000_000,
    "IL": 1_000_000_000, "IN": 868_000_000, "IA": 415_000_000, "KS": 451_000_000,
    "KY": 1_000_000_000, "LA": 1_360_000_000, "ME": 272_000_000, "MD": 268_000_000,
    "MA": 147_000_000, "MI": 1_600_000_000, "MN": 652_000_000, "MS": 1_200_000_000,
    "MO": 1_740_000_000, "MT": 629_000_000, "NE": 405_000_000, "NV": 417_000_000,
    "NH": 197_000_000, "NJ": 264_000_000, "NM": 675_000_000, "NY": 665_000_000,
    "NC": 1_530_000_000, "ND": 130_000_000, "OH": 794_000_000, "OK": 797_000_000,
    "OR": 689_000_000, "PA": 1_160_000_000, "RI": 109_000_000, "SC": 551_000_000,
    "SD": 207_000_000, "TN": 813_000_000, "TX": 3_310_000_000, "UT": 317_000_000,
    "VT": 229_000_000, "VA": 1_480_000_000, "WA": 1_230_000_000, "DC": 100_700_000,
    "WV": 1_211_000_000, "WI": 1_060_000_000, "WY": 348_000_000,
}


def load_provisional_awards() -> pd.DataFrame:
    path = DATA_DIR / "bead_provisional_awards_v3.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found -- run scripts/build_bead_provisional_awards.py first."
        )
    return pd.read_csv(path).set_index("state_usps")


def build_comparison() -> pd.DataFrame:
    fcc = pd.read_csv(DATA_DIR / "fcc_technology_summary.csv")
    gso = fcc[fcc.technology_label == "GSO Satellite"].set_index("state_usps")["locations_served"]
    starlink_monthly_usd = load_cheapest_starlink_monthly_usd()
    provisional = load_provisional_awards()

    rows = []
    for state, original in ORIGINAL_ALLOCATION_USD.items():
        award_row = provisional.loc[state]
        provisional_usd = award_row["provisional_award_usd"]
        locations = gso.get(state)
        pct_change = round((provisional_usd - original) / original * 100, 1)
        usd_per_location = round(provisional_usd / locations, 2) if locations else None
        rows.append(
            {
                "state_usps": state,
                "original_allocation_usd": original,
                "provisional_award_usd": provisional_usd,
                "provisional_award_source": award_row["source"],
                "pct_change_vs_original": pct_change,
                "gso_satellite_locations": locations,
                "provisional_usd_per_gso_location": usd_per_location,
                "provisional_per_location_months_of_starlink": (
                    round(usd_per_location / starlink_monthly_usd, 1)
                    if usd_per_location is not None
                    else None
                ),
            }
        )
    return pd.DataFrame(rows).sort_values("provisional_usd_per_gso_location")


if __name__ == "__main__":
    result = build_comparison()
    print(result.to_string(index=False))
    print(f"\nMedian cut vs. original allocation: {result['pct_change_vs_original'].median()}%")
    print(f"\nProvisional award source breakdown:\n{result['provisional_award_source'].value_counts()}")
    out_path = DATA_DIR / "bead_allocation_v2.csv"
    result.to_csv(out_path, index=False)
    print(f"\nWrote {out_path}")
