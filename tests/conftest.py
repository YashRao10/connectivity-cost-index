from pathlib import Path

import pandas as pd
import pytest

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

VALID_TECH_LABELS = {
    "DSL (Copper)",
    "Cable",
    "Fiber",
    "GSO Satellite",
    "LEO Satellite",
    "Unlicensed Fixed Wireless",
    "Licensed Fixed Wireless",
    "LBR Fixed Wireless",
    "Other",
}

VALID_STATE_CODES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL",
    "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT",
    "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI",
    "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
}


@pytest.fixture(scope="session")
def fcc_summary() -> pd.DataFrame:
    path = DATA_DIR / "fcc_technology_summary.csv"
    if not path.exists():
        pytest.skip(f"{path} not present (run scripts/load_fcc_broadband.py first)")
    return pd.read_csv(path)


@pytest.fixture(scope="session")
def cost_comparison() -> pd.DataFrame:
    path = DATA_DIR / "cost_comparison_v1.csv"
    if not path.exists():
        pytest.skip(f"{path} not present (run scripts/build_cost_comparison.py first)")
    return pd.read_csv(path)


@pytest.fixture(scope="session")
def pricing_snapshot() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "pricing_snapshot.csv")


@pytest.fixture(scope="session")
def ookla_summary() -> pd.DataFrame:
    path = DATA_DIR / "ookla_regional_summary.csv"
    if not path.exists():
        pytest.skip(f"{path} not present (run scripts/load_ookla_regional.py first)")
    return pd.read_csv(path)


@pytest.fixture(scope="session")
def bead_comparison() -> pd.DataFrame:
    path = DATA_DIR / "bead_allocation_v1.csv"
    if not path.exists():
        pytest.skip(f"{path} not present (run scripts/build_bead_comparison.py first)")
    return pd.read_csv(path)
