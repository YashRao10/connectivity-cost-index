# Connectivity Cost Index

**Is satellite internet's pricing premium justified by its performance, or is it a connectivity tax paid for coverage rather than speed?**

A cost-per-Mbps comparison across internet access technologies (LEO satellite, GSO satellite, fiber, cable, DSL, fixed wireless), using public data instead of marketing claims, across **all 50 states + DC**.

**Headline finding:** LEO satellite (Starlink) beats Licensed Fixed Wireless (Verizon 5G Home / T-Mobile Home Internet, the actual 5G-home-internet product, not a niche one) on cost-per-Mbps in every single state (51 of 51), but not by a fixed margin: the gap ranges from a modest 2.1x in Idaho to 25.5x in Alaska. It's not the worst value everywhere, though: DSL in Rhode Island and unlicensed fixed wireless pricing in Hawaii, Nevada, and Rhode Island all beat it. The real story is less "satellite always wins" and more "satellite reliably beats its most direct national competitor everywhere, while losing occasionally to cheaper legacy/local options and consistently to wired infrastructure where that exists." See the live site for full methodology, caveats, and how this finding changed (and got more precise) as the sample grew from an initial 10-state pilot to full national coverage.

## Four data/analysis layers

1. **Market layer**: [FCC National Broadband Map](https://broadbandmap.fcc.gov/) bulk CSV downloads (free, no API key; coverage by technology per location, satellite split into GSO vs. LEO, fixed wireless split into licensed/unlicensed/LBR) + published ISP/carrier pricing → cost-per-Mbps by technology, by state. All 50 states + DC.
2. **Real-world performance layer**: [Ookla Open Data](https://github.com/teamookla/ookla-open-data), spatially joined against real US Census state boundaries (not a bounding-box approximation), refreshed automatically each quarter via GitHub Actions → actual measured speed/latency vs. advertised, plus a Q1→Q2 2026 quarter-over-quarter trend. All 50 states + DC.
3. **Policy layer**: NTIA BEAD program provisional awards by state, individually verified against NTIA's own official per-state "BEAD Final Proposal Overview" PDFs for 50 of 51 states + DC (the original telecompetitor.com-sourced figures checked out unreliable: only 12 of 27 spot-checked states matched within 2%), surfaced as both a table and an interactive US choropleth map. Four sub-layers built on the same underlying BEAD Final Proposal project data (5,806 real funded projects): (a) the state-total table/map above; (b) a granular per-technology breakdown: satellite (GSO+LEO) is 22% of all funded locations at $701–1,138/location vs. fiber's $6,420.70/location, a real 5.6× gap, not an estimate; (c) a point-density map of the 22,675 individual BEAD-funded community institutions (schools, libraries, clinics, etc.); (d) a breakdown of the 1.1M BEAD-eligible locations that did *not* get funded, by NTIA's own official reason code: 67.5% were already served some other way, only 0.03% were a state saying it couldn't afford to serve them. All 50 states + DC.
4. **Personal reliability layer (in progress)**: a lightweight logger (Cloudflare speed-test endpoints + ping, no external dependencies) running on real broadband/cellular connections, building toward a personal-vs-market overlay once enough data has accumulated.

The live site (`docs/index.html`) also has filtering/sorting on the full technology comparison table, and an interactive choropleth map covering all 50 states + DC (AK/HI render as AlbersUSA insets; only non-state territories PR/GU/VI/AS/MP are excluded; see `scripts/build_state_map_data.py`).

## Repo layout

- `scripts/`: data pull and build scripts (FCC, Ookla, Census shapefiles, BEAD, cost comparison)
- `data/`: small, committed summary/output CSVs and the map GeoJSON; `data/raw/` is gitignored (large source files, regenerated on demand, not stored in git)
- `docs/`: the published site (GitHub Pages)
- `logger/`: the personal connectivity logger + scheduling configs (launchd/Task Scheduler)
- `.github/workflows/`: the quarterly Ookla refresh automation

## Status

Actively developed, v4.0. Market, real-world, and policy layers all at full 50-states-+-DC coverage; personal layer collecting data; interactivity (filter/sort + choropleth map + CAI point-density map) shipped, plus a plain-language explainer of how each of the seven technologies physically works (with a to-scale orbit diagram and latency-physics floors), a BEAD technology-mix share bar with per-technology cost cards, and a shareable per-state lookup (pick a state or click the map; the URL updates to `#state=XX`). Started as a 10-state pilot in one region-spread sample (West Coast, Sun Belt, Midwest, Mountain West, Northeast/major-metro) and scaled to full national coverage. See the site's methodology section for how several early findings got corrected or sharpened once the sample grew, including a same-day BEAD accuracy overhaul (2026-09-23) that replaced a secondary-source dataset checked out unreliable with primary NTIA-verified figures.

## License

MIT. See [LICENSE](LICENSE).
