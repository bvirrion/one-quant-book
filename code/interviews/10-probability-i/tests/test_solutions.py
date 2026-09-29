"""Numbers gate: every numerical answer printed in Book 18, chapter 10 (text and solutions)."""
import pathlib
import sys
from fractions import Fraction

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from iv_prob1 import (
    arrangements,
    at_least_one,
    bayes,
    first_ace_position,
    first_ace_position_brute,
    four_doors_switch,
    meet_within,
    monday_positions,
    multisets,
    no_collision,
    rank_probabilities,
    ticket_boxes,
    two_dice_protocols,
)


def test_text_examples():
    assert round(float(1 - no_collision(30, 10_000)), 3) == 0.043
    assert first_ace_position() == Fraction(53, 5)
    for n, k in [(6, 1), (8, 2), (10, 3)]:
        assert first_ace_position_brute(n, k) == first_ace_position(n, k)
    pa, pb = two_dice_protocols()
    assert (pa, pb) == (Fraction(1, 11), Fraction(1, 6))


def test_q1_arrangements():
    assert arrangements("ABCDE") == 120 and arrangements("AABBC") == 30


def test_q2_four_rolls():
    p = at_least_one(Fraction(1, 6), 4)
    assert p == Fraction(671, 1296) and round(float(p), 3) == 0.518


def test_q3_two_aces():
    assert Fraction(4, 52) * Fraction(3, 51) == Fraction(1, 221)


def test_q4_stars_and_bars():
    assert multisets(10, 4) == 286 and multisets(10, 4, True) == 84


def test_q5_ranks():
    assert rank_probabilities() == (Fraction(1, 2), Fraction(1, 6), Fraction(1, 3))


def test_q6_collisions():
    p = 1 - no_collision(1000, 10**6)
    assert round(float(p), 3) == 0.393
    assert round(1 - np.exp(-1000 * 999 / 2e6), 3) == 0.393


def test_q7_bayes():
    p = bayes(Fraction(1, 500), Fraction(95, 100), Fraction(2, 100))
    assert p == Fraction(95, 1093) and round(float(p), 3) == 0.087


def test_q8_protocol_simulation():
    rng = np.random.default_rng(0)
    d = rng.integers(1, 7, size=(400_000, 2))
    a = (d == 6).any(axis=1)
    assert abs(np.mean((d[a] == 6).all(axis=1)) - 1 / 11) < 0.005
    pick = rng.integers(0, 2, size=400_000)
    shown = d[np.arange(400_000), pick] == 6
    assert abs(np.mean((d[shown] == 6).all(axis=1)) - 1 / 6) < 0.005


def test_q10_two_alerts():
    odds = Fraction(1, 499) * (Fraction(95, 2)) ** 2
    p = odds / (1 + odds)
    assert round(float(p), 3) == 0.819


def test_q11_tickets():
    assert ticket_boxes() == Fraction(8, 13)
    assert round(8 / 13, 3) == 0.615


def test_q12_four_doors():
    stay, sw = four_doors_switch()
    assert stay == Fraction(1, 4) and sw == Fraction(3, 8)


def test_q13_meet():
    assert meet_within(10, 60) == Fraction(11, 36)
    rng = np.random.default_rng(1)
    t = rng.uniform(0, 60, size=(400_000, 2))
    assert abs(np.mean(np.abs(t[:, 0] - t[:, 1]) <= 10) - 11 / 36) < 0.003


def test_q14_monday():
    assert monday_positions() == Fraction(13, 27)


def test_extra_numbers():
    import math

    assert round(float(1 - no_collision(30, 10_000)), 3) == round(1 - math.exp(-30 * 29 / 20_000), 3)
    n = next(n for n in range(1, 3000) if 1 - no_collision(n, 10**6) >= Fraction(1, 2))
    assert n == 1178 and round(math.sqrt(2e6 * math.log(2))) == 1177
    assert 200 * 0.95 == 190 and round(99_800 * 0.02) == 1996 and round(190 / 2186, 3) == 0.087
    assert round(2 * float(at_least_one(Fraction(1, 6), 4)) - 1, 4) == 0.0355
    assert 14**2 - 13**2 == 27 and 7**2 - 6**2 == 13
    assert (50 / 5, 48 / 5) == (10.0, 9.6)


def test_worked_answers():
    a, b = Fraction(7, 10) * Fraction(2, 5), Fraction(3, 10) * Fraction(9, 10)
    assert a == Fraction(28, 100) and b == Fraction(27, 100) and a / (a + b) == Fraction(28, 55)
    assert round(28 / 55, 2) == 0.51
    rng = np.random.default_rng(10)
    x = rng.standard_normal((200_000, 10))
    best, worst = x.argmax(axis=1), x.argmin(axis=1)
    assert abs((best > worst).mean() - 0.5) < 0.005
    assert abs((best == 9).mean() - 0.1) < 0.003
    assert abs(((best == 9) & (worst == 0)).mean() - 1 / 90) < 0.001
