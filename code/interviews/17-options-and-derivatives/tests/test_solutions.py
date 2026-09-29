"""Numbers gate: every numerical answer printed in Book 18, chapter 17 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from iv_options import call, digital, digital_vega, fair_variance_smile, gamma, parity_gap, put, vega


def smile(k):
    return max(0.05, 0.2 - 0.1 * math.log(k / 100))


def test_q1_parity():
    assert round(100 * math.exp(-0.01), 3) == 99.005
    assert round(parity_gap(7.10, 2.40, 104, 100, 0.04, 0.25), 3) == -0.295


def test_q2_lower_bound():
    assert round(50 - 40 * math.exp(-0.01), 2) == 10.40


def test_q4_atm():
    assert round(call(100, 100, 0.2, 0.25), 2) == 3.99 and 0.4 * 100 * 0.2 * 0.5 == 4.0
    assert round(1 / math.sqrt(2 * math.pi), 4) == 0.3989


def test_q5_butterfly():
    assert 12 - 2 * 7 + 1.5 == -0.5


def test_q6_early_exercise():
    assert round(put(10, 100, 0.3, 1, 0.05), 2) == 85.12
    assert round(100 * math.exp(-0.05) - 10, 2) == 85.12 and 100 - 10 == 90


def test_q7_gamma():
    g_week, g_year = gamma(100, 100, 0.2, 1 / 52), gamma(100, 100, 0.2, 1)
    assert round(g_week, 3) == 0.144 and round(g_year, 4) == 0.0198
    assert round(g_week / g_year, 1) == 7.2 and round(math.sqrt(52), 1) == 7.2


def test_q8_hedged_pnl():
    gamma_pnl = 0.5 * 50 * 2**2
    theta = -0.5 * 50 * 100**2 * 0.2**2 / 252
    assert gamma_pnl == 100 and round(theta, 1) == -39.7 and round(gamma_pnl + theta, 1) == 60.3
    assert round(100 * 0.2 / math.sqrt(252), 2) == 1.26


def test_q9_digital_vega():
    assert digital_vega(100, 110, 0.2, 1) > 0 and digital_vega(100, 90, 0.2, 1) < 0


def test_q10_digital_skew():
    base = digital(100, 100, 0.2, 1)
    v = vega(100, 100, 0.2, 1)
    assert round(base, 4) == 0.4602 and round(v, 1) == 39.7
    assert round(base + v * 0.001, 3) == 0.500
    # check against finite differences of calls on the skewed surface sigma(K) = 0.2 - 0.001 (K - 100)
    h = 0.01

    def c(k):
        return call(100, k, 0.2 - 0.001 * (k - 100), 1)

    assert abs(-(c(100 + h) - c(100 - h)) / (2 * h) - (base + v * 0.001)) < 1e-4


def test_q11_density():
    assert round((9.0 - 2 * 6.0 + 3.8) / 25, 3) == 0.032 and round(0.032 * 5, 2) == 0.16


def test_q12_variance_swap():
    assert round(math.sqrt(fair_variance_smile(lambda k: 0.2)), 3) == 0.2
    assert round(math.sqrt(fair_variance_smile(smile)), 3) == 0.205


def test_q13_dividend_parity():
    assert 100 - 2 - 100 == -2


def test_q14_straddle():
    straddle = call(100, 100, 0.2, 1 / 252) + put(100, 100, 0.2, 1 / 252)
    assert round(straddle, 2) == 1.01 and round(0.8 * 100 * 0.2 / math.sqrt(252), 2) == 1.01
    assert round(3 - straddle, 2) == 1.99


def test_figure_peak():
    spots = np.arange(80, 120.5, 0.5)
    g = [gamma(s, 100, 0.2, 1 / 52) for s in spots]
    assert abs(spots[int(np.argmax(g))] - 100) <= 1


def test_hook_explanations():
    gap = -parity_gap(7.10, 2.40, 104, 100, 0.04, 0.25)
    # a borrow fee l acting as a dividend yield: S (1 - exp(-l T)) = gap
    fee = -math.log(1 - gap / 104) / 0.25
    assert round(100 * fee, 1) == 1.1
    assert round(10.398 - 9.50, 2) == 0.90


def test_worked_answers():
    from fractions import Fraction

    delta = Fraction(20, 30)
    assert delta == Fraction(2, 3) and delta * 90 == 60 and round(float(delta * 100 - 60), 2) == 6.67
    q = Fraction(100 - 90, 30)
    assert q == Fraction(1, 3) and 20 * q == delta * 100 - 60
    assert round(-1 * 0.30 - 2 * 0.30, 2) == -0.90
    theta = -0.2 * 100 / (2 * math.sqrt(2 * math.pi * 0.25))
    assert round(math.sqrt(2 * math.pi * 0.25), 4) == 1.2533 and round(theta, 2) == -7.98 and round(-theta / 365, 3) == 0.022
    g = gamma(100, 100, 0.2, 0.25)
    assert round(g, 4) == 0.0398 and round(-0.5 * g * 100**2 * 0.04, 2) == -7.97
    h = 1e-5
    bs_theta = -(call(100, 100, 0.2, 0.25) - call(100, 100, 0.2, 0.25 - h)) / h
    assert abs(bs_theta - theta) < 0.02
