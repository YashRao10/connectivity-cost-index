"""Summarize the personal connectivity logger's raw samples
(data/personal_logs.db, written by logger/collect_sample.py) into
per-label aggregates for the site's personal reliability layer.

Scaffolded ahead of having enough accumulated samples to be worth
publishing -- run it for real once data/personal_logs.db has meaningful
history. Never read personal_logs.db content directly outside this
aggregation path; only the aggregated summary (no raw per-sample rows)
is meant to leave this script.

Usage:
    python scripts/build_personal_reliability_summary.py

Output: data/personal_reliability_summary.csv
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "personal_logs.db"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "personal_reliability_summary.csv"

METRICS = ["download_mbps", "upload_mbps", "latency_avg_ms", "latency_jitter_ms", "packet_loss_pct"]


def load_samples(db_path: Path) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    try:
        return pd.read_sql_query("SELECT * FROM samples", conn)
    finally:
        conn.close()


def summarize(samples: pd.DataFrame) -> pd.DataFrame:
    grouped = samples.groupby("label")
    summary = grouped[METRICS].agg(["mean", "median", "min", "max", "std"])
    summary.columns = [f"{metric}_{stat}" for metric, stat in summary.columns]
    summary["sample_count"] = grouped.size()
    summary["first_sample_ts"] = grouped["ts"].min()
    summary["last_sample_ts"] = grouped["ts"].max()
    return summary.reset_index().round(2)


if __name__ == "__main__":
    if not DB_PATH.exists():
        raise SystemExit(
            f"Missing {DB_PATH} -- run logger/collect_sample.py to collect samples first"
        )
    samples = load_samples(DB_PATH)
    if samples.empty:
        raise SystemExit(f"{DB_PATH} has no samples yet")

    result = summarize(samples)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {len(result)} label summaries to {OUTPUT_PATH}")
