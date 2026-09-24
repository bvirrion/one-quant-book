"""Numbers gate: every numerical answer printed in the Chapter 6 text and solutions."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from financing_demo import (
    Book,
    annual_cost_cash,
    annual_cost_swap,
    forced_sale,
    margin_call_price,
    return_on_equity,
    spiral,
)


def test_text():
    assert return_on_equity(0.10, 5, 0.04) == pytest.approx(0.34) and return_on_equity(-0.10, 5, 0.04) == pytest.approx(-0.66)
    assert forced_sale(5e9, 5, 0.04) == pytest.approx(0.8e9)
    assert (-1 + 7 * 0.04) / 8 == pytest.approx(-0.09)
    assert margin_call_price(1, 0.5, 0.25) == pytest.approx(2 / 3)
    assert round(margin_call_price(1, 0.15, 0.10), 3) == 0.944
    assert round(1 / 0.075, 1) == 13.3
    b = Book(300e6, 200e6, 100e6)
    assert annual_cost_cash(b, 0.04, 0.005, 0.003, 0.003) == pytest.approx(2.2e6)
    assert annual_cost_swap(b, 0.04, 0.005, 0.003, 0.003) == pytest.approx(2.7e6)
    assert round(spiral(8, 0.05, 0.10)[-1] * 100, 1) == 10.2


def test_exercises():
    assert 1500 / 250 == 6 and round(250 / 1500 * 100, 1) == 16.7 and return_on_equity(0.06, 6, 0.04) == pytest.approx(0.16)
    assert 50e6 * 0.97 == pytest.approx(48.5e6) and round(48.5e6 * 0.042 * 7 / 360) == 39608      # 2
    assert 20e6 * (0.04 - 0.06) == pytest.approx(-400_000)                                       # 3
    assert round(margin_call_price(80, 0.40, 0.30), 2) == 68.57 and 0.4 * 60 - (60 - 48) == 12   # 4
    a, e = 3e9 * 0.95, 3e9 / 6 - 0.05 * 3e9                                                      # 5
    assert round(a / e, 2) == 8.14 and forced_sale(3e9, 6, 0.05) == pytest.approx(0.75e9)
    assert a - 4 * e == pytest.approx(1.45e9)
    assert 1 - 2.5 / 4 == 0.375 and 0.12 * 40 == pytest.approx(4.8) and 0.12 * 25 == pytest.approx(3.0)   # 6

    def wiped(imp):
        s = spiral(8, 0.05, imp)
        return len(s) < 12 or s[-1] >= 0.125
    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if wiped(mid) else (mid, hi)
    assert round(hi, 3) == 0.129 and round(1 / 7, 3) == 0.143                                    # 7


def test_problem():
    e, a = 4e9, 28e9
    assert a / e == 7 and round(e / a * 100, 1) == 14.3
    n0 = a / 1.6
    m = 0.1 * n0
    assert n0 == pytest.approx(17.5e9) and m == pytest.approx(1.75e9) and m / a == pytest.approx(0.0625)
    assert e - m == pytest.approx(2.25e9)
    fin = a * 0.0445
    net = fin - e * 0.04
    assert fin == pytest.approx(1.246e9) and net == pytest.approx(1.086e9)
    assert round(net / e * 100, 1) == 27.2 and round(net / a * 100, 2) == 3.88
    l1 = 0.10 * a
    assert l1 == pytest.approx(2.8e9) and (a - l1) / (e - l1) == pytest.approx(21)
    assert 2.25e9 / 5 == pytest.approx(0.45e9) and l1 / 5 - 0.45e9 == pytest.approx(0.11e9)
    a1 = a - l1
    l2 = 0.08 * a1
    assert l2 == pytest.approx(2.016e9) and e - l1 - l2 == pytest.approx(-0.816e9)
    d = (a1 - l2) / 5
    assert round(d / 1e9, 2) == 4.64
    owed = l1 / 5 + l2 / 5
    held = m / 5 + 0.45e9
    assert round(owed / 1e6) == 963 and held == pytest.approx(0.8e9)
    assert round((owed - held + 0.12 * d) / 1e6) == 720
    assert round((owed - held + 0.03 * d) / 1e6) == 302
    assert 0.10 * a == pytest.approx(2.8e9)
