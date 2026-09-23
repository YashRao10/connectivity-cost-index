"""Log one connectivity sample: download/upload throughput, latency, jitter,
packet loss. Appends a row to a local SQLite DB.

No external dependencies beyond `requests` (already used elsewhere in this
repo) -- uses Cloudflare's public speed-test endpoints (speed.cloudflare.com)
rather than requiring speedtest-cli/speedtest to be installed, and the
system `ping` binary for latency/jitter/packet loss.

Usage:
    python logger/collect_sample.py --label home-wifi
    python logger/collect_sample.py --label cellular-tether

--label is required and freeform (e.g. "home-wifi", "cellular-tether") --
scope is broadband + cellular per project decision; satellite stays in the
market-layer analysis only unless/until that access exists.
"""

from __future__ import annotations

import argparse
import platform
import re
import sqlite3
import statistics
import subprocess
import time
from pathlib import Path

import requests

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "personal_logs.db"
CF_DOWN_URL = "https://speed.cloudflare.com/__down?bytes={size}"
CF_UP_URL = "https://speed.cloudflare.com/__up"
DOWNLOAD_BYTES = 10_000_000  # 10MB
UPLOAD_BYTES = 5_000_000  # 5MB
PING_TARGET = "1.1.1.1"
PING_COUNT = 10

SCHEMA = """
CREATE TABLE IF NOT EXISTS samples (
    ts REAL NOT NULL,
    label TEXT NOT NULL,
    download_mbps REAL,
    upload_mbps REAL,
    latency_avg_ms REAL,
    latency_jitter_ms REAL,
    packet_loss_pct REAL
);
"""


def measure_download() -> float | None:
    try:
        start = time.monotonic()
        resp = requests.get(CF_DOWN_URL.format(size=DOWNLOAD_BYTES), timeout=30)
        resp.raise_for_status()
        elapsed = time.monotonic() - start
        bits = len(resp.content) * 8
        return round((bits / elapsed) / 1_000_000, 2)
    except requests.RequestException:
        return None


def measure_upload() -> float | None:
    try:
        payload = b"0" * UPLOAD_BYTES
        start = time.monotonic()
        resp = requests.post(CF_UP_URL, data=payload, timeout=30)
        resp.raise_for_status()
        elapsed = time.monotonic() - start
        bits = len(payload) * 8
        return round((bits / elapsed) / 1_000_000, 2)
    except requests.RequestException:
        return None


def measure_ping():
    is_windows = platform.system() == "Windows"
    count_flag = "-n" if is_windows else "-c"
    try:
        out = subprocess.run(
            ["ping", count_flag, str(PING_COUNT), PING_TARGET],
            capture_output=True,
            text=True,
            timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if is_windows else 0,
        ).stdout
    except subprocess.SubprocessError:
        return None, None, None

    # Packet loss: Windows says "Lost = 0 (0% loss)", macOS/Linux say
    # "X% packet loss" -- try both rather than branching on platform, in
    # case wording changes across OS versions.
    loss_match = re.search(r"\(([\d.]+)%\s*loss\)", out) or re.search(
        r"([\d.]+)% packet loss", out
    )
    packet_loss = float(loss_match.group(1)) if loss_match else None

    # Compute avg/jitter ourselves from individual reply times rather than
    # trusting each OS's own summary line -- Windows ping doesn't report
    # stddev/jitter at all, only min/max/avg, so this is the only way to
    # get a jitter figure on Windows. Matches "time=12ms" (Windows) and
    # "time=12.345 ms" (macOS/Linux) with one regex.
    times = [float(m) for m in re.findall(r"time[=<]([\d.]+)\s*ms", out)]
    if times:
        avg_ms = round(statistics.mean(times), 2)
        jitter_ms = round(statistics.stdev(times), 2) if len(times) > 1 else 0.0
    else:
        avg_ms = jitter_ms = None
    return avg_ms, jitter_ms, packet_loss


def save_sample(label: str, download_mbps, upload_mbps, latency_avg_ms, latency_jitter_ms, packet_loss_pct) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(SCHEMA)
    conn.execute(
        "INSERT INTO samples VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            time.time(),
            label,
            download_mbps,
            upload_mbps,
            latency_avg_ms,
            latency_jitter_ms,
            packet_loss_pct,
        ),
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True, help="e.g. home-wifi, cellular-tether")
    args = parser.parse_args()

    down = measure_download()
    up = measure_upload()
    avg_ms, jitter_ms, loss_pct = measure_ping()

    save_sample(args.label, down, up, avg_ms, jitter_ms, loss_pct)
    print(
        f"[{args.label}] down={down} Mbps up={up} Mbps "
        f"latency={avg_ms} ms jitter={jitter_ms} ms loss={loss_pct}%"
    )
