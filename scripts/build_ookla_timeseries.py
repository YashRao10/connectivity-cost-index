"""Multi-quarter Ookla trend. Reuses the already-committed
data/ookla_regional_summary.csv as the "current quarter" (2026 Q2) rather
than re-downloading its ~530MB of raw tiles, and computes a fresh summary
for one prior quarter (2026 Q1) to diff against it. Extend PRIOR_QUARTERS
to build a longer trend once more history is wanted.

Usage:
    python scripts/pull_ookla.py --year 2026 --quarter 1 --type fixed
    python scripts/pull_ookla.py --year 2026 --quarter 1 --type mobile
    python scripts/build_ookla_timeseries.py

Output: data/ookla_timeseries.csv
"""

from pathlib import Path

import pandas as pd
from load_ookla_regional import load_and_filter, load_state_boundaries, summarize

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_DIR = DATA_DIR / "raw" / "ookla"
CURRENT_QUARTER = (2026, 2)  # matches data/ookla_regional_summary.csv

# (year, quarter, filename-date-stamp) for quarters to compute fresh and
# diff against CURRENT_QUARTER.
PRIOR_QUARTERS = [
    (2026, 1, "2026-01-01"),
]


def summarize_quarter(year: int, quarter: int, date_stamp: str, states) -> pd.DataFrame:
    frames = []
    for net_type in ("fixed", "mobile"):
        path = RAW_DIR / net_type / f"{date_stamp}_performance_{net_type}_tiles.parquet"
        if not path.exists():
            raise SystemExit(
                f"Missing {path} -- run: python scripts/pull_ookla.py "
                f"--year {year} --quarter {quarter} --type {net_type}"
            )
        raw = load_and_filter(path, states)
        summary = summarize(raw, net_type)
        summary["year"] = year
        summary["quarter"] = quarter
        frames.append(summary)
    return pd.concat(frames, ignore_index=True)


if __name__ == "__main__":
    states = load_state_boundaries()

    current = pd.read_csv(DATA_DIR / "ookla_regional_summary.csv")
    current["year"], current["quarter"] = CURRENT_QUARTER

    prior = pd.concat(
        [summarize_quarter(y, q, d, states) for y, q, d in PRIOR_QUARTERS],
        ignore_index=True,
    )

    all_quarters = pd.concat([prior, current], ignore_index=True)

    # Quarter-over-quarter delta on median_down_mbps, per state + network type.
    all_quarters = all_quarters.sort_values(["state_usps", "network_type", "year", "quarter"])
    all_quarters["prev_median_down_mbps"] = all_quarters.groupby(
        ["state_usps", "network_type"]
    )["median_down_mbps"].shift(1)
    all_quarters["down_mbps_qoq_change_pct"] = (
        (all_quarters["median_down_mbps"] - all_quarters["prev_median_down_mbps"])
        / all_quarters["prev_median_down_mbps"]
        * 100
    ).round(1)

    print(
        all_quarters[
            [
                "state_usps", "network_type", "year", "quarter",
                "median_down_mbps", "down_mbps_qoq_change_pct",
            ]
        ].to_string(index=False)
    )
    out_path = DATA_DIR / "ookla_timeseries.csv"
    all_quarters.to_csv(out_path, index=False)
    print(f"\nWrote {out_path}")
