"""Numbers gate: every numerical answer printed in Book 18, chapter 7 (text and solutions)."""
import pathlib
import sys
from fractions import Fraction

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from iv_offer import (
    A,
    B,
    best_single_ask,
    breakeven_leave_probability,
    deferral_schedule,
    expected_value,
    forfeited,
    sign_on_repayment,
    value_if_leave,
    value_if_stay,
)


def test_text_two_offers():
    assert (value_if_stay(A), value_if_leave(A)) == (1070, 670)
    assert (value_if_stay(B), value_if_leave(B)) == (960, 900)
    p = breakeven_leave_probability(A, B)
    assert p == Fraction(11, 34) and round(float(p), 2) == 0.32
    assert expected_value(A, Fraction(1, 5)) == 990 and expected_value(B, Fraction(1, 5)) == 948
    assert expected_value(A, Fraction(1, 2)) == 870 and expected_value(B, Fraction(1, 2)) == 930
    # A's sensitivity to leaving is 400 a unit of probability, B's 60
    assert value_if_stay(A) - value_if_leave(A) == 400 and value_if_stay(B) - value_if_leave(B) == 60


def test_text_monte_carlo():
    for p in (0.1, 0.3, 0.6):
        est = []
        for seed in range(20):
            leave = np.random.default_rng(seed).random(20_000) < p
            est.append(np.where(leave, float(value_if_leave(A)), float(value_if_stay(A))).mean())
        assert abs(np.mean(est) - float(expected_value(A, p))) < 1.0


def test_q2_sign_on():
    assert sign_on_repayment(60_000, 9) == 37_500
    assert sign_on_repayment(60_000, 30) == 0


def test_q3_deferral():
    cash, inst = deferral_schedule(200_000, Fraction(2, 5))
    assert cash == 120_000 and inst == [Fraction(80_000, 3)] * 3
    assert round(float(inst[0])) == 26_667
    assert forfeited(200_000, Fraction(2, 5), 18) == Fraction(160_000, 3)
    assert round(float(forfeited(200_000, Fraction(2, 5), 18))) == 53_333


def test_q6_noncompete():
    # paid garden leave of six months at base 250 against an unpaid twelve-month non-compete, next job at 400 a year
    paid_leave_cost = Fraction(6, 12) * 400 - Fraction(6, 12) * 250
    unpaid_cost = Fraction(12, 12) * 400
    assert paid_leave_cost == 75 and unpaid_cost == 400


def test_q9_ask():
    a, ev, brute = best_single_ask(260, 250, 350)
    assert a == 305 and ev == Fraction(1121, 4) and round(float(ev), 2) == 280.25
    assert brute == (Fraction(305), Fraction(1121, 4))
    # acceptance probability at the optimum
    assert Fraction(350 - 305, 100) == Fraction(9, 20)


def test_q8_counteroffer():
    # match plus 20% on a base of 200: 240; the external offer's total of 320 against the counter's 240 + bonus 60
    assert 200 * Fraction(6, 5) == 240
