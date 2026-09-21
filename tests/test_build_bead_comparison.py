"""Unit tests for the BEAD allocation join logic."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build_bead_comparison import BEAD_ALLOCATION_USD, build_comparison


def test_bead_allocation_amounts_are_positive():
    assert all(v > 0 for v in BEAD_ALLOCATION_USD.values())


def test_bead_allocation_keys_are_two_letter_state_codes():
    assert all(len(k) == 2 and k.isupper() for k in BEAD_ALLOCATION_USD)


def test_build_comparison_covers_every_configured_state():
    result = build_comparison()
    assert set(result["state_usps"]) == set(BEAD_ALLOCATION_USD.keys())


def test_per_location_math_is_correct():
    result = build_comparison()
    for _, row in result.dropna(subset=["bead_usd_per_gso_location"]).iterrows():
        expected = round(row["bead_allocation_usd"] / row["gso_satellite_locations"], 2)
        assert row["bead_usd_per_gso_location"] == expected
