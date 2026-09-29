"""Numbers gate: every numerical answer printed in Book 18, chapter 5 (text and solutions)."""
import pathlib
import random
import sys
from fractions import Fraction

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from iv_screen import at_least_one, coupon_collector, domino_tilings, expected_max_two_dice, reroll_game, two_asset_vol
from iv_screen_windows import moving_averages, moving_averages_buggy


def test_text_six_in_six():
    assert round(float(at_least_one(Fraction(1, 6), 6)), 3) == 0.665


def test_q1_max_two_dice():
    v = expected_max_two_dice()
    assert v == Fraction(161, 36)
    assert round(float(v), 2) == 4.47


def test_q2_signals():
    assert round(float(at_least_one(Fraction(15, 100), 10)), 3) == 0.803


def test_q3_windows():
    p = [10, 11, 12, 13]
    assert moving_averages_buggy(p, 2) == [10.5, 11.5]  # misses the last window
    assert moving_averages(p, 2) == [10.5, 11.5, 12.5]
    assert moving_averages_buggy([1, 2], 2) == []  # one window, none returned
    for seed in range(200):
        rng = random.Random(seed)
        xs = [rng.randint(0, 9) for _ in range(rng.randint(0, 20))]
        k = rng.randint(1, 6)
        oracle = [sum(xs[i : i + k]) / k for i in range(len(xs) - k + 1)] if k <= len(xs) else []
        got = moving_averages(xs, k)
        assert len(got) == len(oracle) and all(abs(a - b) < 1e-9 for a, b in zip(got, oracle, strict=True))


def test_q4_portfolio():
    assert round(two_asset_vol(0.2, 0.2, 0.5), 4) == 0.1732
    assert round(two_asset_vol(0.2, 0.2, 1.0), 4) == 0.2


def test_q5_dominoes():
    assert [domino_tilings(n) for n in range(1, 7)] == [1, 2, 3, 5, 8, 13]
    assert [2 ** (n - 1) for n in range(1, 5)] == [1, 2, 4, 8]


def test_q7_reroll():
    assert reroll_game(2) == Fraction(17, 4)
    assert reroll_game(3) == Fraction(14, 3)
    # the planted wrong reasoning: re-roll half the time and average 5 when kept -> 4.5 (misses that the re-roll averages 3.5)
    assert Fraction(1, 2) * 5 + Fraction(1, 2) * 4 == Fraction(9, 2)


def test_q8_coupon():
    v = coupon_collector(6)
    assert v == Fraction(147, 10) and round(float(v), 1) == 14.7
    assert coupon_collector(2) == 3
    means = []
    for seed in range(10):
        rng = np.random.default_rng(seed)
        draws = rng.integers(0, 6, size=(20_000, 80))
        seen = np.zeros((20_000, 6), dtype=bool)
        first_full = np.full(20_000, -1)
        for t in range(80):
            seen[np.arange(20_000), draws[:, t]] = True
            done = seen.all(axis=1) & (first_full < 0)
            first_full[done] = t + 1
        means.append(first_full[first_full > 0].mean())
    assert abs(np.mean(means) - 14.7) < 0.05


def test_worked_answers():
    c = 0.5
    p = 1 - c + c * np.log(c)
    assert round(p, 3) == 0.153 and round(0.5 * np.log(2), 3) == 0.347
    rng = np.random.default_rng(5)
    x, y = rng.uniform(0, 1, (2, 400_000))
    assert abs((x * y > c).mean() - p) < 0.003
    assert not ((x * y > 0.5) & ~((x > 0.5) & (y > 0.5))).any() and p < 0.25
    assert 6 + Fraction(6, 5) == Fraction(36, 5)
    r = random.Random(7)
    total, trials = 0, 40_000
    for _ in range(trials):
        prev, n = 0, 0
        while True:
            x = r.randint(1, 6)
            n += 1
            if prev == 6 and x != 6:
                break
            prev = x
        total += n
    assert abs(total / trials - 7.2) < 0.1
    assert round(1.5 * 252, 0) == 378 and round(1.5 * np.sqrt(252), 1) == 23.8 and round(np.sqrt(252), 1) == 15.9
