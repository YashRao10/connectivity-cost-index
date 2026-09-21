"""v1 BEAD/policy layer: implied BEAD dollars per GSO-satellite-served
location, by state -- a first pass at connecting subsidy dollars to the
market-layer findings already in this project.

Source for allocation amounts: NTIA's June 2023 BEAD state allocation
announcement (https://www.ntia.gov/funding-programs/internet-all/
broadband-equity-access-and-deployment-bead-program/program-documentation/
state-allocation-totals), a static one-time figure per state -- NOT the
same as final approved subgrantee/project awards, which have since evolved
per-state through the Final Proposal process. Hardcoded here rather than
scraped since the NTIA page blocks automated fetches (403); update by hand
if a more current reference is needed.

Methodology: GSO Satellite locations_served (from fcc_technology_summary.csv)
is used as a proxy for "underserved" locations, not a precise BEAD-eligibility
count. This has real grounding, not just a starting point: BEAD's own
definition of "unserved"/"underserved" explicitly treats satellite as
non-qualifying/lower-tier service in most cases, so places where GSO
satellite shows significant coverage plausibly correlate with places lacking
adequate terrestrial options. It is still an approximation -- a location can
have both GSO satellite and another technology available, and this proxy
doesn't distinguish "GSO satellite is the only option" from "GSO satellite
is one of several options."

Output: data/bead_allocation_v1.csv
"""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# NTIA BEAD state allocation totals, announced 2023-06-26. Static figures.
BEAD_ALLOCATION_USD = {
    "NJ": 263_689_548.65,
    "NC": 1_532_999_481.15,
    "MT": 628_973_798.59,
    "CA": 1_864_136_508.93,
    "TX": 3_312_616_455.45,
    "NY": 664_618_251.49,
    "OH": 793_688_107.63,
    "FL": 1_169_947_392.70,
    "WA": 1_227_742_066.30,
    "CO": 826_522_650.41,
}


def build_comparison() -> pd.DataFrame:
    fcc = pd.read_csv(DATA_DIR / "fcc_technology_summary.csv")
    gso = fcc[fcc.technology_label == "GSO Satellite"].set_index("state_usps")["locations_served"]

    rows = []
    for state, allocation in BEAD_ALLOCATION_USD.items():
        locations = gso.get(state)
        rows.append(
            {
                "state_usps": state,
                "bead_allocation_usd": allocation,
                "gso_satellite_locations": locations,
                "bead_usd_per_gso_location": round(allocation / locations, 2) if locations else None,
            }
        )
    return pd.DataFrame(rows).sort_values("bead_usd_per_gso_location")


if __name__ == "__main__":
    result = build_comparison()
    print(result.to_string(index=False))
    out_path = DATA_DIR / "bead_allocation_v1.csv"
    result.to_csv(out_path, index=False)
    print(f"\nWrote {out_path}")
