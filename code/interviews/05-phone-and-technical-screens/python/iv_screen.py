"""Book 18, chapter 5: the values behind the chapter's sanity-check questions (exact)."""
from fractions import Fraction
from itertools import product
from math import sqrt


def expected_max_two_dice():
    return Fraction(sum(max(a, b) for a, b in product(range(1, 7), repeat=2)), 36)


def at_least_one(p, n):
    return 1 - (1 - p) ** n


def two_asset_vol(s1, s2, rho, w1=0.5):
    w2 = 1 - w1
    return sqrt(w1 * w1 * s1 * s1 + w2 * w2 * s2 * s2 + 2 * w1 * w2 * rho * s1 * s2)


def domino_tilings(n):
    a, b = 1, 1  # tilings of 2x0 and 2x1
    for _ in range(n - 1):
        a, b = b, a + b
    return b if n >= 1 else 1


def reroll_game(rolls):
    """Value of rolling a die up to `rolls` times, keeping the last roll taken."""
    v = Fraction(7, 2)
    for _ in range(rolls - 1):
        v = Fraction(sum(max(x, v) for x in range(1, 7)), 6)
    return v


def coupon_collector(n):
    return n * sum(Fraction(1, k) for k in range(1, n + 1))
