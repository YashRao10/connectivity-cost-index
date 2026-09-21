"""Schema and sanity checks on the committed data outputs.

These run against whatever data/*.csv is currently checked in -- not
against a fixed golden dataset -- so they catch regressions (a bad
technology label, a negative cost, a state dropped silently) whenever
someone regenerates the data, without needing to re-run the full
download pipeline in CI.
"""

import math

from conftest import VALID_STATE_CODES, VALID_TECH_LABELS


def test_fcc_summary_schema(fcc_summary):
    expected_cols = {
        "state_usps", "technology_label", "locations_served",
        "unique_providers", "median_max_down_mbps", "median_max_up_mbps",
    }
    assert expected_cols.issubset(fcc_summary.columns)


def test_fcc_summary_technology_labels_are_known(fcc_summary):
    unknown = set(fcc_summary["technology_label"]) - VALID_TECH_LABELS
    assert not unknown, f"Unrecognized technology label(s): {unknown}"


def test_fcc_summary_state_codes_are_valid(fcc_summary):
    unknown = set(fcc_summary["state_usps"]) - VALID_STATE_CODES
    assert not unknown, f"Invalid state code(s): {unknown}"


def test_fcc_summary_covers_all_51_states(fcc_summary):
    # Catches the opposite failure mode from the "valid codes" check above:
    # a state silently missing from a rebuild (upstream download skipped,
    # a merge dropping rows) rather than a bad/unexpected code appearing.
    missing = VALID_STATE_CODES - set(fcc_summary["state_usps"])
    assert not missing, f"Market layer missing state(s): {missing}"


def test_fcc_summary_locations_served_non_negative(fcc_summary):
    assert (fcc_summary["locations_served"] >= 0).all()


def test_fcc_summary_no_duplicate_state_technology_rows(fcc_summary):
    dupes = fcc_summary.duplicated(subset=["state_usps", "technology_label"])
    assert not dupes.any(), "Duplicate (state, technology) rows found"


def test_every_state_has_leo_and_gso_satellite_rows(fcc_summary):
    # These two are central to the project's headline finding -- if a state
    # is missing either, something upstream silently dropped data.
    for state, group in fcc_summary.groupby("state_usps"):
        techs = set(group["technology_label"])
        assert "LEO Satellite" in techs, f"{state} missing LEO Satellite row"
        assert "GSO Satellite" in techs, f"{state} missing GSO Satellite row"


def test_cost_comparison_no_negative_costs(cost_comparison):
    costs = cost_comparison["cost_per_fcc_median_mbps_usd"].dropna()
    costs = costs[costs != math.inf]
    assert (costs >= 0).all()


def test_cost_comparison_technology_labels_are_known(cost_comparison):
    unknown = set(cost_comparison["technology_label"]) - VALID_TECH_LABELS
    assert not unknown, f"Unrecognized technology label(s): {unknown}"


def test_leo_satellite_cost_is_identical_across_states(cost_comparison):
    # This is the project's headline finding's mechanical backbone (see
    # methodology's zero-cross-state-variance caveat) -- if this test ever
    # fails, either the finding has genuinely changed (investigate before
    # updating the site) or something broke in the pricing/FCC join.
    leo = cost_comparison[cost_comparison["technology_label"] == "LEO Satellite"]
    values = leo["cost_per_fcc_median_mbps_usd"].dropna().unique()
    assert len(values) == 1, f"Expected one LEO Satellite cost value, got {values}"


def test_pricing_snapshot_schema(pricing_snapshot):
    expected_cols = {
        "technology", "provider", "plan", "monthly_price_usd",
        "advertised_mbps_down", "cost_per_mbps_usd", "as_of", "source",
    }
    assert expected_cols.issubset(pricing_snapshot.columns)


def test_ookla_summary_schema(ookla_summary):
    expected_cols = {
        "state_usps", "tiles", "total_tests", "median_down_mbps",
        "median_up_mbps", "median_latency_ms", "network_type",
    }
    assert expected_cols.issubset(ookla_summary.columns)
    assert set(ookla_summary["network_type"]) <= {"fixed", "mobile"}


def test_ookla_summary_speeds_are_positive(ookla_summary):
    assert (ookla_summary["median_down_mbps"] > 0).all()
    assert (ookla_summary["median_up_mbps"] > 0).all()


def test_ookla_summary_covers_all_51_states(ookla_summary):
    # As of v3.1 this layer matches the market layer's full coverage --
    # if COMPARISON_STATES in load_ookla_regional.py ever regresses back
    # to a partial list, this should catch it rather than silently
    # shipping a site claiming "all 50 states + DC" that isn't true.
    missing = VALID_STATE_CODES - set(ookla_summary["state_usps"])
    assert not missing, f"Ookla real-world layer missing state(s): {missing}"


def test_bead_comparison_schema(bead_comparison):
    expected_cols = {
        "state_usps", "original_allocation_usd", "provisional_award_usd",
        "pct_change_vs_original", "gso_satellite_locations",
        "provisional_usd_per_gso_location",
    }
    assert expected_cols.issubset(bead_comparison.columns)


def test_bead_allocations_are_positive(bead_comparison):
    assert (bead_comparison["original_allocation_usd"] > 0).all()
    assert (bead_comparison["provisional_award_usd"] > 0).all()


def test_bead_comparison_covers_all_51_states(bead_comparison):
    missing = VALID_STATE_CODES - set(bead_comparison["state_usps"])
    assert not missing, f"BEAD layer missing state(s): {missing}"
