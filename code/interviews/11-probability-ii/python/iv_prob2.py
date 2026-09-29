"""Book 18, chapter 11: probability II, exactly (sympy linear systems and fractions)."""
from fractions import Fraction
from math import comb

import sympy as sp


def expected_wait_pattern(pattern: str, alphabet: int = 2) -> Fraction:
    """Expected number of symbols until `pattern` first appears, i.i.d. uniform symbols, by first-step analysis
    on the length of the longest suffix that is a prefix of the pattern. Symbols are characters; 'x' stands for
    any symbol other than those in the pattern when alphabet > number of distinct pattern symbols."""
    m = len(pattern)
    symbols = sorted(set(pattern))
    others = alphabet - len(symbols)
    e = sp.symbols(f"e0:{m}")
    eqs = []
    for k in range(m):
        rhs = sp.Integer(1)
        for s in symbols:
            t = pattern[:k] + s
            j = next(j for j in range(len(t), -1, -1) if pattern[:j] == t[len(t) - j :])
            if j < m:
                rhs += sp.Rational(1, alphabet) * e[j]
        if others:
            rhs += sp.Rational(others, alphabet) * e[0]
        eqs.append(sp.Eq(e[k], rhs))
    sol = sp.solve(eqs, e)
    return Fraction(str(sol[e[0]]))


def race(p1: str, p2: str) -> Fraction:
    """Chance that coin pattern p1 appears before p2 (fair coin), by first-step analysis on states = suffixes."""
    states = set()
    for p in (p1, p2):
        for i in range(len(p)):
            states.add(p[:i])
    states = sorted(states, key=len)
    x = {s: sp.Symbol("x_" + (s or "e")) for s in states}
    eqs = []
    for s in states:
        rhs = 0
        for c in "HT":
            t = s + c
            if t.endswith(p1):
                rhs += sp.Rational(1, 2)
                continue
            if t.endswith(p2):
                continue
            nxt = max((u for u in states if t.endswith(u)), key=len)
            rhs += sp.Rational(1, 2) * x[nxt]
        eqs.append(sp.Eq(x[s], rhs))
    sol = sp.solve(eqs, list(x.values()))
    return Fraction(str(sol[x[""]]))


def ruin_up_prob(p, a: int, b: int) -> Fraction:
    """Random walk +1 w.p. p, -1 otherwise, from 0: chance of reaching +b before -a."""
    p = Fraction(p)
    q = 1 - p
    if p == q:
        return Fraction(a, a + b)
    r = q / p
    return (1 - r**a) / (1 - r ** (a + b))


def symmetric_duration(start: int, top: int) -> int:
    """Expected steps of a symmetric walk from `start` until it hits 0 or `top`."""
    return start * (top - start)


def compound_moments(mean_n, var_n, mean_x, var_x):
    return mean_n * mean_x, mean_n * var_x + var_n * mean_x**2


def expected_distinct(draws: int, values: int) -> Fraction:
    return values * (1 - Fraction(values - 1, values) ** draws)


def best_of_n_uniform(n: int):
    """Values V_k of seeing k more iid U(0,1) offers with no recall: V_1 = 1/2, V_k = (1 + V_{k-1}^2) / 2."""
    v = [Fraction(0), Fraction(1, 2)]
    for _ in range(2, n + 1):
        v.append((1 + v[-1] ** 2) / 2)
    return v


def covering_spacing(n: int) -> Fraction:
    """Expected length of the spacing among n uniform points on [0,1] that covers an independent uniform point."""
    return Fraction(2, n + 2)


def binom_tail(n: int, p, k: int) -> Fraction:
    p = Fraction(p)
    return sum(comb(n, j) * p**j * (1 - p) ** (n - j) for j in range(k, n + 1))


def expected_runs(n: int) -> Fraction:
    return 1 + Fraction(n - 1, 2)
