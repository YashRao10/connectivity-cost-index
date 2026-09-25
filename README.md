# Connectivity Cost Index

**Is satellite internet's pricing premium justified by its performance, or is it a connectivity tax paid for coverage rather than speed?**

**[Live site](https://yashrao10.github.io/connectivity-cost-index/)** · every home internet technology, priced per Mbps, across **all 50 states + DC**, from public data instead of marketing claims.

## Key findings

- **Starlink beats 5G home internet on cost per Mbps in all 51 states/DC**, by 2.1x (Idaho) to 25.5x (Alaska), and it is the only technology without a wire that meets the FCC's 100/20 Mbps broadband definition at the state median everywhere. 5G home internet meets it in 1 state.
- **But wired service wins wherever it reaches.** Where fiber or cable exists, Starlink costs 4.3x (New Mexico) to 49x (Connecticut, West Virginia) more per Mbps than the cheapest wired option, median 8.9x.
- **A few local options beat it too:** unlicensed fixed wireless in Hawaii, Nevada, and Rhode Island, and DSL in Delaware and Rhode Island (two tiny FCC populations of 4 and 14 locations).
- **Affordability:** at the median household income, Starlink's $55 plan is 0.56% (Massachusetts) to 1.14% (Mississippi) of monthly income.
- **BEAD subsidies:** the 2025 restructuring cut the median state's award by 62%. Satellite now serves 22% of BEAD-funded locations at $701 to $1,138 per location, vs. $6,420.70 for fiber, a 5.6x gap in real committed dollars.

The site's methodology section covers every caveat, and how several early findings were corrected or sharpened as the sample grew from a 10-state pilot to full national coverage.

## What's on the site

Seven parts, in reading order: the short answer; how each network physically works; what a Mbps costs (cost ranges, the FCC 100/20 check, and state maps of the satellite premium, share of income, and BEAD subsidy); what people actually get (Ookla speeds and the quarterly trend); where BEAD money goes; an explore section (state lookup with side-by-side compare, and the full table with CSV download); and the reliability layer, FAQ, and methodology.

## Data layers

1. **Market layer**: [FCC National Broadband Map](https://broadbandmap.fcc.gov/) bulk CSV downloads (free, no API key; coverage by technology per location, satellite split into GSO vs. LEO, fixed wireless split into licensed/unlicensed/LBR) + published ISP/carrier pricing → cost-per-Mbps by technology, by state. All 50 states + DC. Fiber, cable, and DSL are priced from each state's own largest provider for that technology (`data/state_top_providers.csv` + `data/provider_pricing.csv`, national plan as fallback); satellite and 5G home internet use their single national price.
2. **Real-world performance layer**: [Ookla Open Data](https://github.com/teamookla/ookla-open-data), spatially joined against real US Census state boundaries (not a bounding-box approximation), refreshed automatically each quarter via GitHub Actions → actual measured speed/latency vs. advertised, plus a Q1→Q2 2026 quarter-over-quarter trend. All 50 states + DC.
3. **Policy layer**: NTIA BEAD program provisional awards by state, individually verified against NTIA's own official per-state "BEAD Final Proposal Overview" PDFs for 50 of 51 states + DC (the original telecompetitor.com-sourced figures checked out unreliable: only 12 of 27 spot-checked states matched within 2%), surfaced as both a table and an interactive US choropleth map. Four sub-layers built on the same underlying BEAD Final Proposal project data (5,806 real funded projects): (a) the state-total table/map above; (b) a granular per-technology breakdown: satellite (GSO+LEO) is 22% of all funded locations at $701–1,138/location vs. fiber's $6,420.70/location, a real 5.6× gap, not an estimate; (c) a point-density map of the 22,675 individual BEAD-funded community institutions (schools, libraries, clinics, etc.); (d) a breakdown of the 1.1M BEAD-eligible locations that did *not* get funded, by NTIA's own official reason code: 67.5% were already served some other way, only 0.03% were a state saying it couldn't afford to serve them. All 50 states + DC.
4. **Affordability layer**: median household income by state (Census CPS, 2025) via [FRED](https://fred.stlouisfed.org/), which needs no API key, turned into each plan's share of median monthly income (`scripts/pull_state_income.py`).
5. **Personal reliability layer (in progress)**: a lightweight logger (Cloudflare speed-test endpoints + ping, no external dependencies) running on real broadband/cellular connections, building toward a personal-vs-market overlay once enough data has accumulated.

## Repo layout

- `scripts/`: data pull and build scripts (FCC, Ookla, Census shapefiles, BEAD, cost comparison)
- `data/`: small, committed summary/output CSVs and the map GeoJSON; `data/raw/` is gitignored (large source files, regenerated on demand, not stored in git)
- `docs/`: the published site (GitHub Pages)
- `logger/`: the personal connectivity logger + scheduling configs (launchd/Task Scheduler)
- `tests/`: pytest suite (build logic plus data-integrity checks on every committed CSV)
- `.github/workflows/`: CI (ruff + pytest) and the quarterly Ookla refresh

## Status

v4.2, actively developed. Market, real-world, policy, and affordability layers are at full 50-states-+-DC coverage; the personal reliability layer is still collecting data. Pricing is a September 2026 snapshot and Ookla data runs through Q2 2026 (refreshed quarterly by GitHub Actions).

To rebuild the site data from the committed CSVs: `python scripts/build_cost_comparison.py && python scripts/build_state_map_data.py && python scripts/regenerate_site_data.py`, then `pytest` (data-integrity and build tests) and `ruff check .`.

## License

MIT. See [LICENSE](LICENSE).
