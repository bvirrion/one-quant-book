"""Numbers gate: every numerical answer printed in Book 18, chapter 2 (text and solutions)."""
import itertools
import pathlib
import sys
from fractions import Fraction

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from iv_process import best_choice_probability, breakeven_q, interns_needed, optimal_cutoff, value_of_waiting


def test_q4_accept_or_wait():
    assert value_of_waiting(Fraction(2, 5), 130, 70) == 94
    assert breakeven_q(100, 130, 70) == Fraction(1, 2)
    # a one-week extension that lets the pending process finish: the decision is then made knowing B
    assert value_of_waiting(Fraction(2, 5), 130, 100) == 112
    # value of the extension against accepting now
    assert 112 - 100 == 12


def test_q6_class():
    assert interns_needed(30, Fraction(3, 5), Fraction(4, 5)) == 63
    assert Fraction(30) / (Fraction(3, 5) * Fraction(4, 5)) == Fraction(125, 2)


def brute_force(n: int, r: int) -> Fraction:
    wins = 0
    perms = list(itertools.permutations(range(n)))
    for p in perms:  # p[i] is the rank of the i-th offer, n-1 the best
        best_seen = max(p[: r - 1], default=-1)
        chosen = next((x for x in p[r - 1 :] if x > best_seen), p[-1])
        wins += chosen == n - 1
    return Fraction(wins, len(perms))


def test_q7_best_choice():
    for n in range(2, 7):
        for r in range(1, n + 1):
            assert best_choice_probability(n, r) == brute_force(n, r)
    r, p = optimal_cutoff(5)
    assert r == 3 and p == Fraction(13, 30)
    assert round(float(p), 3) == 0.433
    assert best_choice_probability(5, 1) == Fraction(1, 5)
    r100, p100 = optimal_cutoff(100)
    assert r100 == 38 and round(float(p100), 3) == 0.371


def test_q7_simulation():
    wins = []
    for seed in range(20):
        rng = np.random.default_rng(seed)
        v = rng.random((20_000, 5))
        best_first2 = v[:, :2].max(axis=1)
        later = v[:, 2:]
        better = later > best_first2[:, None]
        idx = np.where(better.any(axis=1), better.argmax(axis=1), 2)
        chosen = later[np.arange(len(v)), idx]
        wins.append(np.mean(chosen == v.max(axis=1)))
    assert abs(np.mean(wins) - 13 / 30) < 0.005


def test_track_record_se():
    import math

    sr_a = 1.5
    sr_m = sr_a / math.sqrt(12)
    se_m = math.sqrt((1 + sr_m**2 / 2) / 36)
    se_a = se_m * math.sqrt(12)
    assert round(se_a, 2) == 0.60
    assert math.isclose(se_a, math.sqrt((12 + sr_a**2 / 2) / 36))


def test_worked_answers():
    weeks = {"A": 7, "B": 4, "C": 10}
    starts = {k: 12 - v for k, v in weeks.items()}
    assert starts == {"A": 5, "B": 8, "C": 2}
    assert sorted(starts, key=starts.get) == ["C", "A", "B"]
    scores = [3, 3, 4, 2, 3]
    assert Fraction(sum(scores), 5) == 3 and min(scores) == 2
    assert Fraction(sum(scores) + 1, 5) == Fraction(16, 5)
