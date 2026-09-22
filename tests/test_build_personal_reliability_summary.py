"""Unit tests for the personal reliability logger's aggregation logic.
Uses a synthetic fixture DB -- never reads the real data/personal_logs.db,
which is off limits by design (PII classifier)."""

import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build_personal_reliability_summary import METRICS, load_samples, summarize

SCHEMA = """
CREATE TABLE samples (
    ts REAL NOT NULL,
    label TEXT NOT NULL,
    download_mbps REAL,
    upload_mbps REAL,
    latency_avg_ms REAL,
    latency_jitter_ms REAL,
    packet_loss_pct REAL
);
"""

FIXTURE_ROWS = [
    (1.0, "home-wifi", 100.0, 20.0, 12.0, 1.5, 0.0),
    (2.0, "home-wifi", 80.0, 18.0, 14.0, 2.5, 0.5),
    (3.0, "home-wifi", 90.0, 19.0, 13.0, 2.0, 0.0),
    (4.0, "cellular-tether", 30.0, 5.0, 40.0, 8.0, 1.0),
    (5.0, "cellular-tether", 10.0, 3.0, 60.0, 12.0, 3.0),
]


@pytest.fixture
def fixture_db(tmp_path) -> Path:
    db_path = tmp_path / "personal_logs_fixture.db"
    conn = sqlite3.connect(db_path)
    conn.execute(SCHEMA)
    conn.executemany("INSERT INTO samples VALUES (?, ?, ?, ?, ?, ?, ?)", FIXTURE_ROWS)
    conn.commit()
    conn.close()
    return db_path


def test_load_samples_reads_all_rows(fixture_db):
    samples = load_samples(fixture_db)
    assert len(samples) == len(FIXTURE_ROWS)


def test_summarize_produces_one_row_per_label(fixture_db):
    samples = load_samples(fixture_db)
    result = summarize(samples)
    assert set(result["label"]) == {"home-wifi", "cellular-tether"}
    assert len(result) == 2


def test_summarize_sample_counts_are_correct(fixture_db):
    samples = load_samples(fixture_db)
    result = summarize(samples)
    counts = dict(zip(result["label"], result["sample_count"]))
    assert counts["home-wifi"] == 3
    assert counts["cellular-tether"] == 2


def test_summarize_mean_math_is_correct(fixture_db):
    samples = load_samples(fixture_db)
    result = summarize(samples)
    home = result[result["label"] == "home-wifi"].iloc[0]
    assert home["download_mbps_mean"] == round((100.0 + 80.0 + 90.0) / 3, 2)


def test_summarize_has_all_metric_stat_columns(fixture_db):
    samples = load_samples(fixture_db)
    result = summarize(samples)
    for metric in METRICS:
        for stat in ("mean", "median", "min", "max", "std"):
            assert f"{metric}_{stat}" in result.columns


def test_summarize_tracks_first_and_last_sample_ts(fixture_db):
    samples = load_samples(fixture_db)
    result = summarize(samples)
    cellular = result[result["label"] == "cellular-tether"].iloc[0]
    assert cellular["first_sample_ts"] == 4.0
    assert cellular["last_sample_ts"] == 5.0
