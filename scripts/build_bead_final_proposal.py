"""Granular BEAD layer: real per-project funding and technology mix, replacing
the state-total-lump-sum proxy used by build_bead_comparison.py's per-location
figure with actual funded locations by technology, per state.

Input source: NTIA BEAD Final Proposal data, third-party-compiled bulk
download from broadbandexpanded.com/funding/beadfinalproposaldata (NTIA's own
site has no single bulk download; per-state figures aren't independently
API-fetchable). The compiler states this is "not intended to be authoritative
or a substitute" for original state data -- treat all figures here as
provisional/approximate, same spirit as the v2 state-total layer.

Download (manual, ~22.5MB zip):
    https://broadbandexpanded.com/files/data/bead/BEAD_FP_Data_BroadbandExpanded_20260827.zip
Unzip to data/raw/bead/ (5 CSVs: SUBGRANTEE, PROJECT, LOCATION, NO_BEAD, CAI --
only PROJECT and LOCATION are used here).

Technology codes in LOCATION.csv match the same FCC BDC scheme this repo
already uses in load_fcc_broadband.py (confirmed: 10/40/50/60/61/70/71/72 --
notably 61 = LEO Satellite appears, meaning some BEAD money funds Starlink/
Kuiper deployments directly, not just wired buildout).

Methodology: bead_support (federal subsidy $) is recorded per PROJECT, not
per location, and ~5.7% of projects fund a mix of technologies across their
locations (e.g. mostly fiber with a few satellite locations for the hardest-
to-reach spots) -- checked directly against the data (290 of 5,093 projects
in a 3M-row sample had >1 technology). Splitting the whole project's dollar
figure onto one technology would misattribute it, so bead_support is
allocated across technologies *within* a project proportional to each
technology's share of that project's funded locations. Location counts
themselves need no such split -- LOCATION.csv already records technology
per individual location directly.

Reconciliation: state-level totals here are checked against
data/bead_allocation_v2.csv's provisional_award_usd (the state-total figure
already on the site, itself individually NTIA-verified as of 2026-09-23 --
see scripts/build_bead_provisional_awards.py). They should roughly agree
(they're nominally the same NTIA program, same restructuring), but don't
assume they match state-by-state -- see build_reconciliation() and the
site's caveat text for documented examples (RI +52.7%, NC +24.1%, DC -83%
on a tiny base) and reasoning about why they can diverge (different
compilation dates, project approval status, or scope).

Output:
    data/bead_final_proposal_by_state_tech.csv
    data/bead_final_proposal_reconciliation.csv
"""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_DIR = DATA_DIR / "raw" / "bead"

TECH_CODE_LABELS = {
    10: "DSL (Copper)",
    40: "Cable",
    50: "Fiber",
    60: "GSO Satellite",
    61: "LEO Satellite",
    70: "Unlicensed Fixed Wireless",
    71: "Licensed Fixed Wireless",
    72: "LBR Fixed Wireless",
}

RECONCILIATION_FLAG_PCT = 15.0  # abs% difference above which a state gets flagged


