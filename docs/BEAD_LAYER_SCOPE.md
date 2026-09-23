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
status notes above. Root-caused 2 of the 3 remaining granular-layer
reconciliation gaps (2026-09-23 follow-up): RI's and NC's project-level
totals in the granular layer match the *old, superseded* telecompetitor.com
figures to the dollar (RI: $16,137,983 exactly; NC: $408,511,175.10 vs.
telecompetitor's $408,511,175) -- broadbandexpanded.com's underlying
project data for those two states appears to reflect an earlier submission
than NTIA's current overview PDF, not a bug in this project's aggregation
math. Checked directly: `data/raw/bead/PROJECT_20260827.csv` filtered to
each state, summed `bead_support` raw (no location-join needed to see
this) -- both totals landed on the old telecompetitor figure exactly.
Illinois does NOT show this pattern (its raw project sum doesn't match its
old telecompetitor figure either).

**Illinois follow-up (2026-09-23):** ruled out the two most likely bugs,
found a real but different-shaped discrepancy. Re-confirmed IL's NTIA
figure is current, not stale -- refetched the PDF (it now lives under a
`2026-08` date-folder path, moved since the original check, but the
document itself still reads "Updated 11/24/2025" with the same
$831,161,724 Total Deployment Cost, so nothing changed upstream). Checked
for duplicate/double-counted data directly: 0 duplicate `project_id`s, 0
`location_id`s appearing under more than one project, 0 IL projects
missing from LOCATION.csv (so no Unknown-bucket contribution either) --
all $935,758,035.68 of IL's granular total is tied to 232 real projects
covering 155,734 *unique* locations, no double-counting found anywhere.

The real gap: IL's own PDF reports 142,546 "Eligible Broadband
Serviceable Locations" against a technology mix of Fiber 97,122 (68.1%),
Fixed Wireless (all types combined) 33,610 (23.6%), LEO Satellite 11,490
(8.1%), Hybrid Fiber-Coax 194 (0.2%). This project's granular location
counts for IL are Fiber 107,678, LEO 24,224, Fixed Wireless (Licensed +
LBR + Unlicensed combined) 23,352, Cable 480 -- fiber and LEO both come in
notably *higher* than NTIA's category totals, fixed wireless notably
*lower*, netting to 155,734 total vs. NTIA's 142,416-142,546, an excess of
~13,200 locations that roughly tracks (but doesn't cleanly reconcile
against) the $104.6M dollar gap. This isn't a duplicate-counting or
stale-data bug -- it looks like a genuine scope or technology-classification
difference between broadbandexpanded.com's project-level location lists
and NTIA's own "eligible locations" summary count, but the exact mechanism
(some other state's projects showing the opposite pattern, technology
code mapping, or a real scope difference in which locations a funded
project is allowed to include beyond the strict BEAD-eligible set) isn't
pinned down. Would need either a location-level join against NTIA's own
BSL eligibility list (not present in this dataset) or the same close-read
applied to a few other flagged states to see if this pattern generalizes,
neither attempted here.

Open items now: (1) DC's provisional award is still on the unverified
telecompetitor.com estimate (no NTIA overview PDF exists for it) --
re-check periodically in case NTIA publishes one later; (2) Illinois's
+12.6% gap (granular $935.8M vs. NTIA-verified $831.2M) is confirmed NOT a
duplicate-counting or stale-snapshot bug (see the 2026-09-23 follow-up
above), but the real cause -- a ~13,200-location, technology-mix-shaped
discrepancy between this project's location counts and NTIA's own
category totals -- is still not pinned down; would need a location-level
join against NTIA's eligibility data (not available here) or a check of
whether other flagged states show the same fiber/LEO-up,
fixed-wireless-down pattern.

~~(3) CAI_20260827.csv (community anchor institutions) carries real
latitude/longitude per funded site -- could support an actual point-density
map of funded locations~~ -- done 2026-09-23 (`scripts/build_cai_locations.py`,
canvas point-density map, 22,675 plotted institutions, spatial-index
clustering on hover). Type-code labels (S/F/H/L/C/P/G) are inferred from
entity-name patterns, not an official codebook -- none found.

~~(4) NO_BEAD_20260827.csv (excluded/ineligible locations with a reason
code) is unused -- could show which locations were considered and
rejected, not just which were funded~~ -- done 2026-09-23
(`scripts/build_bead_no_bead_summary.py`). Reason codes decoded from NTIA's
own "BEAD Final Proposal Guidance v1.2" PDF (primary source, pages 41-44),
not guessed from the numeric codes alone. Headline: of 1,097,151 excluded
locations nationally, 67.5% were already being served some other way
(private service or another federal/state program), 22.5% turned out not
to be real locations (removed from the FCC Fabric), and only 330 (0.03%,
used by 3 states) were excluded because an Eligible Entity said it
couldn't afford to serve them.

~~(5) noticed in passing while investigating NC: at least one BEAD project
nationally has `project_type == "M"` (middle-mile, not last-mile) and
appears to have no matching rows in LOCATION.csv -- middle-mile projects
may be silently excluded~~ -- checked directly 2026-09-23 and resolved:
`PROJECT_20260827.csv`'s `project_type` breaks down as L=5,608 (last-mile),
NaN=150, C=15, c=26, l=6, and exactly **1** M (middle-mile) project
nationally -- the $13.05M NC project already spotted. `project_type` isn't
loaded or filtered on anywhere in `build_bead_final_proposal.py`, so there
is no type-based exclusion path; the M project is simply one of the 56
projects nationally ($88.0M combined, matches exactly) with zero
LOCATION.csv rows, already caught by the existing Unknown-bucket fix from
the SD/DC investigation above. Checked each project_type's total dollar
exposure and no-location-count too (C: 15/15 all missing, $2.07M; c: 26/26
all missing, $19.50 -- both effectively test/placeholder rows given the
tiny dollar amounts; L: 14/5,608 missing, $72.9M -- the bulk of the $88M;
l and NaN: 0 missing). Nothing here understates any state's total beyond
what the Unknown bucket already surfaces. A guard test
(`test_middle_mile_projects_are_not_excluded`) was added so a future
change can't quietly reintroduce a project_type filter.

International comparison remains an unscoped stretch goal -- would need
its own research pass before any build, not something to start
opportunistically.
