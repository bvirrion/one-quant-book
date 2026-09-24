"""Numbers gate: every numerical answer printed in the Chapter 5 text and solutions."""
import math
import pathlib
import sys
from statistics import NormalDist

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from clearing_demo import Trade, Waterfall, initial_margin, net_obligations, netting_efficiency, random_trades

W = Waterfall(120, 30, 20, 400, 400)


def test_text():
    t = [Trade("A", "B", "X", 5000, 20.0), Trade("B", "C", "X", 3000, 20.1), Trade("C", "A", "X", 4000, 19.95)]
    sh, cash = net_obligations(t)
    assert (sh["A"]["X"], sh["B"]["X"], sh["C"]["X"]) == (1000, -2000, 1000)
    assert [round(cash[m]) for m in "ABC"] == [-20200, 39700, -19500]
    assert round(sum(x.quantity * x.price for x in t)) == 240_100 and round(netting_efficiency(t) * 100) == 83
    assert round(initial_margin(1e9, 0.04, 2, 2.33) / 1e6) == 132
    assert round(initial_margin(1e9, 0.25, 2, 2.33) / 1e6) == 824
    assert 3.7 - 0.7 == pytest.approx(3.0) and 120 + 30 == 150 and 120 + 30 + 20 == 170 and sum(
        v for _, v in W.layers()) == 970


def test_exercises():
    assert 40 * 39 // 2 == 780 and 780 / 40 == 19.5                                        # 1
    t = [Trade("B", "A", "X", 2000, 50.0), Trade("C", "B", "X", 2000, 50.2), Trade("A", "C", "X", 1500, 50.1)]
    sh, cash = net_obligations(t)                                                          # 2
    assert (sh["A"]["X"], sh["B"]["X"], sh["C"]["X"]) == (-500, 0, 500)
    assert [round(cash[m]) for m in "ABC"] == [24850, 400, -25250]
    assert round(netting_efficiency(t) * 100, 1) == 90.8
    a, b = initial_margin(400e6, 0.025, 2, 2.33), initial_margin(400e6, 0.025, 1, 2.33)     # 3
    assert round(a / 1e6, 1) == 33.0 and round(b / 1e6, 1) == 23.3 and round((a - b) / 1e6, 1) == 9.7
    assert list(W.allocate(140).values()) == [120, 20, 0, 0, 0, 0]                          # 4
    assert list(W.allocate(300).values()) == [120, 30, 20, 130, 0, 0] and 130 / 25 == 5.2
    assert list(W.allocate(1000).values()) == [120, 30, 20, 400, 400, 30]
    assert round(initial_margin(600e6, 0.03, 2, 2.33) / 1e6) == 59                          # 5
    assert round(initial_margin(600e6, 0.18, 2, 2.33) / 1e6) == 356
    assert 10e6 * 0.04 == pytest.approx(400_000)                                            # 6
    assert round(netting_efficiency(random_trades(2000, 8, 1)) * 100, 1) == 96.0            # 7


def test_problem():
    n = 2.4e9
    assert round(initial_margin(n, 0.013, 2, 2.33) / 1e6, 1) == 102.8                       # 1
    z = 130e6 / (n * 0.013 * math.sqrt(2))
    assert round(z, 2) == 2.95 and round(NormalDist().cdf(z) * 100, 1) == 99.8             # 2
    assert n * 0.03 == pytest.approx(72e6)                                                  # 3
    n2 = n * 0.97
    l1 = n2 * 0.06
    assert round(l1 / 1e6, 1) == 139.7                                                      # 5
    v = n2 * 0.94
    l2 = v * 0.02
    assert round((l1 + l2) / 1e6, 1) == 183.4                                               # 6
    auction = 0.004 * v * 0.98
    total = l1 + l2 + auction
    assert round(auction / 1e6, 1) == 8.6 and round(total / 1e6, 1) == 192.0                # 7
    pw = Waterfall(130, 25, 15, 400, 400)
    assert [round(x, 1) for x in pw.allocate(total / 1e6).values()] == [130, 25, 15, 22.0, 0, 0]   # 8
    assert round((total / 1e6 - 170) / 20, 2) == 1.10                                       # 9
    fast = l1 + 0.004 * v
    assert round(fast / 1e6, 1) == 148.4 and fast < 155e6                                   # 10
    assert round(total / (0.013 * n), 1) == 6.2                                             # 11
    assert 130 + 25 + 15 + 400 + 400 == 970                                                 # 12
    f = (970e6 - 0.004 * n2) / (n2 * (1 - 0.004))
    assert round(f * 100) == 41                                                             # 13
    assert round(3 * 0.013 * math.sqrt(3) * n / 1e6) == 162                                 # 14
