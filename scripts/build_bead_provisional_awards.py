"""Builds the authoritative provisional-award-per-state dataset that
build_bead_comparison.py joins against, replacing v2's single hand-compiled
telecompetitor.com dict.

Background: v2's provisional awards (originally in build_bead_comparison.py's
BEAD_AWARDS_USD dict) were sourced entirely from telecompetitor.com, a
secondary compilation. Investigating the granular layer's reconciliation
caveat (2026-09-22/23) turned up NTIA's own per-state "BEAD Final Proposal
Overview" PDFs (broadbandusa.ntia.gov/funding-programs/.../awardee/<state>,
which links to the current PDF -- the exact path's date folder varies per
state and drifts as proposals get amended, so it must be looked up per
state, not guessed). Checked 27 states directly against these PDFs: the
granular per-project layer (data/bead_final_proposal_by_state_tech.csv)
matched NTIA's real "Total Deployment Cost" within 2% for 26 of 27; the old
telecompetitor.com figure only matched within 2% for 12 of 27 -- e.g.
Hawaii's real cost is $30.67M, telecompetitor's compilation said $94.87M
(3x too high).

Source priority per state (highest confidence first):
    1. ntia_pdf         -- individually verified against NTIA's own overview
                           PDF (data/raw/bead/ntia_verification_*.csv, one
                           file per contributing session/machine -- gitignored
                           raw inputs, see docs/BEAD_LAYER_SCOPE.md for the
                           lookup method).
    2. granular_fallback -- no individual PDF check yet, but the granular
                           per-project layer's state total is available and,
                           per the 26/27 spot-check above, reliable.
    3. legacy_unverified -- neither of the above (as of this build: DC has
                           no NTIA overview PDF at all; a handful of states
                           may be mid-verification). Falls back to the
                           original telecompetitor.com figure, explicitly
                           flagged as the least-trusted tier.

Output: data/bead_provisional_awards_v3.csv (state_usps, provisional_award_usd,
source, ntia_updated_date -- blank outside the ntia_pdf tier).
"""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_BEAD_DIR = DATA_DIR / "raw" / "bead"

# Last-resort fallback for states with no NTIA PDF as of this build. As of
# this build, only DC qualifies: no overview PDF exists for it on
# broadbandusa.ntia.gov (confirmed independently by both contributing
# sessions). Same telecompetitor.com figure v2 originally used -- kept only
# because there's nothing more authoritative yet, not because it's trusted
# on its own. Interesting cross-check found 2026-09-23: once
# build_bead_final_proposal.py's "Unknown (no location data)" bucket was
# added (some BEAD projects have no matching LOCATION.csv rows and were
# previously silently dropped, understating a few states -- DC included),
# DC's granular total came to exactly $996,099, matching this legacy figure
# to the dollar. Reassuring, but not independent verification -- the same
# stale-snapshot pattern explained RI's and NC's granular/legacy exact
# matches (see docs/BEAD_LAYER_SCOPE.md), so this likely means DC's
# broadbandexpanded.com data and its old telecompetitor.com figure trace
# back to the same outdated source, not that $996,099 is confirmed correct
# against NTIA's real current number. Re-check before citing.
LEGACY_FALLBACK_USD = {
    "DC": 996_099,
}


# Contributing sessions independently produced slightly different column
# names/order (state vs. state_usps, ntia_updated_date vs. as_of_date) --
# normalized here rather than forcing a re-export, since both files are
# gitignored raw inputs anyway (see data/raw/bead/).
COLUMN_ALIASES = {"state_usps": "state", "as_of_date": "ntia_updated_date"}


def load_ntia_verifications() -> pd.DataFrame:
    files = sorted(RAW_BEAD_DIR.glob("ntia_verification_*.csv"))
    if not files:
        return pd.DataFrame(columns=["state", "ntia_total_deployment_cost", "ntia_updated_date"])
    frames = [pd.read_csv(f).rename(columns=COLUMN_ALIASES) for f in files]
    combined = pd.concat(frames, ignore_index=True)
    combined = combined[combined["ntia_total_deployment_cost"] != "?"]
    combined["ntia_total_deployment_cost"] = combined["ntia_total_deployment_cost"].astype(float)
    # If a state was somehow verified twice (e.g. both sessions checked it),
    # keep the first -- they should agree; a real mismatch is worth surfacing
    # by hand, not silently averaged away.
    return combined.drop_duplicates(subset="state", keep="first")


def load_granular_totals() -> pd.Series:
    granular = pd.read_csv(DATA_DIR / "bead_final_proposal_by_state_tech.csv")
    return granular.groupby("state_usps", observed=True)["bead_support_usd"].sum()


def merge_provisional_awards(
    all_state_codes: list[str], ntia: pd.DataFrame, granular_totals: pd.Series
) -> pd.DataFrame:
    """Pure merge logic (no file I/O) -- ntia is indexed by state, columns
    include ntia_total_deployment_cost and ntia_updated_date; granular_totals
    is a state_usps-indexed Series of dollar totals. Split out from
    build_provisional_awards() so it's testable against small synthetic
    fixtures instead of the real gitignored/committed data files."""
    rows = []
    for state in all_state_codes:
        if state in ntia.index:
            rows.append(
                {
                    "state_usps": state,
                    "provisional_award_usd": round(ntia.loc[state, "ntia_total_deployment_cost"], 2),
                    "source": "ntia_pdf",
                    "ntia_updated_date": ntia.loc[state, "ntia_updated_date"],
                }
            )
        elif state in granular_totals.index:
            rows.append(
                {
                    "state_usps": state,
                    "provisional_award_usd": round(granular_totals[state], 2),
                    "source": "granular_fallback",
                    "ntia_updated_date": None,
                }
            )
        elif state in LEGACY_FALLBACK_USD:
            rows.append(
                {
                    "state_usps": state,
                    "provisional_award_usd": LEGACY_FALLBACK_USD[state],
                    "source": "legacy_unverified",
                    "ntia_updated_date": None,
                }
            )
        else:
            raise ValueError(
                f"{state}: no NTIA verification, no granular total, and no legacy "
                "fallback -- add one before this state can appear in the BEAD layer."
            )
    return pd.DataFrame(rows).sort_values("state_usps")


def build_provisional_awards(all_state_codes: list[str]) -> pd.DataFrame:
    ntia = load_ntia_verifications().set_index("state")
    granular_totals = load_granular_totals()
    return merge_provisional_awards(all_state_codes, ntia, granular_totals)


if __name__ == "__main__":
    # Same 51-state list build_bead_comparison.py's original ORIGINAL_ALLOCATION_USD
    # covers -- imported at call time to avoid a hard circular import at module load.
    from build_bead_comparison import ORIGINAL_ALLOCATION_USD

    result = build_provisional_awards(sorted(ORIGINAL_ALLOCATION_USD.keys()))
    out_path = DATA_DIR / "bead_provisional_awards_v3.csv"
    result.to_csv(out_path, index=False)
    print(result["source"].value_counts())
    print(f"\nWrote {out_path}")
