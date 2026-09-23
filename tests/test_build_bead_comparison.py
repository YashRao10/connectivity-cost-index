"""Unit tests for the BEAD allocation join logic (v2: original + provisional
award, all 50 states + DC)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build_bead_comparison import (
    BEAD_AWARDS_USD,
    build_comparison,
    load_cheapest_starlink_monthly_usd,
)


def test_bead_award_amounts_are_positive():
    for original, provisional in BEAD_AWARDS_USD.values():
        assert original > 0
        assert provisional > 0


def test_bead_allocation_keys_are_two_letter_state_codes():
    assert all(len(k) == 2 and k.isupper() for k in BEAD_AWARDS_USD)


def test_bead_covers_all_50_states_plus_dc():
    assert len(BEAD_AWARDS_USD) == 51


def test_build_comparison_covers_every_configured_state():
    result = build_comparison()
    assert set(result["state_usps"]) == set(BEAD_AWARDS_USD.keys())


def test_per_location_math_is_correct():
    result = build_comparison()
    for _, row in result.dropna(subset=["provisional_usd_per_gso_location"]).iterrows():
        expected = round(row["provisional_award_usd"] / row["gso_satellite_locations"], 2)
        assert row["provisional_usd_per_gso_location"] == expected


def test_pct_change_math_is_correct():
    result = build_comparison()
    for _, row in result.iterrows():
        expected = round(
            (row["provisional_award_usd"] - row["original_allocation_usd"])
            / row["original_allocation_usd"]
            * 100,
            1,
        )
        assert row["pct_change_vs_original"] == expected


def test_provisional_awards_are_generally_lower_than_original():
    # The 2025 restructuring cut funding almost everywhere -- if most states
    # showed an increase, something would be wrong with the source data.
    result = build_comparison()
    assert (result["pct_change_vs_original"] < 0).sum() >= 45


def test_cheapest_starlink_monthly_price_is_positive_and_reasonable():
    price = load_cheapest_starlink_monthly_usd()
    assert 0 < price < 500


def test_starlink_months_math_is_correct():
    result = build_comparison()
    starlink_monthly_usd = load_cheapest_starlink_monthly_usd()
    for _, row in result.dropna(subset=["provisional_per_location_months_of_starlink"]).iterrows():
        expected = round(row["provisional_usd_per_gso_location"] / starlink_monthly_usd, 1)
        assert row["provisional_per_location_months_of_starlink"] == expected


def test_starlink_months_column_present_wherever_usd_per_location_is():
    result = build_comparison()
    has_usd = result["provisional_usd_per_gso_location"].notna()
    has_months = result["provisional_per_location_months_of_starlink"].notna()
    assert (has_usd == has_months).all()
