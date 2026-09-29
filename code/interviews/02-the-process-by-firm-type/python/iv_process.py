"""Book 18, chapter 2: deciding between processes that run on different clocks.

Accept-or-wait against a deadline, the classical best-choice (secretary) rule, and the
arithmetic of an internship class. Exact with fractions where the answer is rational.
"""
from fractions import Fraction
from math import ceil


def value_of_waiting(q, offer_value, fallback):
    """Expected value of declining a held offer to wait for a process that ends in an offer with probability q."""
    return q * offer_value + (1 - q) * fallback


def breakeven_q(held, offer_value, fallback):
    """Offer probability at which waiting is worth exactly the held offer."""
    return Fraction(held - fallback) / Fraction(offer_value - fallback)


def best_choice_probability(n: int, r: int) -> Fraction:
    """Chance of taking the best of n offers seen in random order when the first r-1 are declined and the
    first later offer better than all earlier ones is accepted (Ferguson 1989, eq. 1)."""
    if r == 1:
        return Fraction(1, n)
    return Fraction(r - 1, n) * sum(Fraction(1, i - 1) for i in range(r, n + 1))


def optimal_cutoff(n: int):
    """The cutoff r maximising best_choice_probability(n, r), and that probability."""
    return max(((r, best_choice_probability(n, r)) for r in range(1, n + 1)), key=lambda t: t[1])


def interns_needed(hires: int, return_rate, accept_rate) -> int:
    """Interns to take so that return offers times acceptances cover the hires, in expectation."""
    return ceil(Fraction(hires) / (Fraction(return_rate) * Fraction(accept_rate)))
