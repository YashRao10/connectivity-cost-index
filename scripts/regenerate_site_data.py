"""Regenerate the embedded ROWS and OOKLA_ROWS JS data blocks in docs/index.html
straight from the current CSVs, instead of hand-editing the HTML after every
batch of new states. Only touches the two data arrays -- narrative prose,
the BEAD section, and the range-chart/table rendering logic are left alone,
since those need human judgment about wording, not just data.

Usage:
    python scripts/regenerate_site_data.py
"""

import re
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
HTML_PATH = Path(__file__).resolve().parent.parent / "docs" / "index.html"


def js_num(x):
    if pd.isna(x):
        return "null"
    x = float(x)
    # Site convention: cpm=null covers both "no pricing match" (price also
    # null) and "divide-by-zero" (price populated, e.g. NJ DSL's 0 Mbps
    # median) -- the renderer distinguishes the two cases by checking price,
    # not by a separate Infinity value. See docs/index.html's cpm renderer.
    if x in (float("inf"), float("-inf")):
        return "null"
    if x == int(x):
        return str(int(x))
    return str(round(x, 3))


def js_str(x):
    if pd.isna(x) or x is None:
        return "null"
    escaped = str(x).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def build_rows_block() -> str:
    df = pd.read_csv(DATA_DIR / "cost_comparison_v1.csv")
    df = df.sort_values(["state_usps", "technology_label"])
    lines = ["const ROWS = ["]
    for _, r in df.iterrows():
        lines.append(
            "  {{state:{}, tech:{}, provider:{}, price:{}, mbps:{}, cpm:{}, providers:{}, locations:{}}},".format(
                js_str(r["state_usps"]),
                js_str(r["technology_label"]),
                js_str(r.get("provider")),
                js_num(r.get("monthly_price_usd")),
                js_num(r.get("median_max_down_mbps")),
                js_num(r.get("cost_per_fcc_median_mbps_usd")),
                js_num(r.get("unique_providers")),
                js_num(r.get("locations_served")),
            )
        )
    lines.append("];")
    return "\n".join(lines)


def build_ookla_rows_block() -> str:
    df = pd.read_csv(DATA_DIR / "ookla_regional_summary.csv")
    df = df.sort_values(["state_usps", "network_type"])
    lines = ["const OOKLA_ROWS = ["]
    for _, r in df.iterrows():
        lines.append(
            "  {{state:{}, net:{}, down:{}, up:{}, lat:{}, tests:{}}},".format(
                js_str(r["state_usps"]),
                js_str(r["network_type"].capitalize()),
                js_num(round(r["median_down_mbps"], 1)),
                js_num(round(r["median_up_mbps"], 1)),
                js_num(round(r["median_latency_ms"])),
                js_num(r["total_tests"]),
            )
        )
    lines.append("];")
    return "\n".join(lines)


def replace_block(html: str, var_name: str, new_block: str) -> str:
    pattern = re.compile(rf"const {var_name} = \[.*?\n\];", re.DOTALL)
    if not pattern.search(html):
        raise SystemExit(f"Could not find `const {var_name} = [...]` block in {HTML_PATH}")
    return pattern.sub(new_block, html, count=1)


def main() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")
    html = replace_block(html, "ROWS", build_rows_block())
    html = replace_block(html, "OOKLA_ROWS", build_ookla_rows_block())
    HTML_PATH.write_text(html, encoding="utf-8")

    n_states = pd.read_csv(DATA_DIR / "cost_comparison_v1.csv")["state_usps"].nunique()
    print(f"Regenerated ROWS + OOKLA_ROWS for {n_states} states in {HTML_PATH}")
    print("Note: narrative prose (headline stats, 'N states' mentions, BEAD section) "
          "was NOT touched -- update that separately once state count stabilizes.")


if __name__ == "__main__":
    main()
