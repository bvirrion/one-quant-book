"""Book 18, chapter 13: betting and market-making games, exactly where possible."""
from fractions import Fraction
from functools import cache
from itertools import product
from math import comb, log

import sympy as sp


def kelly_binary(p, net_odds):
    """Fraction of wealth to stake on a bet paying net_odds per unit if it wins (probability p)."""
    p = Fraction(p)
    return p - (1 - p) / Fraction(net_odds)


def kelly_general(outcomes):
    """Kelly fraction for a bet with (probability, net return per unit staked) outcomes, exact by sympy."""
    f = sp.Symbol("f", real=True)
    g = sum(sp.Rational(p) * sp.log(1 + sp.Rational(r) * f) for p, r in outcomes)
    sols = [s for s in sp.solve(sp.diff(g, f), f) if s.is_real and 0 <= s < 1]
    return sols[0]


def log_growth(outcomes, f: float) -> float:
    return sum(float(p) * log(1 + float(r) * f) for p, r in outcomes)


def halving_probability(kelly_multiple, fraction_left=0.5):
    """Continuous-time approximation (One Quant Book 2, chapter 29): chance of ever falling to
    `fraction_left` of starting wealth at c times the Kelly fraction is fraction_left ** (2/c - 1)."""
    return fraction_left ** (2 / kelly_multiple - 1)


def dice_sum_moments(n_dice: int):
    vals = [sum(t) for t in product(range(1, 7), repeat=n_dice)]
    m = Fraction(sum(vals), len(vals))
    v = Fraction(sum((x - m) ** 2 for x in vals), len(vals))
    return m, v


def expected_max_dice(n_dice: int) -> Fraction:
    return Fraction(sum(max(t) for t in product(range(1, 7), repeat=n_dice)), 6**n_dice)


def red_in_top(k: int = 10, red: int = 26, total: int = 52):
    """Mean and variance of the number of red cards among the top k (hypergeometric)."""
    m = Fraction(k * red, total)
    v = Fraction(k * red * (total - red) * (total - k), total * total * (total - 1))
    return m, v


def fair_sum_given_die_at_least(threshold: int = 4, n_dice: int = 3):
    """Expected sum of n dice given that one known die is at least `threshold`."""
    faces = range(threshold, 7)
    return Fraction(sum(faces), len(faces)) + Fraction(7, 2) * (n_dice - 1)


def mm_profit(h, alpha, span=100, demand_width=20):
    """Per-arrival expected profit of a market maker quoting mid +/- h on a value uniform on [0, span]:
    with probability alpha an informed trader who knows the value trades when it is outside the quotes; otherwise
    an uninformed trader arrives and trades (buy or sell) with probability max(0, 1 - h / demand_width)."""
    h = Fraction(h)
    half = Fraction(span, 2)
    informed_loss = (half - h) ** 2 / span if h < half else Fraction(0)  # both sides: 2 * (half - h)^2 / (2 * span)
    demand = max(Fraction(0), 1 - h / demand_width)
    return (1 - Fraction(alpha)) * h * demand - Fraction(alpha) * informed_loss


def best_width(alpha, grid=None):
    grid = grid or [Fraction(i, 10) for i in range(0, 201)]
    return max(grid, key=lambda h: mm_profit(h, alpha))


def winner_curse_shade(noise_half_width=10):
    """Two bidders see V + U(-w, w); both bid signal - k; the winner (higher signal) earns k - max(e1, e2) on
    average; zero expected profit at k = E[max of two U(-w, w)] = w / 3."""
    return Fraction(noise_half_width, 3)


@cache
def red_black_value(red: int, black: int) -> Fraction:
    """Turn cards one at a time: red pays +1, black -1; stop whenever you like. Value of optimal play."""
    if red == 0:
        return Fraction(0)
    if black == 0:
        return Fraction(red)
    n = red + black
    cont = Fraction(red, n) * (1 + red_black_value(red - 1, black)) + Fraction(black, n) * (
        -1 + red_black_value(red, black - 1)
    )
    return max(Fraction(0), cont)


def fixed_bet_ruin(bankroll_units: int, rounds: int, p):
    """Bet one unit a round at even money with win probability p, for `rounds` rounds, stopping if broke.
    Returns (probability of ruin, expected final bankroll in units)."""
    p = Fraction(p)
    dist = {bankroll_units: Fraction(1)}
    ruin = Fraction(0)
    for _ in range(rounds):
        new = {}
        for w, pr in dist.items():
            if w == 0:
                continue
            new[w + 1] = new.get(w + 1, 0) + pr * p
            new[w - 1] = new.get(w - 1, 0) + pr * (1 - p)
        ruin += new.pop(0, Fraction(0))
        dist = new
    final = sum(w * pr for w, pr in dist.items())
    return ruin, final


def binom_pmf(n, k, p):
    return comb(n, k) * p**k * (1 - p) ** (n - k)
