# Policy/econ layer scope: BEAD grants vs. actual market gaps

Roadmap item 3 (2026-09-20 planning session). Goal: connect public subsidy
spending to the market-layer findings already in this project -- is BEAD
money going where the FCC data says the actual gaps are, and at what
implied cost per unserved location?

**Status as of 2026-09-23: three layers built and live.** Simple:
`scripts/build_bead_comparison.py` -> `data/bead_allocation_v2.csv`, all 50
states + DC. Granular: `scripts/build_bead_final_proposal.py` ->
`data/bead_final_proposal_by_state_tech.csv`, using the real 5,806-project
BEAD Final Proposal data from broadbandexpanded.com -- answers the "are
states leaning on BEAD to build infrastructure where satellite is already
cost-competitive" question posed below: yes, satellite is 22.0% of all
funded locations at $701-1,138/location vs. fiber's $6,420.70/location, a
real 5.6x gap. Verification (new, 2026-09-23): the simple layer's
provisional-award figures were individually checked against NTIA's own
official per-state "BEAD Final Proposal Overview" PDFs
(`scripts/build_bead_provisional_awards.py`) -- see "NTIA verification"
section below for the full story, since this uncovered a real accuracy
problem in the original telecompetitor.com-sourced figures, not just a
reconciliation nuance. The rest of this doc is left as-written from the
original planning session for context on what was decided and why -- see
the live site's two BEAD sections and their methodology changelog entries
for the current, public framing.

## NTIA verification (2026-09-23)

While investigating the granular layer's state-level reconciliation caveat
(10 of 50 states disagreeing >=15% against the original telecompetitor.com
figures), found that NTIA itself publishes a per-state "BEAD Final Proposal
Overview" one-pager PDF -- primary source, not a secondary compilation.
No bulk download exists; each state's current PDF has to be looked up
individually:

1. Fetch `https://broadbandusa.ntia.gov/funding-programs/broadband-equity-access-and-deployment-program/awardee/<state-name-lowercase-hyphenated>`
   (e.g. `.../awardee/alaska`) -- this links to the current PDF.
2. The PDF path's date-folder drifts per state as proposals get amended
   (seen: 2025-11 through 2026-08 across different states) -- don't guess
   it, always resolve via the awardee page.
3. At least one state (South Dakota) hosts its overview PDF off the NTIA
   domain entirely, on the state's own site -- the awardee page still
   linked to the real one.
4. DC is the one state with no overview PDF published at all, as of this
   check -- kept on the old telecompetitor.com estimate, flagged
   unverified on-site.
5. Extract "Total Deployment Cost" (maps to this project's
   `provisional_award_usd`) via `pdftotext -layout` or PyMuPDF (`fitz`) --
   much cheaper than a WebFetch round-trip per state at this scale (51
   states).

Checked 27 states directly this way (split across two collaborating
sessions, desktop + MacBook): only 12 of 27 matched the original
telecompetitor.com figure within 2% -- e.g. Hawaii's real BEAD cost is
$30.67M, telecompetitor's compilation said $94.87M, a 3x overstatement.
The granular per-project layer's own state totals, by contrast, matched
NTIA's real numbers within 2% for 26 of those 27 (the exception, Illinois,
was still only 12.6% off). All 50 states + DC are now covered:
`scripts/build_bead_provisional_awards.py` merges individually-verified
NTIA figures (50 states) with a granular-layer fallback and a legacy
telecompetitor.com fallback (DC only, last resort) into
`data/bead_provisional_awards_v3.csv`, which `build_bead_comparison.py`
now joins against instead of a hardcoded dict. Headline spread changed
from 355x (CT $2.21 to AK $784.17) to 462x (CT $2.21 to AK $1,021.06) --
Alaska's real number was *higher* than the old estimate, not lower.

Raw per-state verification data (gitignored, one file per contributing
session): `data/raw/bead/ntia_verification_desktop.csv`,
`data/raw/bead/ntia_verification_macbook.csv`.

## Data sources found

1. **NTIA official state allocation totals** --
   https://www.ntia.gov/funding-programs/internet-all/broadband-equity-access-and-deployment-bead-program/program-documentation/state-allocation-totals
   One number per state/territory, static since the June 2023 announcement
   ($42.45B total). Confirmed: NJ $263,689,548.65, NC $1,532,999,481.15 (via
   search; exact page has the full table incl. MT and should be scraped/
   copied directly rather than re-searched per state).
2. **BEAD Final Proposal data (project/subgrantee/location level)** --
   third-party aggregator (broadbandexpanded.com/funding/beadfinalproposaldata),
   zipped CSVs, most recent as of 2026-08-27. This is the granular layer:
   which specific locations/technologies BEAD money is actually funding,
   not just a state-level lump sum. Worth checking whether NTIA publishes
   this directly too before depending on a third-party mirror.
3. **NTIA BEAD Progress Dashboard** -- state-by-state approval/deployment
   status (not funding amounts), useful for a "how far along is this state"
   column.

## What this buys us, using data already in this repo

- `data/fcc_technology_summary.csv` already has `locations_served` per
  technology per state -- can derive an "unserved / underserved" proxy
  (locations with no technology above some speed threshold) per state.
- Combine with NTIA allocation totals: **implied BEAD dollars per
  unserved/underserved location**, by state. This is the actual
  TIM+econ angle -- not just "here's how much money," but "here's whether
  that amount is plausible relative to the gap it's meant to close."
- Cross-reference against the existing GSO/LEO satellite findings: are
  states leaning on BEAD to build wired/fixed-wireless infrastructure in
  areas where satellite is already the cost-competitive option today? That's
  a genuinely interesting policy question this project is positioned to ask
  that a plain BEAD tracker wouldn't.

## Not yet resolved / needs a decision before building

- ~~Whether to pull the granular Final Proposal data~~ -- resolved
  2026-09-22: pulled it, built the full state/technology layer. Turned out
  to be a single 22.5MB bulk ZIP (not per-state manual downloads like the
  FCC pull), covering all 50 states + DC + 3 territories. Did need the
  same memory-safety treatment as expected (LOCATION.csv is 194MB/3.79M
  rows; loaded with usecols/dtype, no chunking needed at that size).
- International comparison (Canada/UK/EU) was floated as a stretch goal --
  not scoped at all yet; different regulatory bodies, different data
  formats per country, likely a separate research pass before any build.
- ~~This layer only makes sense once the state sample is bigger than 3~~ --
  resolved: the market layer scaled to all 50 states + DC on 2026-09-20,
  and the BEAD layer was rebuilt at that scale the same day.

## Recommended next step (as of 2026-09-23)

All three layers are built, live, and NTIA-verified where possible -- see
status notes above. Open items now: (1) DC's provisional award is still on
the unverified telecompetitor.com estimate (no NTIA overview PDF exists
for it) -- re-check periodically in case NTIA publishes one later; (2) the
granular layer's remaining state-level gaps (RI +52.7%, NC +24.1%, IL
+12.6% vs. the now-verified figures) aren't explained -- would need
digging into broadbandexpanded.com's underlying project data for those
three states specifically; (3) CAI_20260827.csv (community anchor
institutions, not used in this build) carries real latitude/longitude per
funded site -- could support an actual point-density map of funded
locations someday, not attempted here, the existing map still uses the
state-total proxy; (4) NO_BEAD_20260827.csv (57.9MB, excluded/ineligible
locations with a reason code) is also unused -- could show which locations
were considered and rejected, not just which were funded. International
comparison remains an unscoped stretch goal -- would need its own research
pass before any build, not something to start opportunistically.
