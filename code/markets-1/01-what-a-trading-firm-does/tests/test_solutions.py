"""Numbers gate: every numerical answer printed in the Chapter 1 solutions."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from whoearns import break_even_volume, simulate_day


def phi(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def test_exercises():
    assert 0.04 / 25.00 * 1e4 == pytest.approx(16.0)                    # exo 1
    assert 300 * 0.02 == pytest.approx(6.0)
    assert 2e6 * 0.001 == pytest.approx(2000) and 2000 * 252 == 504_000  # exo 2
    gross = 0.12 * 500e6                                                 # exo 4
    mgmt = 0.02 * 500e6
    perf = 0.20 * (gross - mgmt)
    assert (mgmt, perf) == (10e6, 10e6)
    assert (gross - mgmt - perf) / 500e6 == pytest.approx(0.08)
    assert (mgmt + perf) / gross == pytest.approx(1 / 3)
    c = 1.00 - 0.14 * 5 + 0.20 - 0.05                                    # exo 5, cents
    assert c == pytest.approx(0.45)
    assert break_even_volume(90_000, c / 100) == pytest.approx(20e6)
    bp = 467.8e6 / 1545e9 * 1e4                                          # exo 6
    assert round(bp, 2) == 3.03
    assert round(467.8 / 609, 2) == 0.77
    assert round(50 * bp / 1e4 * 100, 1) == 1.5                          # cents on EUR 50
    d = simulate_day(7)                                                  # exo 7
    assert round(d["mm_spread_earned"]) == 20000
    assert round(d["mm_position_pnl"]) == -9173
    assert round(d["mm_net"]) == 14427


def test_problem():
    half = 1.0
    assert half / 4000 * 1e4 == pytest.approx(2.5)                        # 1
    adverse = 0.12 * 5                                                    # 2
    c = half - adverse + 0.20 - 0.02                                      # 3
    assert c == pytest.approx(0.58)
    daily = 6e6 * c / 100                                                 # 4
    assert daily == pytest.approx(34_800)
    assert daily * 252 == pytest.approx(8_769_600)                        # 5
    cost = 14 * 350_000 + 2.1e6 + 0.56e6                                  # 6
    assert cost == pytest.approx(7.56e6) and cost / 252 == pytest.approx(30_000)
    assert daily - 30_000 == pytest.approx(4_800)                         # 7
    assert (daily - 30_000) * 252 == pytest.approx(1_209_600)
    assert round(30_000 / daily * 100, 1) == 86.2                         # 8
    assert round(break_even_volume(30_000, c / 100)) == 5_172_414         # 9
    c2 = half - 0.16 * 5 + 0.20 - 0.02                                    # 10
    assert c2 == pytest.approx(0.38)
    assert round(break_even_volume(30_000, c2 / 100)) == 7_894_737
    assert 6e6 * c2 / 100 - 30_000 == pytest.approx(-7_200)               # 11
    assert half + (c - c2) == pytest.approx(1.2)                          # 12
    assert round(break_even_volume(30_000, 0.53 / 100)) == 5_660_377      # 13
    z = 4_800 / 22_000
    assert round(phi(-z), 2) == 0.41                                      # 14
    sharpe = z * math.sqrt(252)
    assert round(sharpe, 2) == 3.46                                       # 15
    assert round(phi(-sharpe) * 1e4, 1) == 2.7                            # 16: 0.027 %
    assert round(1_209_600 / 5e6 * 100, 1) == 24.2                        # 17
    assert (2 * daily - 30_000) / (daily - 30_000) == pytest.approx(8.25)  # 18


def test_interview():
    assert round((49.97 - 49.99) * 100, 2) == -2.0                        # iq 3
    assert 2e9 * 1e-4 * 252 == pytest.approx(50.4e6)                      # iq 4
