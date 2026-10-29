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
            "  {{state:{}, tech:{}, provider:{}, price:{}, mbps:{}, up:{}, cpm:{}, providers:{}, locations:{}, basis:{}}},".format(
                js_str(r["state_usps"]),
                js_str(r["technology_label"]),
                js_str(r.get("provider")),
                js_num(r.get("monthly_price_usd")),
                js_num(r.get("median_max_down_mbps")),
                js_num(r.get("median_max_up_mbps")),
                js_num(r.get("cost_per_fcc_median_mbps_usd")),
                js_num(r.get("unique_providers")),
                js_num(r.get("locations_served")),
                js_str(r.get("price_basis")),
            )
        )
    lines.append("];")
    return "\n".join(lines)


def build_timeseries_rows_block() -> str:
    """One row per state/network: Q1-Q3 medians, Q1->Q2 change (pct12) and the
    latest quarter-over-quarter change (pct, Q2->Q3), sorted by the latest change."""
    df = pd.read_csv(DATA_DIR / "ookla_timeseries.csv")
    wide = df.pivot_table(
        index=["state_usps", "network_type"], columns="quarter", values="median_down_mbps"
    )
    wide.columns = [f"q{int(c)}" for c in wide.columns]
    wide = wide.reset_index()
    wide["pct12"] = ((wide["q2"] - wide["q1"]) / wide["q1"] * 100).round(1)
    wide["pct"] = ((wide["q3"] - wide["q2"]) / wide["q2"] * 100).round(1)
    wide = wide.dropna(subset=["pct", "pct12"]).sort_values("pct")
    lines = ["const TIMESERIES_ROWS = ["]
    for _, r in wide.iterrows():
        lines.append(
            "  {{state:{}, net:{}, q1:{}, q2:{}, q3:{}, pct12:{}, pct:{}}},".format(
                js_str(r["state_usps"]),
                js_str(r["network_type"].capitalize()),
                js_num(round(r["q1"], 1)),
                js_num(round(r["q2"], 1)),
                js_num(round(r["q3"], 1)),
                js_num(r["pct12"]),
                js_num(r["pct"]),
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


def build_income_rows_block() -> str:
    df = pd.read_csv(DATA_DIR / "state_median_income.csv").sort_values("state_usps")
    lines = ["const INCOME_ROWS = ["]
    for _, r in df.iterrows():
        lines.append(
            "  {{state:{}, income:{}, year:{}}},".format(
                js_str(r["state_usps"]),
                js_num(r["median_household_income_usd"]),
                js_num(r["year"]),
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
    html = replace_block(html, "TIMESERIES_ROWS", build_timeseries_rows_block())
    html = replace_block(html, "INCOME_ROWS", build_income_rows_block())
    HTML_PATH.write_text(html, encoding="utf-8")

    n_states = pd.read_csv(DATA_DIR / "cost_comparison_v1.csv")["state_usps"].nunique()
    n_ts_states = pd.read_csv(DATA_DIR / "ookla_timeseries.csv")["state_usps"].nunique()
    print(f"Regenerated ROWS + OOKLA_ROWS for {n_states} states, "
          f"TIMESERIES_ROWS for {n_ts_states} states, in {HTML_PATH}")
    print("Note: narrative prose (headline stats, 'N states' mentions, BEAD section) "
          "was NOT touched -- update that separately once state count stabilizes.")


if __name__ == "__main__":
    main()
