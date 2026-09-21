"""Unit tests for the FCC technology-code mapping and summarization logic,
using small synthetic frames -- no real downloaded FCC data required."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from load_fcc_broadband import TECH_CODE_LABELS, summarize_by_technology


def test_tech_code_labels_cover_the_codes_seen_in_real_data():
    # Codes confirmed against a real FCC BDC header (see script docstring):
    # 10/40/50/60/61/70/71/72. If a new code shows up in future FCC data,
    # this test doesn't fail (unmapped codes fall into "Other" by design),
    # but it locks in the current known set so an accidental deletion is
    # caught.
    assert set(TECH_CODE_LABELS.keys()) == {10, 40, 50, 60, 61, 70, 71, 72}
    assert TECH_CODE_LABELS[60] == "GSO Satellite"
    assert TECH_CODE_LABELS[61] == "LEO Satellite"
    assert TECH_CODE_LABELS[71] == "Licensed Fixed Wireless"


def test_summarize_by_technology_groups_and_labels_correctly():
    df = pd.DataFrame(
        {
            "technology": [61, 61, 60, 99],  # 99 = unmapped -> "Other"
            "max_advertised_download_speed": [280, 280, 50, 10],
            "max_advertised_upload_speed": [30, 30, 4, 1],
            "brand_name": ["Starlink", "Starlink", "Viasat", "Mystery ISP"],
            "state_usps": ["NJ", "NJ", "NJ", "NJ"],
        }
    )
    summary = summarize_by_technology(df)
    by_tech = summary.set_index("technology_label")

    assert by_tech.loc["LEO Satellite", "locations_served"] == 2
    assert by_tech.loc["LEO Satellite", "unique_providers"] == 1
    assert by_tech.loc["GSO Satellite", "locations_served"] == 1
    assert by_tech.loc["Other", "locations_served"] == 1


def test_summarize_by_technology_median_is_correct():
    df = pd.DataFrame(
        {
            "technology": [50, 50, 50],
            "max_advertised_download_speed": [100, 200, 300],
            "max_advertised_upload_speed": [10, 20, 30],
            "brand_name": ["ISP A", "ISP B", "ISP C"],
            "state_usps": ["NY", "NY", "NY"],
        }
    )
    summary = summarize_by_technology(df)
    row = summary[summary["technology_label"] == "Fiber"].iloc[0]
    assert row["median_max_down_mbps"] == 200
