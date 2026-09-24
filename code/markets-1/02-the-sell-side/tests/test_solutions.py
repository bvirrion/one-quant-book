"""Numbers gate: every numerical answer printed in the Chapter 2 solutions."""
import math
import pathlib
import sys
from statistics import NormalDist

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from blockbid import Z95, Block, breakeven_discount, impact_cost, risk_std, unwind_days


def test_text_numbers():
    b = Block(2e6, 1e7, 0.02)
    assert round(impact_cost(b) * 100, 2) == 0.63
    assert round(Z95 * risk_std(b) * 100, 2) == 2.69
    assert round(breakeven_discount(b) * 100, 2) == 3.31
    assert round(breakeven_discount(b) * 50, 2) == 1.66
    fast = Block(2e6, 1e7, 0.02, participation=0.25)
    assert round(breakeven_discount(fast) * 100, 1) == 2.3
    assert round((1 - math.sqrt(0.5)) * 100) == 29
    assert round(60 / (2000 * 0.12) * 100) == 25 and round(25 / (400 * 0.12) * 100) == 52


def test_exercises():
    assert 30e6 * 0.015 * math.sqrt(3 / 3) == pytest.approx(450_000)           # 1
    b = Block(5e5, 5e6, 0.015)                                                 # 2
    assert unwind_days(b) == pytest.approx(1.0) and round(impact_cost(b) * 100, 2) == 0.33
    assert 800e6 * 0.035 == pytest.approx(28e6)                                # 3
    assert 800e6 / 40 * 6 == pytest.approx(120e6)
    b = Block(3e6, 6e6, 0.025)                                                 # 4
    assert round(breakeven_discount(b) * 100, 2) == 6.55
    assert round(breakeven_discount(b) * 20, 2) == 1.31
    fin, inter, fees, tot = 4.251 + 7.195, 10.271 + 9.340, 9.339, 41.453       # 6
    assert [round(x / tot * 100) for x in (fin, inter, fees)] == [28, 47, 23]
    assert round(fin / (14.522 + 16.535) * 100) == 37
    b = Block(2e6, 1e7, 0.02)                                                  # 7
    hedged = impact_cost(b) + Z95 * risk_std(Block(2e6, 1e7, 0.02 * math.sqrt(0.6)))
    assert round(hedged * 100, 2) == 2.71
    assert round((breakeven_discount(b) - hedged) * 1e4) == 61


def test_problem():
    n = 4e6 * 25
    b = Block(4e6, 8e6, 0.018)
    assert n == 100e6 and unwind_days(b) == pytest.approx(5.0)                 # 1-2
    assert round(impact_cost(b) * 100, 2) == 0.89 and round(impact_cost(b) * n, -3) == 891_000
    assert round(risk_std(b) * 100, 2) == 2.32 and round(risk_std(b) * n, -3) == 2_324_000
    d = breakeven_discount(b)
    assert round(d * 100, 2) == 4.71 and math.floor(25 * (1 - d) * 100) / 100 == 23.82
    b2 = Block(4e6, 8e6, 0.018, participation=0.2)                             # 6
    assert unwind_days(b2) == pytest.approx(2.5) and round(breakeven_discount(b2) * 100, 2) == 3.59
    rs = risk_std(Block(4e6, 8e6, 0.018 * math.sqrt(0.5), participation=0.2))  # 7
    d7 = impact_cost(b2) + Z95 * rs
    assert round(rs * 100, 2) == 1.16 and round(d7 * 100, 2) == 2.80
    assert round((d7 - impact_cost(b2)) * n, -4) == 1_910_000                  # 8
    assert round((impact_cost(b2) + rs) * 100, 2) == 2.05                      # 9
    assert round((1 - NormalDist().cdf(1)) * 100) == 16
    assert round((impact_cost(b2) + 0.01 / 25) * 100, 2) == 0.93               # 10
    assert round(risk_std(b2) * 100, 2) == 1.64
    assert round((d7 - impact_cost(b2) - 0.01 / 25) * 100, 2) == 1.87          # 11
    assert round(150e6 * 0.12 * 0.10 * 3 / 252) == 21_429                      # 14
    assert -0.03 * n + 0.01 * n == pytest.approx(-2e6)                         # 17
    assert round((d7 + 0.004) * 100, 2) == 3.20 and round((d7 + 0.004) * 2500) == 80  # 19


def test_interview():
    assert math.sqrt(1 / 3) == pytest.approx(0.577, abs=1e-3)                  # iq 2
    assert 4 * math.sqrt(1) / math.sqrt(4) == pytest.approx(2.0)               # iq 5
