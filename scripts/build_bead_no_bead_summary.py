"""BEAD "no-BEAD locations" layer: why locations eligible for BEAD funding
(unserved/underserved on NTIA's Challenge Process list) end up NOT funded by
a BEAD project. Complements build_bead_final_proposal.py's funded-location
data with the excluded/non-funded counterpart -- answers "what happened to
the locations that didn't get a project," not just "what got funded."

Input: data/raw/bead/NO_BEAD_20260827.csv (57.9MB, ~1.1M rows, part of the
same broadbandexpanded.com BEAD Final Proposal compilation used elsewhere
in this project -- see scripts/build_bead_final_proposal.py's docstring).
This is NTIA's own standard fp_no_BEAD_locations.csv schema (confirmed via
NTIA's BEAD Challenge Process documentation), not a broadbandexpanded
invention -- every Eligible Entity that doesn't fund 100% of its
BEAD-eligible locations must submit one of these as part of its Final
Proposal.

Reason code definitions (source: NTIA's own "BEAD Final Proposal Guidance"
v1.2, https://www.ntia.gov/sites/default/files/2024-11/bead_final_proposal_guidance_v1.2.pdf,
pages 41-44 -- primary source, not guessed from the numeric codes alone):
    1 = Location should not have a broadband connection (demolished,
        uninhabitable, a support structure like a shed/barn, or mobile/not
        permanently installed -- e.g. an RV)
    2 = Location does not need mass-market broadband due to nature of use
        (land/natural formation, a CAI without demand, an enterprise or
        government-property location)
    3 = Location has been removed from the latest FCC Fabric version --
        i.e. it's not considered a real serviceable location anymore
    4 = Location is already served by an enforceable commitment (another
        federal/state program: BIP, CAFII, CPF, EACAM, RDOF, RECONNECT,
        SLFRF, TBCP1, TBCP2)
    5 = Location is already served by non-subsidized (privately funded)
        service
    6 = Other -- can be connected within 10 business days of a request
        with a standard installation fee (i.e. service is readily available
        on demand, just not currently active)
    7 = The Eligible Entity is financially incapable of serving this
        underserved location (NTIA sets "a high bar" for this code)

`classification` (0/1) marks whether the excluded location was originally
unserved (0) or underserved (1) per the Challenge Process -- not decoded
further here since NTIA's guidance doesn't define this pairing beyond that.

Output:
    data/bead_no_bead_by_state_reason.csv
    data/bead_no_bead_national_summary.csv
"""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_DIR = DATA_DIR / "raw" / "bead"

REASON_CODE_LABELS = {
    1: "Location shouldn't have a connection (demolished/uninhabitable/outbuilding/mobile)",
    2: "Doesn't need service (land, CAI without demand, enterprise, gov't property)",
    3: "Removed from the FCC Fabric (not a real serviceable location)",
    4: "Already served by another program (BIP/CAFII/CPF/EACAM/RDOF/RECONNECT/SLFRF/TBCP)",
    5: "Already served by non-subsidized (private) service",
    6: "Other -- connectable within 10 business days on request",
    7: "Eligible Entity financially incapable of serving it",
}


def load_no_bead_locations(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    return pd.read_csv(
        raw_dir / "NO_BEAD_20260827.csv",
        usecols=["location_id", "classification", "reason", "state"],
        dtype={"classification": "Int8", "reason": "int8", "state": "category"},
    )


def summarize_by_state_reason(locations: pd.DataFrame) -> pd.DataFrame:
    locations = locations.copy()
    locations["reason_label"] = locations["reason"].map(REASON_CODE_LABELS).fillna("Unrecognized code")
    summary = (
        locations.groupby(["state", "reason", "reason_label"], observed=True)
        .agg(
            location_count=("location_id", "count"),
            underserved_share=("classification", "mean"),
        )
        .reset_index()
        .rename(columns={"state": "state_usps"})
    )
    summary["underserved_share"] = summary["underserved_share"].round(3)
    return summary.sort_values(["state_usps", "location_count"], ascending=[True, False])


def summarize_national(locations: pd.DataFrame) -> pd.DataFrame:
    locations = locations.copy()
    locations["reason_label"] = locations["reason"].map(REASON_CODE_LABELS).fillna("Unrecognized code")
    total = len(locations)
    summary = (
        locations.groupby(["reason", "reason_label"], observed=True)
        .agg(location_count=("location_id", "count"))
        .reset_index()
        .sort_values("location_count", ascending=False)
    )
    summary["pct_of_total"] = (summary["location_count"] / total * 100).round(1)
    return summary


if __name__ == "__main__":
    locations = load_no_bead_locations()

    by_state = summarize_by_state_reason(locations)
    state_path = DATA_DIR / "bead_no_bead_by_state_reason.csv"
    by_state.to_csv(state_path, index=False)
    print(f"Wrote {state_path} ({len(by_state)} state/reason rows, "
          f"{by_state['state_usps'].nunique()} states/territories)")

    national = summarize_national(locations)
    national_path = DATA_DIR / "bead_no_bead_national_summary.csv"
    national.to_csv(national_path, index=False)
    print(f"\nWrote {national_path}")
    print(national.to_string(index=False))
    print(f"\nTotal excluded locations: {len(locations):,}")
