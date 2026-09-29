"""Numbers gate: every numerical answer printed in Book 18, chapter 18 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from iv_rates import (
    cip_forward,
    convexity,
    curve,
    dv01,
    forward_rate,
    modified_duration,
    price,
    roll_down_return,
)


def test_q1_q2_q3():
    assert round(-7 * 0.0025, 4) == -0.0175
    assert round(dv01(10e6, 98, 6.5)) == 6370
    assert round(100 * forward_rate(0.03, 1, 0.04, 2), 2) == 5.01


def test_q5_hedge():
    assert round(10 * 850 / 460, 2) == 18.48


def test_q6_duration_convexity():
    assert round(price(0.04, 0.04, 10), 6) == 100
    d, c = modified_duration(0.04, 0.04, 10), convexity(0.04, 0.04, 10)
    assert round(d, 2) == 8.11 and round(c, 1) == 80.8
    approx = -d * 0.01 + 0.5 * c * 0.0001
    exact = price(0.04, 0.05, 10) / 100 - 1
    assert round(100 * approx, 2) == -7.71 and round(100 * exact, 2) == -7.72
    assert round(100 * -d * 0.01, 2) == -8.11


def test_q7_rolldown():
    assert round(100 * curve(5), 2) == 3.69 and round(100 * curve(4), 2) == 3.59
    total, roll, carry = roll_down_return(curve(5), 5, 0.03)
    assert round(100 * roll, 2) == 0.33 and round(100 * carry, 2) == 0.69 and round(100 * total, 2) == 1.02


def test_q8_negative_carry():
    assert round((0.04 - 0.045) * 100e6 / 12) == -41_667


def test_q9_cip():
    assert round(cip_forward(1.10, 0.04, 0.02), 4) == 1.1216


def test_q11_recap_numbers():
    assert 12 - 5 == 7  # 2s10s flattened by 7 bp


def test_q12_barbell():
    d10 = modified_duration(0.04, 0.04, 10)
    d2, d30 = modified_duration(0.04, 0.04, 2), modified_duration(0.04, 0.04, 30)
    w = (d10 - d2) / (d30 - d2)
    cb = (1 - w) * convexity(0.04, 0.04, 2) + w * convexity(0.04, 0.04, 30)
    assert round(w, 3) == 0.404 and round(cb) == 173 and round(convexity(0.04, 0.04, 10)) == 81
    # on a parallel 100 bp move either way the barbell does better (convexity)
    for dy in (-0.01, 0.01):
        barbell = (1 - w) * (price(0.04, 0.04 + dy, 2) / 100 - 1) + w * (price(0.04, 0.04 + dy, 30) / 100 - 1)
        bullet = price(0.04, 0.04 + dy, 10) / 100 - 1
        assert barbell > bullet
    assert math.isclose((1 - w) * d2 + w * d30, d10)


def test_extra_numbers():
    assert round((1 - 1.04**-10) / 0.04, 2) == round(modified_duration(0.04, 0.04, 10), 2) == 8.11
    total, _, _ = roll_down_return(curve(5), 5, 0.03)
    d4 = modified_duration(curve(5), curve(4), 4)
    assert round(d4, 1) == 3.7 and round(10_000 * total / d4) == 28
    assert round(41_666.67 / 100e6 * 100, 3) == 0.042
    assert round(100 * curve(0.25), 1) == 2.9 and round(100 * curve(30), 1) == 4.1


def test_worked_answers():
    p = 100 / 1.04**10
    md = 10 / 1.04
    assert round(1.04**10, 3) == 1.480 and round(10 * math.log(1.04), 3) == 0.392
    assert round(p, 2) == 67.56 and round(md, 2) == 9.62 and round(p * md * 1e-4, 3) == 0.065
    assert round(p - 100 / 1.0401**10, 4) == 0.0649
    assert round(4.2 - 1.9, 1) == 2.3 and round(100 * (1.042 / 1.019 - 1), 2) == 2.26
