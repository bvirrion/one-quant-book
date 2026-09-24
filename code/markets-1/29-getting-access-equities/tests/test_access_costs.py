import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from access_costs import cost_table, monthly_rebate


def test_three_venues_three_signs():
    t = {name: (p, a) for name, p, a in cost_table(9e6)}
    assert t["maker-taker exchange"][0] == pytest.approx(-0.0017) and t["maker-taker exchange"][1] == pytest.approx(0.0033)
    assert t["inverted exchange"][0] > 0 > t["inverted exchange"][1]
    assert t["flat-fee venue"][0] == t["flat-fee venue"][1] == pytest.approx(0.0006)


def test_monthly_rebate_jumps_at_a_threshold():
    assert monthly_rebate(24.0e6) - monthly_rebate(23.9e6) == pytest.approx(7_400 * 21)
