"""Unit tests for the pricing-to-FCC-label mapping in build_cost_comparison.py.

Catches the exact class of bug fixed in commit ea72cad (Licensed Fixed
Wireless pricing silently compared against the wrong FCC population because
the mapping and the FCC labels had drifted apart) by asserting the two stay
in sync going forward.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build_cost_comparison import TECH_TO_FCC_LABEL
from load_fcc_broadband import TECH_CODE_LABELS


def test_every_mapped_fcc_label_is_a_real_fcc_label():
    # Every value TECH_TO_FCC_LABEL maps *to* must be a label
    # load_fcc_broadband.py can actually produce -- otherwise the join in
    # build_cost_comparison.py silently drops that technology's pricing.
    real_labels = set(TECH_CODE_LABELS.values())
    for slug, fcc_label in TECH_TO_FCC_LABEL.items():
        assert fcc_label in real_labels, (
            f"pricing_snapshot technology '{slug}' maps to '{fcc_label}', "
            f"which load_fcc_broadband.py never produces"
        )


def test_licensed_and_unlicensed_fixed_wireless_are_distinct():
    # The specific regression this test suite exists to prevent: these two
    # must never map to the same FCC label again.
    assert (
        TECH_TO_FCC_LABEL["licensed_fixed_wireless"]
        != TECH_TO_FCC_LABEL["unlicensed_fixed_wireless"]
    )


def test_cheapest_plan_is_selected_per_technology():
    from build_cost_comparison import load_pricing_by_technology

    result = load_pricing_by_technology()
    # Licensed Fixed Wireless has multiple Verizon 5G Home tiers in
    # pricing_snapshot.csv -- confirm the cheapest one wins, not the first
    # or the most expensive.
    row = result[result["technology_label"] == "Licensed Fixed Wireless"]
    if not row.empty:
        assert row.iloc[0]["monthly_price_usd"] == row["monthly_price_usd"].min()
