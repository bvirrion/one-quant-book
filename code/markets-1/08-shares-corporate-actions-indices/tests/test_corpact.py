import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from corpact import CapIndex, back_adjust, dividend_factor, reinvest_factor, rights_factor, split_factor, terp


def test_dividend_adjustment_is_exact_only_at_the_theoretical_ex_price():
    # cum price 102, dividend 2. If the stock opens ex at exactly 100 and closes there, the
    # adjusted return is 0 %, as the total return (100 + 2) / 102 - 1 is.
    exact = back_adjust(np.array([102.0, 100.0]), {1: dividend_factor(102.0, 2.0)})
    assert exact[1] / exact[0] == pytest.approx(1.0)
    # If it closes ex at 99, the adjusted return is 99/100 while the total return is 101/102:
    adj = back_adjust(np.array([102.0, 99.0]), {1: dividend_factor(102.0, 2.0)})
    assert adj[1] / adj[0] == pytest.approx(0.99)
    assert (99.0 + 2.0) / 102.0 == pytest.approx(0.990196, abs=1e-6)
    # the reinvestment factor P_ex / (P_ex + D) is exact in every case
    assert back_adjust(np.array([102.0, 99.0]), {1: reinvest_factor(99.0, 2.0)})[0] == pytest.approx(102 * 99 / 101)


def test_split_leaves_the_adjusted_series_continuous():
    raw = np.array([1200.0, 1208.88, 120.888, 121.0])
    adj = back_adjust(raw, {2: split_factor(10)})
    assert adj[1] == pytest.approx(120.888) and adj[2] / adj[1] == pytest.approx(1.0)


def test_terp():
    assert terp(10.0, 4, 1, 6.0) == pytest.approx(9.2)
    assert rights_factor(10.0, 4, 1, 6.0) == pytest.approx(0.92)


def test_rebase_keeps_the_level():
    px = {"A": 10.0, "B": 20.0}
    ix = CapIndex({"A": 100.0, "B": 50.0}, {"A": 1.0, "B": 1.0}, divisor=2.0)
    before = ix.level(px)

    def add(i):
        i.shares["C"], i.floats["C"] = 10.0, 0.5
    ix.rebase(dict(px, C=40.0), add)
    assert ix.level(dict(px, C=40.0)) == pytest.approx(before)
