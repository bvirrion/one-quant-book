"""Numbers gate: every numerical answer printed in the Chapter 26 text and solutions."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from zero_day import simulate_with_hedgers, straddle_price

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/gex"))
from firm_gex import YEAR_MINUTES, Holding, delta, gamma, gamma_shares_per_pct, hedge_trade


def cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def test_text():
    assert round(straddle_price(100.0, 0.16, 1 / 252), 2) == 0.80 and round(2 * (1 - cdf(0.8)), 2) == 0.42
    assert round(gamma(100.0, 100.0, 21 / 252, 0.16) * 100 * 0.01, 2) == 0.09
    assert gamma(100.0, 100.0, 60 / YEAR_MINUTES, 0.16) * 100 * 0.01 > 1.0 > gamma(101.0, 100.0, 60 / YEAR_MINUTES, 0.16) * 101 * 0.01 * 20
    assert round(simulate_with_hedgers(4000, 78, 0.001, -0.3, 26), 2) == 0.77
    assert round(simulate_with_hedgers(4000, 78, 0.001, 0.3, 26), 2) == 1.42


def test_exercises():
    assert round(0.8 * 0.16 / math.sqrt(252) * 100, 2) == 0.81 and round(0.8 * 0.32 / math.sqrt(252) * 100, 2) == 1.61
    t = 1 / 252
    assert round(gamma(100.0, 100.0, t, 0.16), 3) == 0.396 and round(delta(100.0, 100.0, t, 0.16, "C"), 2) == 0.50
    book = [Holding(100.0, "C", t, 0.16, 500)]
    assert round(gamma_shares_per_pct(book, 100.0)) == 19_790 and 0.50 * 500 * 100 == 25_000
    assert round(delta(101.0, 100.0, t, 0.16, "C"), 2) == 0.84 and round(hedge_trade(book, 100.0, 101.0)) == -16_873
    assert round(math.sqrt(21), 1) == 4.6 and round(math.sqrt(390 / 15), 1) == 5.1
    assert 2.3e6 * 100 * 6000 == pytest.approx(1.38e12)
    assert round(1 / (1 - 0.3), 2) == 1.43 and round(1 / (1 + 0.3), 2) == 0.77


def test_problem():
    s, v = 600.0, 0.16
    assert 20_000 * 100 == 2_000_000 and 2_000_000 * 600 == 1.2e9
    t60 = 60 / YEAR_MINUTES
    assert round(v * math.sqrt(t60) * 100, 2) == 0.40 and round(gamma(s, 600.0, t60, v), 3) == 0.168
    book = [Holding(600.0, "C", t60, v, -20_000)]
    assert round(gamma_shares_per_pct(book, s) / 1e6, 2) == -2.02
    a, b = hedge_trade(book, s, s * 1.0025), hedge_trade(book, s, s * 1.01)
    assert round(a, -3) == 472_000 and round(b, -3) == 987_000
    base = delta(s, 600.0, t60, v, "C")
    assert round(base + a / 2e6, 2) == 0.74 and round(base + b / 2e6, 2) == 0.99
    open_, late = ([Holding(600.0, "C", m / YEAR_MINUTES, v, -20_000)] for m in (390, 15))
    g390, g15 = gamma_shares_per_pct(open_, s), gamma_shares_per_pct(late, s)
    assert round(g390, -3) == -792_000 and round(g15 / 1e6, 2) == -4.04
    assert round(gamma_shares_per_pct(book, s) / g390, 2) == round(math.sqrt(390 / 60), 2) == 2.55
    assert round(g15 / gamma_shares_per_pct(book, s), 1) == 2.0
    assert round(2.018e6 / (60e6 / 6.5) * 100) == 22
