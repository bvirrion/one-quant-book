"""Numbers gate: every numerical answer printed in Book 18, chapter 1 (text and solutions)."""
import pathlib
import sys
from fractions import Fraction

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from iv_loop import at_least_one, average_score_correlation, expected_stages_sat, loop_pass, offer_probability

TEXT_RATES = [Fraction(3, 10), Fraction(1, 2), Fraction(2, 5)]
BANK_RATES = [Fraction(1, 4), Fraction(1, 2), Fraction(2, 5)]


def test_text_example():
    p = offer_probability(TEXT_RATES)
    assert p == Fraction(3, 50)
    assert expected_stages_sat(TEXT_RATES) == Fraction(29, 20)  # 1.45 stages per application
    assert round(float(1 / p), 1) == 16.7
    assert round(float(at_least_one(p, 20)), 2) == 0.71
    # stages sat per offer
    assert round(float(expected_stages_sat(TEXT_RATES) / p), 1) == 24.2


def test_q3_pipeline():
    p = offer_probability(BANK_RATES)
    assert p == Fraction(1, 20)
    assert 1 / p == 20
    assert round(float(at_least_one(p, 12)), 2) == 0.46
    # applications needed for a 90% chance of at least one offer
    n = next(n for n in range(1, 200) if at_least_one(p, n) >= Fraction(9, 10))
    assert n == 45


def test_q5_loop():
    p1 = loop_pass(0.5, 1, 1)
    assert round(p1, 3) == 0.691
    assert round(loop_pass(0.5, 4, 4), 3) == 0.229
    assert round(loop_pass(0.5, 4, 3), 3) == 0.637
    # a candidate at the bar
    assert round(loop_pass(0.0, 4, 4), 4) == 0.0625
    assert round(loop_pass(0.0, 4, 3), 4) == 0.3125
    # ability needed to pass all four with probability one half
    lo, hi = 0.0, 3.0
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if loop_pass(mid, 4, 4) < 0.5 else (lo, mid)
    assert round(lo, 2) == 1.00  # Phi^-1(0.5 ** 0.25) = 0.998


def test_q5_simulation():

    rates = []
    for seed in range(20):
        r = np.random.default_rng(seed).standard_normal((20_000, 4)) + 0.5 > 0
        rates.append(r.all(axis=1).mean())
    assert abs(np.mean(rates) - loop_pass(0.5, 4, 4)) < 0.003



def test_q7_averaging():
    assert round(average_score_correlation(1.0, 1), 3) == 0.707
    assert round(average_score_correlation(1.0, 2), 3) == 0.816
    assert round(average_score_correlation(1.0, 4), 3) == 0.894
    # two interviewers who confer first and share half their noise: effective noise variance 0.5 + 0.5/2
    r_conf = 1 / (1 + 0.75) ** 0.5
    assert round(r_conf, 3) == 0.756


def test_q7_simulation():
    out = []
    for seed in range(10):
        rng = np.random.default_rng(100 + seed)
        a = rng.standard_normal(50_000)
        s = a[:, None] + rng.standard_normal((50_000, 2))
        out.append(np.corrcoef(a, s.mean(axis=1))[0, 1])
    assert abs(np.mean(out) - average_score_correlation(1.0, 2)) < 0.003


def test_q1_heads_heads():
    # first-step equations a = 1 + b/2 + a/2, b = 1 + a/2  ->  a = 6
    a = Fraction(6)
    b = 1 + a / 2
    assert a == 1 + b / 2 + a / 2
    # second moments by first-step analysis: A = E[T^2] from state 0, B from state 1
    # T0 = 1 + T', A = E[(1+T')^2]; solve the linear system exactly
    # A = 1/2 E[(1+T1)^2] + 1/2 E[(1+T0)^2], B = 1/2 * 1 + 1/2 E[(1+T0)^2]
    ea, eb = Fraction(6), Fraction(4)
    # A = 1/2 (1 + 2 eb + B) + 1/2 (1 + 2 ea + A);  B = 1/2 + 1/2 (1 + 2 ea + A)
    # substitute B: A = 1/2(1 + 2eb) + 1/2(1/2 + 1/2(1 + 2ea + A)) + 1/2(1 + 2ea + A)
    # solve A (1 - 1/4 - 1/2) = 1/2 + eb + 1/4 + 1/4 + ea/2 + 1/2 + ea
    rhs = Fraction(1, 2) + eb + Fraction(1, 4) + Fraction(1, 4) + ea / 2 + Fraction(1, 2) + ea
    second = rhs / Fraction(1, 4)
    assert second - ea**2 == 22
    # simulation over seeds
    means, variances = [], []
    for seed in range(10):
        rng = np.random.default_rng(seed)
        t = []
        for _ in range(20_000):
            n, last = 0, 0
            while True:
                n += 1
                h = rng.random() < 0.5
                if h and last:
                    break
                last = h
            t.append(n)
        means.append(np.mean(t))
        variances.append(np.var(t))
    assert abs(np.mean(means) - 6) < 0.05
    assert abs(np.mean(variances) - 22) < 0.5
    # disjoint-pairs bound
    assert 2 * 4 == 8


def test_q3_threshold():
    import math

    assert round(math.log(0.1) / math.log(0.95), 1) == 44.9


def test_worked_answers():
    from math import erf, sqrt

    def phi(x):
        return 0.5 * (1 + erf(x / sqrt(2)))

    one = phi(1.0)
    assert round(one, 3) == 0.841 and round(one**5, 2) == 0.42
    assert round(1 - (1 - one**5) ** 3, 2) == 0.81 and round(1 - one**5, 2) == 0.58
    assert round(phi(1.5) ** 5, 2) == 0.71
    assert Fraction(1, 2) ** 5 == Fraction(1, 32)
    assert 12 + 10 + 8 + 4 + 4 + 2 == 40


def test_figure_loops():
    import csv

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
    import fig_iv_loops

    fig_iv_loops.main()
    rows = {r["theta"]: r for r in csv.DictReader(open(fig_iv_loops.OUT / "loops.csv"))}
    assert rows["1.0"]["k1"] == "0.8413" and rows["1.0"]["k5"] == "0.4216"
