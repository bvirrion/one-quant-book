"""Numbers gate: every numerical answer printed in the Chapter 8 text and solutions."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from corpact import CapIndex, dividend_factor, terp


def test_text():
    assert round(1208.88 / 10, 2) == 120.89
    assert terp(10.0, 4, 1, 6.0) == pytest.approx(9.2) and 4 * 9.2 + 3.2 == pytest.approx(40.0)
    assert round((99 / 100 - 1) * 100, 3) == -1.0 and round((101 / 102 - 1) * 100, 3) == -0.980
    assert round(0.01 * 2 / 102 * 1e4) == 2


def test_exercises():
    assert 800e6 * 65 == 52e9 and 800e6 * 65 * 0.7 == pytest.approx(36.4e9)
    assert 240 / 1.5 == 160 and 500 * 1.5 == 750
    assert dividend_factor(80, 1.2) == pytest.approx(0.985) and round(76 * 0.985, 2) == 74.86
    t = terp(25, 7, 2, 16)
    assert t == 23 and t / 25 == 0.92 and 700 * t + 200 * (t - 16) == 17_500
    assert (50 + 120 + 330) / 0.5 == 1000 and (50 + 120 + 110) / 1000 == 0.28
    assert [round(x / 280 * 100, 1) for x in (50, 120, 110)] == [17.9, 42.9, 39.3]
    a, tr = 48.45 / 47.5 - 1, (48.45 + 2.5) / 50 - 1
    assert a == pytest.approx(0.02) and tr == pytest.approx(0.019) and a - tr == pytest.approx(0.02 * 2.5 / 50)
    ix = CapIndex({"X": 100e6, "Y": 50e6}, {"X": 1.0, "Y": 1.0}, 1.0)
    px = {"X": 20.0, "Y": 60.0}
    ix.divisor = ix.market_value(px) / 1000
    assert ix.divisor == 5e6

    def buyback(i):
        i.shares["Y"] = 40e6
    ix.rebase(px, buyback)
    assert ix.divisor == pytest.approx(4.4e6) and round(ix.level({"X": 22.0, "Y": 57.0}), 1) == 1018.2


def test_problem():
    sh = {"P": 500e6, "Q": 200e6, "R": 1000e6, "S": 400e6}
    fl = {"P": 1.0, "Q": 0.8, "R": 0.5, "S": 0.9}
    px = {"P": 40.0, "Q": 150.0, "R": 12.0, "S": 75.0}
    caps = {s: px[s] * sh[s] * fl[s] for s in sh}
    m = sum(caps.values())
    assert [caps[s] / 1e9 for s in "PQRS"] == [20, 24, 6, 27] and m == 77e9
    d = m / 2500
    assert d == 30.8e6
    assert [round(caps[s] / m * 100, 1) for s in "PQRS"] == [26.0, 31.2, 7.8, 35.1]
    assert round(0.01 * caps["Q"] / d, 1) == 7.8
    m2 = m - 500e6 * 1.0
    assert round(m2 / d, 2) == 2483.77 and round(500e6 / d, 2) == 16.23
    t = terp(12, 4, 1, 8)
    assert t == pytest.approx(11.2)
    cap_r = t * 1250e6 * 0.5
    m3 = m2 - caps["R"] + cap_r
    d3 = d * m3 / m2
    assert cap_r == pytest.approx(7e9) and m3 == pytest.approx(77.5e9) and round(d3 / 1e6, 3) == 31.203
    cap_t = 30 * 600e6 * 0.75
    m4 = m3 - caps["S"] + cap_t
    d4 = d3 * m4 / m3
    assert m4 == pytest.approx(64e9) and round(d4 / 1e6, 3) == 25.767
    w = {"P": 19.5e9 / m4, "Q": 24e9 / m4, "R": cap_r / m4, "T": cap_t / m4}
    assert [round(v * 100, 1) for v in w.values()] == [30.5, 37.5, 10.9, 21.1]
    assert round(2e9 * caps["S"] / m3 / 1e6) == 697 and round(2e9 * cap_t / m4 / 1e6) == 422
    buy = 2e9 * cap_t / m4
    assert round(buy / 150e6, 1) == 2.8
    cost = 0.7 * 0.02 * (buy / 150e6) ** 0.5
    assert round(cost * 100, 1) == 2.3 and round(cost * buy / 1e6, 1) == 9.9
