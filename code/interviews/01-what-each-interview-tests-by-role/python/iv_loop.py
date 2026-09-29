"""Book 18, chapter 1: the arithmetic of an interview loop.

Stage pass rates, the chance of at least one offer, a loop of noisy interviews
and the value of several independent interviewers. Exact where possible.
"""
from fractions import Fraction
from math import comb, erf, sqrt


def phi(x: float) -> float:
    """Standard normal cdf."""
    return 0.5 * (1.0 + erf(x / sqrt(2.0)))


def offer_probability(pass_rates):
    """Probability that one application ends in an offer: the product of the stage pass rates."""
    p = Fraction(1)
    for r in pass_rates:
        p *= Fraction(r)
    return p


def expected_stages_sat(pass_rates):
    """Expected number of stages a candidate sits per application (stage k is sat if k-1 were passed)."""
    total, reach = Fraction(0), Fraction(1)
    for r in pass_rates:
        total += reach
        reach *= Fraction(r)
    return total


def at_least_one(p, n: int):
    """Chance of at least one success in n independent tries of probability p."""
    return 1 - (1 - p) ** n


def loop_pass(theta: float, k: int, need: int, bar: float = 0.0, noise: float = 1.0) -> float:
    """Chance that a candidate of ability theta passes at least `need` of k independent interviews.

    Each interview scores theta + noise * Z and is passed when the score exceeds `bar`.
    """
    p = phi((theta - bar) / noise)
    return sum(comb(k, j) * p**j * (1 - p) ** (k - j) for j in range(need, k + 1))


def average_score_correlation(noise: float, n: int, spread: float = 1.0) -> float:
    """Correlation between ability (sd `spread`) and the mean of n independent interviewer scores."""
    return spread / sqrt(spread**2 + noise**2 / n)
