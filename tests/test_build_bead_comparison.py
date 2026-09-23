"""Unit tests for the BEAD allocation join logic (v3: original allocation +
NTIA-verified provisional award, all 50 states + DC)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build_bead_comparison import (
    ORIGINAL_ALLOCATION_USD,
    build_comparison,
    load_cheapest_starlink_monthly_usd,
)


def test_original_allocation_amounts_are_positive():
    for original in ORIGINAL_ALLOCATION_USD.values():
        assert original > 0


def test_original_allocation_keys_are_two_letter_state_codes():
    assert all(len(k) == 2 and k.isupper() for k in ORIGINAL_ALLOCATION_USD)


def test_original_allocation_covers_all_50_states_plus_dc():
    assert len(ORIGINAL_ALLOCATION_USD) == 51


def test_build_comparison_covers_every_configured_state():
    result = build_comparison()
    assert set(result["state_usps"]) == set(ORIGINAL_ALLOCATION_USD.keys())


def test_provisional_award_source_is_tracked_and_mostly_ntia_verified():
    result = build_comparison()
    assert set(result["provisional_award_source"]).issubset(
        {"ntia_pdf", "granular_fallback", "legacy_unverified"}
    )
    # As of the 2026-09-23 verification effort, 50 of 51 states have a
    # directly-verified NTIA figure -- only DC lacks a published overview PDF.
    assert (result["provisional_award_source"] == "ntia_pdf").sum() >= 50


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
