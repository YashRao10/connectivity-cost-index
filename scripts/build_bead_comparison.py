"""v2 BEAD/policy layer: implied BEAD dollars per GSO-satellite-served
location, by state -- now using confirmed post-restructuring "Benefit of
the Bargain" provisional awards for all 50 states + DC, replacing v1's
stale June 2023 initial allocation (flagged and callout-ed on the site
after it was found to overstate actual funding by 50-90% in verified
spot checks).

Source: NTIA restructured BEAD in 2025 ("Benefit of the Bargain"); both
the original 2023 allocation and the 2025 provisional award are compiled
here from a single consistent secondary source (telecompetitor.com's
"Updated, Comprehensive List: BEAD Benefit of the Bargain Provisional
Awards"), cross-checked against the handful of states independently
verified via direct NTIA/state-broadband-office sources during the v1
caveat fix (NJ, TX, CO all matched within ~1-2%). NTIA's own
allocation-totals page blocks automated fetches, so this is hand-compiled
and dated -- re-verify before treating any single figure as exact, and
note these are PROVISIONAL awards (administrative review ongoing per
state as of compilation), not necessarily each state's final locked-in
number.

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

Output: data/bead_allocation_v2.csv
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

# (original 2023 allocation, 2025 "Benefit of the Bargain" provisional award),
# both in USD. Compiled 2026-09 from telecompetitor.com's comprehensive list.
BEAD_AWARDS_USD = {
    "AL": (1_400_000_000, 530_743_198),
    "AK": (1_000_000_000, 483_201_643),
    "AZ": (993_000_000, 512_129_677),
    "AR": (1_000_000_000, 308_328_089),
    "CA": (1_900_000_000, 1_574_861_927),
    "CO": (827_000_000, 397_418_888),
    "CT": (144_000_000, 7_216_501),
    "DE": (108_000_000, 13_374_777),
    "FL": (1_160_000_000, 291_117_656),
    "GA": (1_310_000_000, 309_602_817),
    "HI": (149_000_000, 94_869_000),
    "ID": (583_000_000, 436_151_356),
    "IL": (1_000_000_000, 990_645_134),
    "IN": (868_000_000, 486_309_855),
    "IA": (415_000_000, 221_282_630),
    "KS": (451_000_000, 252_629_596),
    "KY": (1_000_000_000, 376_926_543),
    "LA": (1_360_000_000, 499_079_587),
    "ME": (272_000_000, 109_412_662),
    "MD": (268_000_000, 78_106_623),
    "MA": (147_000_000, 18_654_558),
    "MI": (1_600_000_000, 919_106_714),
    "MN": (652_000_000, 377_046_315),
    "MS": (1_200_000_000, 567_165_372),
    "MO": (1_740_000_000, 793_326_180),
    "MT": (629_000_000, 403_758_268),
    "NE": (405_000_000, 43_844_548),
    "NV": (417_000_000, 169_749_806),
    "NH": (197_000_000, 19_305_223),
    "NJ": (264_000_000, 63_551_464),
    "NM": (675_000_000, 432_974_698),
    "NY": (665_000_000, 391_097_989),
    "NC": (1_530_000_000, 408_511_175),
    "ND": (130_000_000, 6_770_073),
    "OH": (794_000_000, 277_114_388),
    "OK": (797_000_000, 493_318_564),
    "OR": (689_000_000, 620_728_287),
    "PA": (1_160_000_000, 793_494_747),
    "RI": (109_000_000, 16_137_983),
    "SC": (551_000_000, 41_358_389),
    "SD": (207_000_000, 72_816_060),
    "TN": (813_000_000, 203_311_189),
    "TX": (3_310_000_000, 1_271_233_725),
    "UT": (317_000_000, 231_292_922),
    "VT": (229_000_000, 118_993_040),
    "VA": (1_480_000_000, 613_277_638),
    "WA": (1_230_000_000, 849_894_572),
    "DC": (100_700_000, 996_099),
    "WV": (1_211_000_000, 624_671_277),
    "WI": (1_060_000_000, 690_445_792),
    "WY": (348_000_000, 198_442_261),
}


def build_comparison() -> pd.DataFrame:
    fcc = pd.read_csv(DATA_DIR / "fcc_technology_summary.csv")
    gso = fcc[fcc.technology_label == "GSO Satellite"].set_index("state_usps")["locations_served"]
    starlink_monthly_usd = load_cheapest_starlink_monthly_usd()

    rows = []
    for state, (original, provisional) in BEAD_AWARDS_USD.items():
        locations = gso.get(state)
        pct_change = round((provisional - original) / original * 100, 1)
        usd_per_location = round(provisional / locations, 2) if locations else None
        rows.append(
            {
                "state_usps": state,
                "original_allocation_usd": original,
                "provisional_award_usd": provisional,
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
    out_path = DATA_DIR / "bead_allocation_v2.csv"
    result.to_csv(out_path, index=False)
    print(f"\nWrote {out_path}")
