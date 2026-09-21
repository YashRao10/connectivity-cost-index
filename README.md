# Connectivity Cost Index

**Is satellite internet's pricing premium justified by its performance, or is it a connectivity tax paid for coverage rather than speed?**

A cost-per-Mbps comparison across internet access technologies (LEO satellite, GSO satellite, fiber, cable, DSL, fixed wireless), using public data instead of marketing claims, across 10 states chosen for regional spread — West Coast, Sun Belt, Midwest, Mountain West, and Northeast/major-metro.

**Headline finding:** LEO satellite (Starlink) beats Licensed Fixed Wireless (Verizon 5G Home / T-Mobile Home Internet) by exactly 10x on cost-per-Mbps, in every one of the 10 states tested — metro and rural alike. It's not the worst value anywhere; it only loses to wired infrastructure (cable, fiber) where that infrastructure actually exists. See the live site for the full methodology and caveats, including an explicit note on where that 10x figure is a real market-structure finding vs. a mechanical constant of national pricing.

## Four data/analysis layers

1. **Market layer** — [FCC National Broadband Map](https://broadbandmap.fcc.gov/) bulk CSV downloads (free, no API key; coverage by technology per location, satellite split into GSO vs. LEO, fixed wireless split into licensed/unlicensed/LBR) + published ISP/carrier pricing → cost-per-Mbps by technology, by state.
2. **Real-world performance layer** — [Ookla Open Data](https://github.com/teamookla/ookla-open-data), spatially joined against real US Census state boundaries (not a bounding-box approximation), refreshed automatically each quarter via GitHub Actions → actual measured speed/latency vs. advertised.
3. **Policy layer** — NTIA BEAD program state allocations vs. GSO-satellite-served locations as an underserved-locations proxy, surfaced as both a table and an interactive US choropleth map.
4. **Personal reliability layer (in progress)** — a lightweight logger (Cloudflare speed-test endpoints + ping, no external dependencies) running on real broadband/cellular connections, building toward a personal-vs-market overlay once enough data has accumulated.

The live site (`docs/index.html`) also has filtering/sorting on the full technology comparison table.

## Repo layout

- `scripts/` — data pull and build scripts (FCC, Ookla, Census shapefiles, BEAD, cost comparison)
- `data/` — small, committed summary/output CSVs and the map GeoJSON; `data/raw/` is gitignored (large source files, regenerated on demand, not stored in git)
- `docs/` — the published site (GitHub Pages)
- `logger/` — the personal connectivity logger + scheduling configs (launchd/Task Scheduler)
- `.github/workflows/` — the quarterly Ookla refresh automation

## Status

Actively developed. 10-state market + real-world + policy layers live; personal layer collecting data; interactivity (filter/sort + choropleth map) shipped.

## License

MIT — see [LICENSE](LICENSE).
