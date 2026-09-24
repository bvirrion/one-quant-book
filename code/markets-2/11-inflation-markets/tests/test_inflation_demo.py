"""Chapter 11 of Book 2: the data and the demo behave as the text says."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from inflation_demo import accruals, august_2022, load_cpi, load_tips10, seasonality


def test_data_is_complete_and_consistent():
    cpi = load_cpi()
    assert (2010, 1) in cpi and (2026, 8) in cpi and len(cpi) == 199
    assert (2025, 10) not in cpi                                   # not collected in the 2025 shutdown
    rows = load_tips10()
    assert all(abs(n - r - b) < 0.03 for _, n, r, b in rows)     # the breakeven is the difference


def test_accrual_equals_lagged_index_change():
    cpi = load_cpi()
    acc = dict(accruals())
    assert abs(acc["2022-08"] - 100 * (cpi[(2022, 6)] / cpi[(2022, 5)] - 1)) < 1e-12


def test_seasonal_pattern_is_stable():
    a, b = seasonality(2010, 2019), seasonality(2010, 2024)
    assert seasonality(2010, 2025) == b                           # 2025 is incomplete, so skipped
    assert max(a, key=a.get) == max(b, key=b.get) == 3
    assert min(a, key=a.get) == min(b, key=b.get) == 11


def test_carry_decomposition():
    a = august_2022()
    cross = a["carry"] - (a["accrual_income"] + a["real_pull"] - a["repo_cost"])
    assert 0 < cross < 200
