# Connectivity Cost Index

**Is satellite internet's pricing premium justified by its performance, or is it a connectivity tax paid for coverage rather than speed?**

This project builds a cost-per-Mbps comparison across internet access technologies (LEO satellite, fixed wireless, cable, fiber, DSL, cellular), using public data rather than marketing claims, and overlays real personal connection data as a live case study.

## Three data layers

1. **Market layer** — [FCC National Broadband Map](https://broadbandmap.fcc.gov/) bulk CSV downloads (free, no API key — coverage by technology per location, with satellite split into GSO vs. LEO) + published ISP/carrier pricing → cost-per-Mbps by technology, by region.
2. **Regional performance layer** — [Ookla Open Data](https://github.com/teamookla/ookla-open-data) and/or [M-Lab](https://www.measurementlab.net/data/) → actual measured speed/latency by region and technology, not advertised speed.
3. **Personal layer** — a lightweight logger (speedtest-cli / Cloudflare speedtest) tracking the author's own broadband and cellular connections over time, plotted against the regional baseline from layer 2.

Satellite providers (Starlink, Kuiper, AST SpaceMobile) are covered in the market layer only — the personal logger currently tracks broadband + cellular; satellite can be added if/when access exists.

## Status

Early scaffolding — Phase 1 (market-layer data pull) in progress.

## License

MIT — see [LICENSE](LICENSE).
