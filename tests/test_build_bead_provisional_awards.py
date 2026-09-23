"""Unit tests for the provisional-award source-priority merge logic
(ntia_pdf > granular_fallback > legacy_unverified). Uses synthetic fixtures
-- never depends on the real ntia_verification_*.csv files (gitignored,
per-session raw inputs) or the committed granular/legacy data matching any
particular snapshot."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build_bead_provisional_awards import LEGACY_FALLBACK_USD, merge_provisional_awards


@pytest.fixture
def ntia() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "state": ["AL", "TX"],
            "ntia_total_deployment_cost": [464_262_346.0, 1_257_675_573.0],
            "ntia_updated_date": ["12/05/2025", "11/18/2025"],
        }
    ).set_index("state")


@pytest.fixture
def granular_totals() -> pd.Series:
    return pd.Series({"AL": 459_115_600.0, "HI": 30_614_250.0, "DC": 169_087.5})


def test_state_with_ntia_verification_uses_ntia_figure(ntia, granular_totals):
    result = merge_provisional_awards(["AL"], ntia, granular_totals)
    row = result.iloc[0]
    assert row["source"] == "ntia_pdf"
    assert row["provisional_award_usd"] == 464_262_346.0
    assert row["ntia_updated_date"] == "12/05/2025"


def test_state_without_ntia_falls_back_to_granular(ntia, granular_totals):
    result = merge_provisional_awards(["HI"], ntia, granular_totals)
    row = result.iloc[0]
    assert row["source"] == "granular_fallback"
    assert row["provisional_award_usd"] == 30_614_250.0


def test_dc_skips_granular_despite_having_a_value(ntia, granular_totals):
    # DC has a granular_totals entry ($169,087.5) but it's in
    # SKIP_GRANULAR_FALLBACK because it's known-incomplete -- must fall
    # through to the legacy dict instead.
    result = merge_provisional_awards(["DC"], ntia, granular_totals)
    row = result.iloc[0]
    assert row["source"] == "legacy_unverified"
    assert row["provisional_award_usd"] == LEGACY_FALLBACK_USD["DC"]


def test_state_with_none_of_the_three_sources_raises():
    empty_ntia = pd.DataFrame(columns=["ntia_total_deployment_cost", "ntia_updated_date"])
    empty_granular = pd.Series(dtype=float)
    with pytest.raises(ValueError, match="ZZ"):
        merge_provisional_awards(["ZZ"], empty_ntia, empty_granular)


def test_priority_order_prefers_ntia_over_granular_when_both_present(granular_totals):
    ntia_with_al = pd.DataFrame(
        {"ntia_total_deployment_cost": [999.0], "ntia_updated_date": ["01/01/2026"]},
        index=pd.Index(["AL"], name="state"),
    )
    result = merge_provisional_awards(["AL"], ntia_with_al, granular_totals)
    row = result.iloc[0]
    assert row["source"] == "ntia_pdf"
    assert row["provisional_award_usd"] == 999.0
