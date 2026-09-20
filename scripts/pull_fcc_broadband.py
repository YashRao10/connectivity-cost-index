"""Pull FCC National Broadband Map coverage-by-technology data for a set of sample locations.

API docs: https://www.fcc.gov/sites/default/files/bdc-public-data-api-spec.pdf
Requires a free FCC BDC API key (register at https://broadbandmap.fcc.gov/data-download/api-key).

Usage:
    FCC_BDC_API_KEY=... python scripts/pull_fcc_broadband.py
"""

import os
import sys

import requests

BDC_BASE_URL = "https://broadbandmap.fcc.gov/api/public/map/v1"

# Sample locations chosen to span technology availability: dense metro,
# suburban, and a rural/LEO-satellite-reliant area.
SAMPLE_LOCATIONS = [
    {"label": "dense_metro", "note": "fill in lat/lon or census block"},
    {"label": "suburban", "note": "fill in lat/lon or census block"},
    {"label": "rural_leo_dependent", "note": "fill in lat/lon or census block"},
]


def main() -> None:
    api_key = os.environ.get("FCC_BDC_API_KEY")
    if not api_key:
        print(
            "FCC_BDC_API_KEY not set. Register for a free key at "
            "https://broadbandmap.fcc.gov/data-download/api-key and re-run.",
            file=sys.stderr,
        )
        sys.exit(1)

    # TODO: fill in real endpoint calls once sample locations are chosen and
    # the exact BDC query shape (location summary vs. nationwide download) is
    # confirmed against the API spec above.
    raise NotImplementedError(
        "Endpoint wiring pending — see SAMPLE_LOCATIONS and BDC API spec."
    )


if __name__ == "__main__":
    main()
