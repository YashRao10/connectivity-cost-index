"""Pull Ookla Open Data (Speedtest) performance tiles for fixed and mobile networks.

Public, anonymous S3 access -- no AWS credentials needed:
    https://ookla-open-data.s3.amazonaws.com/

Layout: parquet/performance/type={fixed|mobile}/year=YYYY/quarter=Q/
        YYYY-MM-01_performance_{fixed|mobile}_tiles.parquet

Each quarterly file is nationwide, tile-level (~610m tiles), and roughly
300-400MB. This script downloads to data/raw/ookla/ and then filters down
to a handful of regions of interest to keep the working dataset small.

Usage:
    python scripts/pull_ookla.py --year 2026 --quarter 2 --type fixed
    python scripts/pull_ookla.py --latest --type fixed   # auto-fallback to
                                                          # most recent published quarter

--latest is what the scheduled GitHub Actions refresh uses: Ookla publishes
each quarter's file with a lag (typically several weeks after quarter-end),
so "the current calendar quarter" is often not live yet. It starts from the
current calendar quarter and walks backward until it finds one that exists
(HTTP 200 on a HEAD request), rather than hardcoding an assumed lag.
"""

import argparse
import datetime
from pathlib import Path

import requests

BASE_URL = "https://ookla-open-data.s3.amazonaws.com/parquet/performance"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "ookla"

QUARTER_START_MONTH = {1: "01", 2: "04", 3: "07", 4: "10"}


def tile_url(year: int, quarter: int, net_type: str) -> str:
    month = QUARTER_START_MONTH[quarter]
    filename = f"{year}-{month}-01_performance_{net_type}_tiles.parquet"
    return f"{BASE_URL}/type={net_type}/year={year}/quarter={quarter}/{filename}", filename


def find_latest_available(net_type: str, max_lookback: int = 6) -> tuple[int, int]:
    """Walk backward from the current calendar quarter until one exists."""
    today = datetime.datetime.now(tz=datetime.UTC).date()
    year, quarter = today.year, (today.month - 1) // 3 + 1
    for _ in range(max_lookback):
        url, _ = tile_url(year, quarter, net_type)
        if requests.head(url, timeout=30).status_code == 200:
            return year, quarter
        quarter -= 1
        if quarter == 0:
            quarter = 4
            year -= 1
    raise RuntimeError(
        f"No published {net_type} tile file found in the last {max_lookback} quarters"
    )


def download_tile_file(year: int, quarter: int, net_type: str) -> Path:
    url, filename = tile_url(year, quarter, net_type)
    out_dir = RAW_DIR / net_type
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / filename

    if out_path.exists():
        print(f"Already have {out_path}")
        return out_path

    print(f"Downloading {url} -> {out_path}")
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        written = 0
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
                written += len(chunk)
                if total:
                    print(f"\r{written / total:.0%}", end="", flush=True)
    print(f"\nSaved {out_path} ({out_path.stat().st_size / 1e6:.1f} MB)")
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int)
    parser.add_argument("--quarter", type=int, choices=[1, 2, 3, 4])
    parser.add_argument("--type", choices=["fixed", "mobile"], default="fixed")
    parser.add_argument(
        "--latest", action="store_true",
        help="Auto-find the most recent published quarter instead of --year/--quarter",
    )
    args = parser.parse_args()

    if args.latest:
        year, quarter = find_latest_available(args.type)
        print(f"Latest available {args.type} quarter: {year} Q{quarter}")
    elif args.year and args.quarter:
        year, quarter = args.year, args.quarter
    else:
        parser.error("Provide either --latest or both --year and --quarter")

    download_tile_file(year, quarter, args.type)
