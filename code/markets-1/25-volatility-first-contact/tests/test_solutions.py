"""Numbers gate: every numerical answer printed in the Chapter 25 text and solutions."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from vol_first import chain, index_style, read_chain, true_forward

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/parity"))
from firm_parity import implied_forward, implied_vol, price

T, R = 0.25, 0.04
FIVE = chain([90.0, 95.0, 100.0, 105.0, 110.0])


def test_text():
    assert FIVE == [(90.0, 11.22, 1.12), (95.0, 7.26, 2.11), (100.0, 4.06, 3.87), (105.0, 1.88, 6.63), (110.0, 0.68, 10.38)]
    assert round(true_forward(), 2) == 100.20
    _, f, div, vols = read_chain(chain([float(k) for k in range(80, 121, 5)]))
    assert round(div, 2) == 0.80 and [round(v * 100, 1) for v in vols[2:7]] == [23.8, 21.8, 20.1, 18.7, 17.6]
    assert round((vols[2] - vols[6]) * 100, 1) == 6.2
    assert round(index_style([float(k) for k in range(50, 181)]), 1) == 23.0
    assert round((1 / 60**2) / (1 / 140**2), 1) == 5.4 and round(15.6 - 14.0, 1) == 1.6 and round(1 - 25.0 / 37.0, 2) == 0.32


def test_exercises():
    f = implied_forward(4.06, 3.87, 100.0, T, R)
    assert round(f, 2) == 100.19 and round(100 - math.exp(-R * T) * f, 2) == 0.81
    assert round((4.06 + 3.87) / 2 / (0.4 * 100.2 * math.exp(-R * T) * 0.5) * 100, 1) == 20.0
    assert (19.25 - 16.70) * 1000 * 40 == pytest.approx(102_000) and round(2.55 / 0.05) == 51
    assert round(math.exp(-R * T) * (100.20 - 90), 2) == 10.10 > 10.05
    with pytest.raises(ValueError):
        implied_vol(10.05, 100.20, 90.0, T, R, "C")
    carry = 100 - math.exp(-R * T) * 98.10
    assert round(carry, 2) == 2.88 and round(carry / T, 1) == 11.5
    r = [0.4, -1.1, 0.7, -2.0, 1.5]
    assert round(math.sqrt(sum(x * x for x in r) / 5) * math.sqrt(252), 1) == 20.2


def test_problem():
    fw = [implied_forward(c, p, k, T, R) for k, c, p in FIVE]
    assert [round(x, 2) for x in fw] == [100.20, 100.20, 100.19, 100.20, 100.20] and round(sum(fw) / 5, 2) == 100.20
    assert round(100 - math.exp(-R * T) * sum(fw) / 5, 2) == 0.80
    assert round((23.8 - 17.6) / 2, 1) == 3.1
    k = 100 * math.exp(-R * T)
    assert round(4.03 - 3.90 - 100.01 + 0.797 + k, 2) == -0.08
    assert round(3.84 - 4.09 + 99.99 - 0.797 - 0.05 - k, 2) == -0.11
    assert round(4.60 - 3.90 - 100.01 + 0.797 + k, 2) == 0.49
    f2 = (97 - 0.797) * math.exp(R * T)
    assert round(f2, 2) == 97.17 and round(implied_vol(2.74, f2, 100.0, T, R, "C") * 100, 1) == 20.5
    wrong = implied_vol(11.22, 100.0, 90.0, T, R, "C")
    right = implied_vol(11.22, 100.20, 90.0, T, R, "C")
    assert round(right * 100, 1) == 23.8 and round(wrong * 100, 1) == 25.1
    assert price(100.2, 100.0, T, R, 0.21, "C") - price(100.2, 100.0, T, R, 0.20, "C") == pytest.approx(0.197, abs=0.002)
