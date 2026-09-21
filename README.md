# Connectivity Cost Index

**Is satellite internet's pricing premium justified by its performance, or is it a connectivity tax paid for coverage rather than speed?**

A cost-per-Mbps comparison across internet access technologies (LEO satellite, GSO satellite, fiber, cable, DSL, fixed wireless), using public data instead of marketing claims, across **all 50 states + DC**.

**Headline finding:** LEO satellite (Starlink) beats Licensed Fixed Wireless (Verizon 5G Home / T-Mobile Home Internet — the actual 5G-home-internet product, not a niche one) on cost-per-Mbps in every single state (51 of 51), but not by a fixed margin — the gap ranges from a modest 2.1x in Idaho to 25.5x in Alaska. It's not the worst value everywhere, though: DSL in Rhode Island and unlicensed fixed wireless pricing in Hawaii, Nevada, and Rhode Island all beat it. The real story is less "satellite always wins" and more "satellite reliably beats its most direct national competitor everywhere, while losing occasionally to cheaper legacy/local options and consistently to wired infrastructure where that exists." See the live site for full methodology, caveats, and how this finding changed (and got more precise) as the sample grew from an initial 10-state pilot to full national coverage.

## Four data/analysis layers

1. **Market layer** — [FCC National Broadband Map](https://broadbandmap.fcc.gov/) bulk CSV downloads (free, no API key; coverage by technology per location, satellite split into GSO vs. LEO, fixed wireless split into licensed/unlicensed/LBR) + published ISP/carrier pricing → cost-per-Mbps by technology, by state. All 50 states + DC.
2. **Real-world performance layer** — [Ookla Open Data](https://github.com/teamookla/ookla-open-data), spatially joined against real US Census state boundaries (not a bounding-box approximation), refreshed automatically each quarter via GitHub Actions → actual measured speed/latency vs. advertised, plus a Q1→Q2 2026 quarter-over-quarter trend. All 50 states + DC.
3. **Policy layer** — NTIA BEAD program allocations vs. GSO-satellite-served locations as an underserved-locations proxy, verified against the 2025 "Benefit of the Bargain" restructuring (not just the original 2023 announcement, which is confirmed wrong for several states post-restructuring) — surfaced as both a table and an interactive US choropleth map. All 50 states + DC.
4. **Personal reliability layer (in progress)** — a lightweight logger (Cloudflare speed-test endpoints + ping, no external dependencies) running on real broadband/cellular connections, building toward a personal-vs-market overlay once enough data has accumulated.

The live site (`docs/index.html`) also has filtering/sorting on the full technology comparison table, and an interactive choropleth map (the map itself excludes AK/HI/territories for projection simplicity — see `scripts/build_state_map_data.py` — though both have real data in every other layer and table).

## Repo layout

- `scripts/` — data pull and build scripts (FCC, Ookla, Census shapefiles, BEAD, cost comparison)
- `data/` — small, committed summary/output CSVs and the map GeoJSON; `data/raw/` is gitignored (large source files, regenerated on demand, not stored in git)
- `docs/` — the published site (GitHub Pages)
- `logger/` — the personal connectivity logger + scheduling configs (launchd/Task Scheduler)
- `.github/workflows/` — the quarterly Ookla refresh automation

## Status

Actively developed. Market, real-world, and policy layers all at full 50-states-+-DC coverage; personal layer collecting data; interactivity (filter/sort + choropleth map) shipped. Started as a 10-state pilot in one region-spread sample (West Coast, Sun Belt, Midwest, Mountain West, Northeast/major-metro) and scaled to full national coverage — see the site's methodology section for how several early findings got corrected or sharpened once the sample grew.

## License

MIT — see [LICENSE](LICENSE).
