"""Unit tests for the BEAD no-BEAD-locations (excluded/non-funded) summary
logic. Uses a synthetic fixture -- never depends on the real (gitignored,
57.9MB) data/raw/bead/NO_BEAD_20260827.csv file."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build_bead_no_bead_summary import (
    REASON_CODE_LABELS,
    summarize_by_state_reason,
    summarize_national,
)


@pytest.fixture
def locations() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "location_id": [1, 2, 3, 4, 5, 6],
            "classification": [0, 0, 1, 0, 1, 0],
            "reason": [5, 5, 3, 4, 5, 99],  # 99 = unrecognized code, on purpose
            "state": ["AL", "AL", "AL", "TX", "TX", "TX"],
        }
    )


def test_all_seven_official_reason_codes_are_mapped():
    assert set(REASON_CODE_LABELS.keys()) == {1, 2, 3, 4, 5, 6, 7}
    for label in REASON_CODE_LABELS.values():
        assert isinstance(label, str) and len(label) > 0


def test_state_reason_counts_are_correct(locations):
    result = summarize_by_state_reason(locations)
    al_reason5 = result[(result.state_usps == "AL") & (result.reason == 5)].iloc[0]
    assert al_reason5["location_count"] == 2


def test_underserved_share_math_is_correct(locations):
    result = summarize_by_state_reason(locations)
    al_reason5 = result[(result.state_usps == "AL") & (result.reason == 5)].iloc[0]
    # classification values [0, 0] for AL's two reason-5 rows -> mean 0.0
    assert al_reason5["underserved_share"] == 0.0
    tx_reason5 = result[(result.state_usps == "TX") & (result.reason == 5)].iloc[0]
    # classification [1] for TX's one reason-5 row -> mean 1.0
    assert tx_reason5["underserved_share"] == 1.0


def test_unrecognized_reason_code_does_not_crash_and_is_labeled(locations):
    result = summarize_by_state_reason(locations)
    unrecognized = result[result.reason == 99]
    assert len(unrecognized) == 1
    assert unrecognized.iloc[0]["reason_label"] == "Unrecognized code"


def test_national_summary_totals_match_row_count(locations):
    national = summarize_national(locations)
    assert national["location_count"].sum() == len(locations)


def test_national_summary_pct_of_total_math_is_correct(locations):
    national = summarize_national(locations)
    reason5_row = national[national.reason == 5].iloc[0]
    expected_pct = round(3 / len(locations) * 100, 1)  # 3 of 6 rows are reason 5
    assert reason5_row["pct_of_total"] == expected_pct


def test_national_summary_sorted_by_count_descending(locations):
    national = summarize_national(locations)
    counts = national["location_count"].tolist()
    assert counts == sorted(counts, reverse=True)
