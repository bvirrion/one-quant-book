"""Numbers gate: every numerical answer printed in Book 18, chapter 11 (text and solutions)."""
import itertools
import math
import pathlib
import sys
from fractions import Fraction

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from iv_prob2 import (
    best_of_n_uniform,
    binom_tail,
    compound_moments,
    covering_spacing,
    expected_distinct,
    expected_runs,
    expected_wait_pattern,
    race,
    ruin_up_prob,
    symmetric_duration,
)


def test_text_examples():
    assert expected_wait_pattern("66", 6) == 42
    assert expected_wait_pattern("HH") == 6 and expected_wait_pattern("HT") == 4
    perms = list(itertools.permutations(range(5)))
    assert Fraction(sum(sum(p[i] == i for i in range(5)) for p in perms), len(perms)) == 1
    assert sum(Fraction(1, k) for k in range(1, 11)) == Fraction(7381, 2520)
    assert round(float(sum(Fraction(1, k) for k in range(1, 11))), 2) == 2.93
    assert ruin_up_prob(Fraction(1, 2), 3, 7) == Fraction(3, 10)


def test_q1_q2_q3():
    perms = list(itertools.permutations(range(6)))
    assert Fraction(sum(sum(p[i] == i for i in range(6)) for p in perms), len(perms)) == 1
    assert 6 + 6 == 12
    assert expected_runs(10) == Fraction(11, 2)
    seqs = list(itertools.product([0, 1], repeat=10))
    assert Fraction(sum(1 + sum(a != b for a, b in zip(s, s[1:], strict=False)) for s in seqs), len(seqs)) == Fraction(11, 2)


def test_q4_q5():
    x = np.random.default_rng(0).random((400_000, 2))
    assert abs(x.min(axis=1).mean() - 1 / 3) < 0.002 and abs(x.max(axis=1).mean() - 2 / 3) < 0.002
    assert Fraction(3, 4) == Fraction(3, 3 + 1) and Fraction(60, 4) == 15


def test_q6_same_face_twice():
    # any face repeated: after the first roll, each roll repeats the previous with probability 1/6
    assert 1 + 6 == 7
    rng = np.random.default_rng(1)
    waits = []
    for _ in range(20_000):
        prev, n = rng.integers(6), 1
        while True:
            cur, n = rng.integers(6), n + 1
            if cur == prev:
                break
            prev = cur
        waits.append(n)
    assert abs(np.mean(waits) - 7) < 0.1


def test_q7_ruin_with_drift():
    p = ruin_up_prob(Fraction(51, 100), 10, 10)
    assert round(float(p), 3) == 0.599
    assert math.isclose(float(p), 1 / (1 + (49 / 51) ** 10))


def test_q8_duration():
    assert symmetric_duration(3, 10) == 21
    rng = np.random.default_rng(2)
    t = []
    for _ in range(20_000):
        x, n = 3, 0
        while 0 < x < 10:
            x += 1 if rng.random() < 0.5 else -1
            n += 1
        t.append(n)
    assert abs(np.mean(t) - 21) < 0.5


def test_q9_wald():
    m, v = compound_moments(40, 40, 0.3, 4)
    assert round(m, 6) == 12 and round(v, 6) == 163.6 and round(math.sqrt(v), 2) == 12.79


def test_q10_distinct():
    assert round(float(expected_distinct(20, 365)), 2) == 19.49


def test_q11_race():
    assert race("HHT", "HTH") == Fraction(2, 3)
    assert expected_wait_pattern("HTH") == 10 and expected_wait_pattern("HHT") == 8
    rng = np.random.default_rng(3)
    wins = 0
    for _ in range(20_000):
        s = ""
        while True:
            s += "H" if rng.random() < 0.5 else "T"
            if s.endswith("HHT"):
                wins += 1
                break
            if s.endswith("HTH"):
                break
    assert abs(wins / 20_000 - 2 / 3) < 0.01


def test_q12_best_of_five():
    v = best_of_n_uniform(5)
    assert v[2] == Fraction(5, 8)
    assert round(float(v[5]), 3) == 0.775 and round(float(v[4]), 3) == 0.742


def test_q13_inspection():
    assert covering_spacing(5) == Fraction(2, 7)
    assert round(float(covering_spacing(5)) * 60, 1) == 17.1
    assert Fraction(2, 6) * 60 == 20 and Fraction(1, 6) * 60 == 10
    rng = np.random.default_rng(4)
    u = np.sort(rng.random((200_000, 5)), axis=1)
    edges = np.concatenate([np.zeros((200_000, 1)), u, np.ones((200_000, 1))], axis=1)
    t = rng.random(200_000)
    idx = (edges <= t[:, None]).sum(axis=1) - 1
    lengths = edges[np.arange(200_000), idx + 1] - edges[np.arange(200_000), idx]
    assert abs(lengths.mean() - 2 / 7) < 0.002


def test_q14_coupling():
    assert round(float(binom_tail(10, Fraction(3, 5), 7)), 3) == 0.382
    assert binom_tail(10, Fraction(1, 2), 7) == Fraction(176, 1024)
    assert round(176 / 1024, 3) == 0.172


def test_q11_q9_extras():
    assert race("THH", "HHT") == Fraction(3, 4)
    assert expected_wait_pattern("THH") == 8
    m, v = compound_moments(40, 40, 0.3, 4)
    assert round(m / math.sqrt(v), 2) == 0.94
    assert 6 * Fraction(2, 42) == Fraction(2, 7)


def test_worked_answers():
    assert Fraction(5 * 4 + 5 * 4, 10 * 9) == Fraction(4, 9) and 9 * Fraction(4, 9) == 4
    seqs = set(itertools.permutations("BBBBBSSSSS"))
    tot = sum(sum(s[i] == s[i + 1] for i in range(9)) for s in seqs)
    assert Fraction(tot, len(seqs)) == 4
    e = {}

    def ex(k):
        if k <= 0:
            return Fraction(0)
        if k not in e:
            e[k] = 1 + Fraction(1, 6) * sum(ex(k - j) for j in range(1, 7))
        return e[k]

    assert ex(1) == 1 and ex(2) == Fraction(7, 6) and ex(3) == Fraction(49, 36) and round(49 / 36, 2) == 1.36
    for k in range(1, 8):
        assert ex(k) == Fraction(7, 6) ** (k - 1)
    assert round(float(ex(7)), 2) == 2.52 and ex(8) != Fraction(7, 6) ** 7
    assert abs(float(ex(100)) - (100 / 3.5 + 10 / 21)) < 1e-9
