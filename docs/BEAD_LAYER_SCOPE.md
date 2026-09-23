# Policy/econ layer scope: BEAD grants vs. actual market gaps

Roadmap item 3 (2026-09-20 planning session). Goal: connect public subsidy
spending to the market-layer findings already in this project -- is BEAD
money going where the FCC data says the actual gaps are, and at what
implied cost per unserved location?

**Status as of 2026-09-22: both the "simple version" and the granular
version are built and live.** Simple: `scripts/build_bead_comparison.py` ->
`data/bead_allocation_v2.csv`, all 50 states + DC, using the 2025 "Benefit
of the Bargain" provisional awards. Granular: `scripts/build_bead_final_proposal.py`
-> `data/bead_final_proposal_by_state_tech.csv` + `data/bead_final_proposal_reconciliation.csv`,
using the real 5,806-project BEAD Final Proposal data from
broadbandexpanded.com -- this directly answers the "are states leaning on
BEAD to build infrastructure where satellite is already cost-competitive"
question posed below: yes, satellite is 22.0% of all funded locations at
$701-1,138/location vs. fiber's $6,420.70/location, a real 5.6x gap. The
rest of this doc is left as-written from the original planning session for
context on what was decided and why -- see the live site's two BEAD
sections and their methodology changelog entries for the current, public
framing (including the state-level reconciliation caveat: 10 of 50 states'
totals disagree >=15% between the two sources, not yet resolved to a
single cause).

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

## Recommended next step (as of 2026-09-22)

Both versions are built and live -- see status note at the top of this
doc. Open items now: (1) reconciling the 10 flagged states where the
granular project-level totals and the state-total figures disagree >=15%
-- would need a primary NTIA source per flagged state to resolve, not
attempted yet; (2) CAI_20260827.csv (community anchor institutions, not
used in this build) carries real latitude/longitude per funded site --
could support an actual point-density map of funded locations someday,
not attempted here, the existing map still uses the state-total proxy;
(3) NO_BEAD_20260827.csv (57.9MB, excluded/ineligible locations with a
reason code) is also unused -- could show which locations were considered
and rejected, not just which were funded. International comparison
remains an unscoped stretch goal -- would need its own research pass
before any build, not something to start opportunistically.
