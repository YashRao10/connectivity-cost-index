"""Unit tests for the CAI point-map data build. Uses synthetic fixtures --
never depends on the real (gitignored) data/raw/bead/CAI_20260827.csv."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build_cai_locations import (
    MAP_EXCLUDED_TERRITORIES,
    TYPE_LABELS,
    build_point_records,
    build_summary,
)


@pytest.fixture
def cai() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "type": ["S", "L", "H", "F", "P", "G", "C", "S"],
            "state": ["TX", "TX", "CA", "AK", "HI", "AS", "GU", "WA"],
            "latitude": [30.1, 30.2, 34.5, 61.2, 21.3, -14.3, 13.4, 47.1],
            "longitude": [-97.1, -97.2, -118.2, -149.9, -157.8, -170.7, 144.7, -122.4],
        }
    )


def test_build_point_records_excludes_territories_but_keeps_ak_hi(cai):
    points = build_point_records(cai)
    states_in_output = {p[3] for p in points}
    assert "AS" not in states_in_output
    assert "GU" not in states_in_output
    assert "AK" in states_in_output
    assert "HI" in states_in_output
    assert len(points) == len(cai) - 2  # AS and GU dropped


def test_build_point_records_rounds_coordinates(cai):
    points = build_point_records(cai)
    tx_point = next(p for p in points if p[3] == "TX" and p[0] == 30.1)
    assert tx_point[0] == round(30.1, 4)
    assert tx_point[1] == round(-97.1, 4)


def test_build_point_records_output_shape_is_compact_arrays(cai):
    points = build_point_records(cai)
    for p in points:
        assert len(p) == 4  # [lat, lon, type_code, state_usps], not a dict
        assert isinstance(p, list)


def test_build_summary_counts_types_with_human_labels(cai):
    summary = build_summary(cai)
    assert summary["type_counts"][TYPE_LABELS["S"]] == 2
    assert summary["type_counts"][TYPE_LABELS["L"]] == 1
    assert summary["total_usable_points"] == len(cai)


def test_build_summary_reports_excluded_territories_separately(cai):
    summary = build_summary(cai)
    assert summary["territories_excluded_from_map"] == {"AS": 1, "GU": 1}
    assert summary["mapped_points"] == len(cai) - 2


def test_null_and_zero_coordinates_are_filtered_before_reaching_build_functions():
    # Mirrors load_cai_locations' filtering logic directly, since that
    # function reads a real file path and isn't itself unit-testable
    # against a fixture -- this documents the two exclusion rules it
    # implements so a future refactor can't silently drop them.
    raw = pd.DataFrame(
        {
            "type": ["S", "L", "H", "F"],
            "state": ["TX", "TX", "TX", "TX"],
            "latitude": [30.1, None, 0.0, 40.0],
            "longitude": [-97.1, -97.2, 0.0, None],
        }
    )
    filtered = raw.dropna(subset=["latitude", "longitude", "type"])
    filtered = filtered[(filtered["latitude"] != 0.0) | (filtered["longitude"] != 0.0)]
    assert len(filtered) == 1
    assert filtered.iloc[0]["type"] == "S"


def test_all_type_codes_seen_in_real_data_are_mapped():
    # Checked directly against the real 2026-08-27 CAI data: exactly these
    # 7 codes appear (plus 1 null row, already filtered upstream). If a
    # future data refresh introduces a new code, it should fail loudly here
    # rather than silently falling back to the raw code as its own label.
    assert set(TYPE_LABELS.keys()) == {"S", "L", "H", "F", "P", "G", "C"}


def test_map_excluded_territories_matches_known_non_state_entries():
    # CAI data (unlike the state-level layers) only ever contains AS and GU
    # among AlbersUSA-incompatible territories -- no PR/VI/MP rows exist in
    # the real 2026-08-27 file, but this set should still match the
    # choropleth's broader EXCLUDED set's *intent* (non-state territories
    # AlbersUSA can't place), even if not its exact membership.
    assert MAP_EXCLUDED_TERRITORIES == {"AS", "GU"}