def load_projects(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    return pd.read_csv(
        raw_dir / "PROJECT_20260827.csv",
        usecols=["state", "project_id", "bead_support"],
        dtype={"state": "category"},
    )


def load_locations(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    return pd.read_csv(
        raw_dir / "LOCATION_20260827.csv",
        usecols=["project_id", "technology", "state"],
        dtype={"technology": "int8", "state": "category"},
    )


UNKNOWN_TECH_LABEL = "Unknown (no location data)"


def aggregate_state_tech_summary(projects: pd.DataFrame, locations: pd.DataFrame) -> pd.DataFrame:
    # Locations per (project, technology) -- this is a direct count, not an
    # estimate, since LOCATION.csv already carries technology per row.
    loc_counts = (
        locations.groupby(["project_id", "technology"], observed=True)
        .size()
        .reset_index(name="locations")
    )
    project_totals = loc_counts.groupby("project_id")["locations"].transform("sum")
    loc_counts["location_share"] = loc_counts["locations"] / project_totals

    merged = loc_counts.merge(projects, on="project_id", how="left")
    merged["bead_support_share_usd"] = merged["bead_support"] * merged["location_share"]
    merged["technology_label"] = merged["technology"].map(TECH_CODE_LABELS).fillna("Other")

    # Some projects (checked 2026-09-23: 56 nationally, $88M combined, mostly
    # South Dakota's single largest project at $72.8M) have zero matching
    # rows in LOCATION.csv -- a project-vs-location scope gap in the source
    # compilation, not something this script can attribute by technology or
    # location count. Dropping them silently would understate (or for a
    # state like SD, entirely zero out) that state's real BEAD spending, so
    # they're kept as an explicit "Unknown" bucket rather than vanishing.
    projects_with_locations = set(loc_counts["project_id"].unique())
    unattributed = projects[~projects["project_id"].isin(projects_with_locations)].copy()
    unattributed["technology_label"] = UNKNOWN_TECH_LABEL
    unattributed["bead_support_share_usd"] = unattributed["bead_support"]
    unattributed["locations"] = 0

    merged = pd.concat(
        [merged, unattributed[["state", "project_id", "technology_label", "bead_support_share_usd", "locations"]]],
        ignore_index=True,
    )

    summary = (
        merged.groupby(["state", "technology_label"], observed=True)
        .agg(
            project_count=("project_id", "nunique"),
            locations_funded=("locations", "sum"),
            bead_support_usd=("bead_support_share_usd", "sum"),
        )
        .reset_index()
        .rename(columns={"state": "state_usps"})
    )
    summary["bead_support_usd"] = summary["bead_support_usd"].round(2)
    summary["usd_per_funded_location"] = (
        summary["bead_support_usd"] / summary["locations_funded"]
    ).round(2)
    summary.loc[summary["technology_label"] == UNKNOWN_TECH_LABEL, "usd_per_funded_location"] = None
    return summary.sort_values(["state_usps", "locations_funded"], ascending=[True, False])


def build_reconciliation(state_tech: pd.DataFrame, existing_totals: pd.Series) -> pd.DataFrame:
    granular_totals = state_tech.groupby("state_usps", observed=True)["bead_support_usd"].sum()
    combined = pd.DataFrame(
        {
            "granular_project_total_usd": granular_totals,
            "site_state_total_usd": existing_totals,
        }
    ).dropna()
    combined["pct_diff"] = (
        (combined["granular_project_total_usd"] - combined["site_state_total_usd"])
        / combined["site_state_total_usd"]
        * 100
    ).round(1)
    combined["flagged"] = combined["pct_diff"].abs() >= RECONCILIATION_FLAG_PCT
    combined.index.name = "state_usps"
    return combined.reset_index().sort_values("pct_diff", key=abs, ascending=False)


if __name__ == "__main__":
    state_tech = aggregate_state_tech_summary(load_projects(), load_locations())
    out_path = DATA_DIR / "bead_final_proposal_by_state_tech.csv"
    state_tech.to_csv(out_path, index=False)
    print(f"Wrote {out_path} ({len(state_tech)} state/technology rows, "
          f"{state_tech['state_usps'].nunique()} states/territories)")

    existing_totals = pd.read_csv(DATA_DIR / "bead_allocation_v2.csv").set_index("state_usps")[
        "provisional_award_usd"
    ]
    recon = build_reconciliation(state_tech, existing_totals)
    recon_path = DATA_DIR / "bead_final_proposal_reconciliation.csv"
    recon.to_csv(recon_path, index=False)
    n_flagged = recon["flagged"].sum()
    print(f"Wrote {recon_path} ({n_flagged} of {len(recon)} states flagged, "
          f">= {RECONCILIATION_FLAG_PCT}% difference vs. site's state-total figure)")
    print(recon.to_string(index=False))
