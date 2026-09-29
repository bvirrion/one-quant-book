"""Numbers gate: every numerical answer printed in Book 18, chapter 13 (text and solutions)."""
import math
import pathlib
import sys
from fractions import Fraction

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from iv_bets import (
    best_width,
    dice_sum_moments,
    expected_max_dice,
    fair_sum_given_die_at_least,
    fixed_bet_ruin,
    halving_probability,
    kelly_binary,
    kelly_general,
    log_growth,
    mm_profit,
    red_black_value,
    red_in_top,
    winner_curse_shade,
)


def test_hook():
    m, _ = dice_sum_moments(3)
    assert m == Fraction(21, 2)
    assert 10 - m == Fraction(-1, 2)  # selling at 10 loses half a point a trade


def test_text_examples():
    assert Fraction(1, 6) * 5 - Fraction(5, 6) * 1 == 0  # 5 to 1 on a six is fair
    assert kelly_binary(Fraction(3, 5), 1) == Fraction(1, 5)
    assert halving_probability(1) == 0.5 and halving_probability(0.5) == 0.125


def test_q1_q2():
    assert Fraction(2 * (2 + 4 + 6), 6) == 4
    assert Fraction(3, 10) * 3 - Fraction(7, 10) == Fraction(1, 5)


def test_q3_q4_q5():
    gaps = [abs(a - b) for a in range(1, 7) for b in range(1, 7)]
    m = Fraction(sum(gaps), 36)
    v = Fraction(sum(g * g for g in gaps), 36) - m * m
    assert m == Fraction(70, 36) and round(float(m), 2) == 1.94
    assert round(float(v), 2) == 2.05 and round(math.sqrt(v), 2) == 1.43
    assert Fraction(sum(g >= 3 for g in gaps), 36) == Fraction(1, 3)
    assert Fraction(sum(g <= 1 for g in gaps), 36) == Fraction(4, 9)
    assert round(math.sqrt(2.5), 2) == 1.58
    assert expected_max_dice(3) == Fraction(119, 24) and round(119 / 24, 2) == 4.96


def test_q6_q7_kelly():
    assert kelly_binary(Fraction(7, 20), 3) == Fraction(2, 15)
    assert Fraction(7, 20) * 3 - Fraction(13, 20) == Fraction(2, 5)
    f = kelly_general([(Fraction(3, 10), 2), (Fraction(3, 10), 0), (Fraction(2, 5), -1)])
    assert f == Fraction(1, 7) or str(f) == "1/7"
    out = [(0.3, 2), (0.3, 0), (0.4, -1)]
    assert log_growth(out, 1 / 7) > log_growth(out, 0.12) and log_growth(out, 1 / 7) > log_growth(out, 0.17)
    assert round(log_growth(out, 1 / 7), 4) == 0.0137


def test_q8_halving():
    assert halving_probability(1) == 0.5 and halving_probability(0.5) == 0.125
    # geometric Brownian motion check: log-wealth drift m, variance s2 with 2m/s2 = 2/c - 1; discrete steps with
    # a Brownian-bridge correction for crossings between steps, over a long horizon
    rng = np.random.default_rng(0)
    for c, target in ((1.0, 0.5), (0.5, 0.125)):
        mu, sig = 0.1, 0.2
        k = c * mu / sig**2
        m, s = k * mu - 0.5 * k * k * sig**2, k * sig
        assert math.isclose(2 * m / s**2, 2 / c - 1)
        a, dt, steps, paths = math.log(0.5), 0.5, 3000, 4000
        x = np.zeros(paths)
        hit = np.zeros(paths, dtype=bool)
        for _ in range(steps):
            y = x + m * dt + s * math.sqrt(dt) * rng.standard_normal(paths)
            p_cross = np.exp(-2 * np.maximum(x - a, 0) * np.maximum(y - a, 0) / (s * s * dt))
            hit |= (y <= a) | (rng.random(paths) < p_cross)
            x = y
        assert abs(hit.mean() - target) < 0.025


def test_q9_red_cards():
    m, v = red_in_top()
    assert m == 5 and v == Fraction(35, 17) and round(math.sqrt(v), 2) == 1.43
    # after seeing three of the ten, all red: the other seven come from 49 cards with 23 red
    assert 3 + Fraction(7 * 23, 49) == Fraction(44, 7) and round(44 / 7, 2) == 6.29


def test_q10_informed_die():
    assert fair_sum_given_die_at_least(4) == 12


def test_q11_width():
    assert best_width(Fraction(5, 100)) == Fraction(52, 5)
    assert best_width(Fraction(15, 100)) == Fraction(57, 5)
    assert round(float(mm_profit(Fraction(57, 5), Fraction(15, 100))), 2) == 1.93
    assert max(mm_profit(Fraction(i, 10), Fraction(3, 10)) for i in range(0, 501)) == 0  # only by not trading
    assert mm_profit(50, Fraction(3, 10)) == 0
    assert mm_profit(0, Fraction(15, 100)) == Fraction(-15, 4)


def test_q12_winners_curse():
    assert winner_curse_shade(10) == Fraction(10, 3)
    rng = np.random.default_rng(1)
    e = rng.uniform(-10, 10, size=(400_000, 2))
    assert abs(e.max(axis=1).mean() - 10 / 3) < 0.03


def test_q13_red_black():
    assert red_black_value(10, 10) == Fraction(26995, 16796)
    assert round(float(red_black_value(10, 10)), 3) == 1.607
    assert round(float(red_black_value(26, 26)), 3) == 2.624


def test_q14_fixed_bets():
    ruin, final = fixed_bet_ruin(10, 100, Fraction(55, 100))
    assert round(float(ruin), 3) == 0.090 and round(float(final), 2) == 19.55


def test_growth_fractions():
    assert round(0.6 * math.log(1.2) + 0.4 * math.log(0.8), 4) == 0.0201
    # continuous approximation: growth at c times Kelly is c (2 - c) times the maximum growth
    assert 0.5 * (2 - 0.5) == 0.75 and 2 * (2 - 2) == 0
    assert sum(1 - Fraction(k - 1, 6) ** 3 for k in range(1, 7)) == Fraction(119, 24)
    assert Fraction(119, 24) > Fraction(161, 36)


def test_worked_answers():
    assert round(math.sqrt(30), 1) == 5.5
    p = Fraction(5, 6)
    assert round(float(1 - p**3), 2) == 0.42 and round(float(1 - p**4), 2) == 0.52
    assert round(float(1 - p**6), 2) == 0.67 and round(float(p**7), 2) == 0.28
    h = Fraction(200)
    assert 300 - h == h - 100 == 100
    # unmoved odds: hedge on B at 1 to 3 (win h/3 on a stake h); A wins: 300 - h, B wins: h/3 - 100
    hb = Fraction(300)
    assert 300 - hb == hb / 3 - 100 == 0
