"""Book 18, chapter 8: mental arithmetic, exactly.

Every printed answer of the chapter is recomputed here, with the approximations and their errors.
"""
from fractions import Fraction
from math import log, sqrt

from scipy.optimize import brentq


def digit_sum_mod9(n: int) -> int:
    """Casting out nines: the residue of n modulo 9 through its digit sum."""
    return sum(int(c) for c in str(abs(n))) % 9


def nines_check(a: int, b: int, claimed: int) -> bool:
    """True if the claimed product passes casting out nines (it may still be wrong)."""
    return (digit_sum_mod9(a) * digit_sum_mod9(b)) % 9 == digit_sum_mod9(claimed)


def sqrt_linear(a: int, d: float):
    """sqrt(a^2 + d) ~ a + d / (2a), and the bound d^2 / (8 a^3) on the error for d >= 0."""
    return a + d / (2 * a), d * d / (8 * a**3)


def doubling_exact(rate: float) -> float:
    return log(2) / log(1 + rate)


def doubling_rule(rate: float, k: float = 72) -> float:
    return k / (100 * rate)


def rate_where_rule_exact(k: float = 72) -> float:
    return brentq(lambda r: doubling_rule(r, k) - doubling_exact(r), 0.001, 0.5)


def ln1p_series(x: float, terms: int = 3) -> float:
    return sum((-1) ** (n + 1) * x**n / n for n in range(1, terms + 1))


def reciprocal_digits(n: int, places: int = 6) -> str:
    return f"{1 / n:.{places}f}"


def exact_sqrt(x: float) -> float:
    return sqrt(x)


def frac(x) -> Fraction:
    return Fraction(x)
