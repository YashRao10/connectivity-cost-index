# Policy/econ layer scope: BEAD grants vs. actual market gaps

Roadmap item 3 (2026-09-20 planning session). Goal: connect public subsidy
spending to the market-layer findings already in this project -- is BEAD
money going where the FCC data says the actual gaps are, and at what
implied cost per unserved location?

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

- Whether to pull the granular Final Proposal data (project-level) or start
  with just the simple state-allocation-total join -- the simple version is
  a day of work, the granular version is comparable in size to the FCC
  fixed-broadband pull and would need the same memory-safety treatment
  (usecols/dtypes/no full-frame copy) that load_fcc_broadband.py needed.
- International comparison (Canada/UK/EU) was floated as a stretch goal --
  not scoped at all yet; different regulatory bodies, different data
  formats per country, likely a separate research pass before any build.
- This layer only makes sense once the state sample is bigger than 3 (the
  scaling work is happening in parallel on the desktop side) -- a
  3-state BEAD comparison isn't enough states to say anything about
  allocation patterns.

## Recommended next step

Start with the simple version: state-allocation-total join against the
existing FCC summary once the state list is bigger (waiting on the
scaling work), rather than committing to the granular Final Proposal
pull before knowing if the simple version is even interesting.
