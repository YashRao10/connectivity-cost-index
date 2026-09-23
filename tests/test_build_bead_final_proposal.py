"""Unit tests for the granular BEAD Final Proposal aggregation logic.
Uses synthetic fixtures -- never depends on the real (gitignored, 22.5MB zip
source) data/raw/bead/*.csv files, so these tests run in CI without the raw
download present."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build_bead_final_proposal import (
    RECONCILIATION_FLAG_PCT,
    TECH_CODE_LABELS,
    aggregate_state_tech_summary,
    build_reconciliation,
)


@pytest.fixture
def projects() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "state": ["AL", "AL", "TX"],
            "project_id": ["p1", "p2", "p3"],
            # p1: all-fiber project. p2: mixed fiber/LEO in AL. p3: all-LEO in TX.
            "bead_support": [100_000.0, 40_000.0, 9_000.0],
        }
    )


@pytest.fixture
def locations() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "project_id": ["p1", "p1", "p1", "p1", "p2", "p2", "p2", "p3", "p3", "p3"],
            "technology": [50, 50, 50, 50, 50, 50, 61, 61, 61, 61],
            "state": ["AL"] * 7 + ["TX"] * 3,
        }
    )


def test_locations_funded_counts_directly_from_location_rows(projects, locations):
    result = aggregate_state_tech_summary(projects, locations)
    al_fiber = result[(result.state_usps == "AL") & (result.technology_label == "Fiber")].iloc[0]
    # p1 contributes 4 fiber locations, p2 contributes 2 fiber locations -> 6
    assert al_fiber["locations_funded"] == 6


def test_bead_support_split_proportionally_within_mixed_project(projects, locations):
    result = aggregate_state_tech_summary(projects, locations)
    al_fiber = result[(result.state_usps == "AL") & (result.technology_label == "Fiber")].iloc[0]
    al_leo = result[(result.state_usps == "AL") & (result.technology_label == "LEO Satellite")].iloc[0]
    # p1 ($100k, all 4 locations fiber) fully attributed to fiber.
    # p2 ($40k, 2/3 fiber + 1/3 LEO) splits 26,666.67 / 13,333.33.
    assert al_fiber["bead_support_usd"] == pytest.approx(100_000 + 40_000 * 2 / 3, abs=0.01)
    assert al_leo["bead_support_usd"] == pytest.approx(40_000 * 1 / 3, abs=0.01)


def test_single_technology_project_is_not_split(projects, locations):
    result = aggregate_state_tech_summary(projects, locations)
    tx_leo = result[(result.state_usps == "TX") & (result.technology_label == "LEO Satellite")].iloc[0]
    assert tx_leo["bead_support_usd"] == pytest.approx(9_000.0)
    assert tx_leo["locations_funded"] == 3


def test_usd_per_funded_location_math_is_correct(projects, locations):
    result = aggregate_state_tech_summary(projects, locations)
    for _, row in result.iterrows():
        expected = round(row["bead_support_usd"] / row["locations_funded"], 2)
        assert row["usd_per_funded_location"] == expected


def test_unmapped_technology_code_falls_back_to_other():
    projects = pd.DataFrame({"state": ["AL"], "project_id": ["p1"], "bead_support": [1000.0]})
    locations = pd.DataFrame({"project_id": ["p1"], "technology": [99], "state": ["AL"]})
    result = aggregate_state_tech_summary(projects, locations)
    assert result.iloc[0]["technology_label"] == "Other"


def test_all_tech_codes_used_in_aggregation_are_mapped():
    # Every code this module claims to recognize should actually be in the
    # shared FCC label scheme, not just documented in a comment.
    assert TECH_CODE_LABELS[50] == "Fiber"
    assert TECH_CODE_LABELS[61] == "LEO Satellite"
    assert len(TECH_CODE_LABELS) == 8


def test_reconciliation_flags_large_discrepancies(projects, locations):
    state_tech = aggregate_state_tech_summary(projects, locations)
    # AL granular total = 140,000; site figure way off (350,000) -> flagged.
    # TX granular total = 9,000; site figure close (9,500) -> not flagged.
    existing_totals = pd.Series({"AL": 350_000.0, "TX": 9_500.0}, name="provisional_award_usd")
    recon = build_reconciliation(state_tech, existing_totals)
    al_row = recon[recon.state_usps == "AL"].iloc[0]
    tx_row = recon[recon.state_usps == "TX"].iloc[0]
    assert al_row["flagged"]
    assert not tx_row["flagged"]
    assert abs(al_row["pct_diff"]) >= RECONCILIATION_FLAG_PCT


def test_reconciliation_pct_diff_math_is_correct(projects, locations):
    state_tech = aggregate_state_tech_summary(projects, locations)
    existing_totals = pd.Series({"AL": 350_000.0, "TX": 9_500.0}, name="provisional_award_usd")
    recon = build_reconciliation(state_tech, existing_totals)
    al_row = recon[recon.state_usps == "AL"].iloc[0]
    expected = round((140_000.0 - 350_000.0) / 350_000.0 * 100, 1)
    assert al_row["pct_diff"] == expected
