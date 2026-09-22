"""Tests for the choropleth map's GeoJSON output.

No fixture for this in conftest.py yet since nothing else needed the raw
geojson -- reads docs/data/state_map.geojson directly here instead.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build_state_map_data import EXCLUDED
from conftest import VALID_STATE_CODES

GEOJSON_PATH = Path(__file__).resolve().parent.parent / "docs" / "data" / "state_map.geojson"


@pytest.fixture(scope="session")
def state_map_geojson() -> dict:
    if not GEOJSON_PATH.exists():
        pytest.skip(f"{GEOJSON_PATH} not present (run scripts/build_state_map_data.py first)")
    with open(GEOJSON_PATH) as f:
        return json.load(f)


def test_map_excludes_exactly_non_state_territories(state_map_geojson):
    # Documents the intentional exclusion (see build_state_map_data.py's
    # docstring/EXCLUDED) as a test, not just a comment -- if someone
    # changes EXCLUDED without updating the map's own rendering, or a
    # non-territory state goes missing by accident, this should fail.
    # AK/HI are NOT excluded -- d3.geoAlbersUsa() plots them as insets.
    mapped_states = {f["properties"]["state_usps"] for f in state_map_geojson["features"]}
    expected = VALID_STATE_CODES - EXCLUDED
    assert mapped_states == expected, (
        f"Mapped states don't match VALID_STATE_CODES minus EXCLUDED. "
        f"Missing: {expected - mapped_states}, unexpected: {mapped_states - expected}"
    )
    assert {"AK", "HI"}.issubset(mapped_states), (
        "AK/HI should be plotted as AlbersUSA insets, not excluded"
    )


def test_map_features_have_expected_properties(state_map_geojson):
    expected_props = {
        "state_usps", "NAME", "cheapest_technology", "cheapest_cost_per_mbps_usd",
        "leo_cost_per_mbps_usd", "leo_locations_served", "bead_allocation_usd",
        "bead_usd_per_gso_location", "has_data",
    }
    for feature in state_map_geojson["features"]:
        assert expected_props.issubset(feature["properties"].keys())


def test_map_has_data_flag_means_market_layer_coverage(state_map_geojson):
    # has_data reflects the market layer's cost_comparison.csv (all 51
    # states/DC minus AK/HI's map exclusion), NOT the still-partial BEAD
    # layer -- a state can be has_data=True with no BEAD allocation at all
    # (e.g. KY), since those are two different coverage sets. This test
    # documents that distinction: has_data should be True everywhere this
    # map plots a state at all, given the market layer's full coverage.
    for feature in state_map_geojson["features"]:
        assert feature["properties"]["has_data"] is True, (
            f"{feature['properties']['state_usps']} plotted with has_data=False "
            "-- market layer should cover every mapped (non-AK/HI/territory) state"
        )
