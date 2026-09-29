"""Numbers gate: every numerical answer printed in Book 18, chapter 6 (text and solutions)."""
import math
import pathlib
import sys
from fractions import Fraction

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from fig_iv_game import game_rows
from iv_game import (
    DECK,
    fair_after,
    fair_given_one_above,
    informed_loss,
    kelly_fraction,
    log_growth,
    mean_var,
    red_card_value,
    sum_distribution,
)


def test_q1_market():
    m, v = mean_var(sum_distribution())
    assert m == 21 and v == Fraction(686, 17)
    assert round(math.sqrt(v), 2) == 6.35
    # closed form: 3 * 14 * (52 - 3) / (52 - 1)
    assert Fraction(3 * 14 * 49, 51) == v


def test_band_and_figure():
    cards, rows = game_rows()
    assert cards == [6, 3, 7]
    assert rows[0][2:] == (10, 32)
    assert round(rows[1][1], 2) == 20.04 and rows[2][1] == 16.1 and rows[3][1] == 16


def test_q3_after_king():
    f = fair_after([13])
    assert f == Fraction(455, 17) and round(float(f), 2) == 26.76


def test_q4_inference():
    f = fair_given_one_above(7)
    assert round(float(f), 2) == 24.36


def test_q7_position():
    f = fair_after([5, 6])
    assert f == Fraction(903, 50) and round(float(f), 2) == 18.06
    assert round(3 * (float(f) - 24), 2) == -17.82


def test_q5_kelly():
    assert math.isclose(kelly_fraction(0.6), 0.2)
    assert round(log_growth(0.6, 0.2), 4) == 0.0201
    assert log_growth(0.6, 0.2) > log_growth(0.6, 0.1) and log_growth(0.6, 0.2) > log_growth(0.6, 0.3)
    assert round(100 * math.exp(10 * log_growth(0.6, 0.2)), 1) == 122.3


def test_q8_informed():
    assert round(float(informed_loss(0)), 2) == 3.10
    assert round(float(informed_loss(2)), 2) == 1.43
    edge = fair_after([13]) - 21
    assert edge == Fraction(98, 17) and round(float(edge), 2) == 5.76
    assert informed_loss(edge) == 0


def test_q9_red_card():
    assert red_card_value(30, 22) == Fraction(15, 26)
    for r in range(0, 8):
        for b in range(0, 8):
            if r + b:
                assert red_card_value(r, b) == Fraction(r, r + b)


def test_q9_simulation():
    wins = []
    for seed in range(20):
        rng = np.random.default_rng(seed)
        deck = np.array([1] * 30 + [0] * 22)
        w = 0
        for _ in range(2_000):
            d = rng.permutation(deck)
            # a rule that waits until more black than red has been seen, else bets on the last card
            seen_r = seen_b = 0
            bet = d[-1]
            for i, c in enumerate(d[:-1]):
                if seen_b - seen_r >= 2:
                    bet = d[i]
                    break
                seen_r += c
                seen_b += 1 - c
            w += bet
        wins.append(w / 2_000)
    assert abs(np.mean(wins) - 15 / 26) < 0.01


def test_deck():
    assert len(DECK) == 52 and sum(DECK) == 364


def test_q6_group_anchor():
    from scipy.stats import norm

    assert 20 * 252 == 5040
    assert round(2 / 1.2, 1) == 1.7
    assert round(2 * norm.sf(2 / 1.2), 3) == 0.096


def test_q7_third_card_sd():
    rest = list(DECK)
    rest.remove(5)
    rest.remove(6)
    m = sum(rest) / len(rest)
    sd = (sum((x - m) ** 2 for x in rest) / len(rest)) ** 0.5
    assert round(m, 2) == 7.06 and round(sd, 1) == 3.8


def test_worked_answers():
    c = math.comb
    absent = Fraction(c(39, 4), c(52, 4))
    e4 = 4 * (1 - absent)
    assert round(float(absent), 3) == 0.304 and round(float(e4), 2) == 2.78
    assert round(13**4 / c(52, 4), 2) == 0.11
    e_after_one = 1 + 3 * (1 - Fraction(c(38, 3), c(51, 3)))
    assert e_after_one == e4
    e_after_two = 1 + 3 * (1 - Fraction(c(37, 2), c(50, 2)))
    assert round(float(e_after_two), 2) == 2.37
    rng = np.random.default_rng(6)
    suits = np.repeat(np.arange(4), 13)
    hands = np.array([rng.permutation(suits)[:4] for _ in range(20_000)])
    distinct = np.array([len(set(h)) for h in hands])
    assert abs(distinct.mean() - float(e4)) < 0.02
    se = math.sqrt((1 + 1.5**2 / 2) / 1.5)
    assert round(se, 2) == 1.19 and round(1.5 / se, 1) == 1.3
