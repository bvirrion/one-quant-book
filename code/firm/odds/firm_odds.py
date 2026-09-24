"""Odds conversion, overround removal and exchange hedging (build of Book 3, Chapter 27).

Decimal odds o pay o per unit staked (stake included); the implied probability is 1/o. A bookmaker's
implied probabilities sum to more than one; the excess is the overround. Four ways to recover
probabilities: multiplicative (normalise), additive (subtract an equal share), power (raise to a common
exponent), and Shin's model of a bookmaker facing a share z of insiders.
"""
import math


def implied(odds: list[float]) -> list[float]:
    return [1 / o for o in odds]


def overround(odds: list[float]) -> float:
    return sum(implied(odds)) - 1


def multiplicative(odds: list[float]) -> list[float]:
    pi = implied(odds)
    s = sum(pi)
    return [x / s for x in pi]


def additive(odds: list[float]) -> list[float]:
    pi = implied(odds)
    e = (sum(pi) - 1) / len(pi)
    return [x - e for x in pi]


def _bisect(f, lo: float, hi: float, tol: float = 1e-12) -> float:
    flo = f(lo)
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
        if hi - lo < tol:
            break
    return 0.5 * (lo + hi)


def power(odds: list[float]) -> list[float]:
    """p_i = pi_i^k with k chosen so that the p_i sum to one."""
    pi = implied(odds)
    k = _bisect(lambda k: sum(x**k for x in pi) - 1, 1.0, 10.0)
    return [x**k for x in pi]


def shin(odds: list[float]) -> tuple[list[float], float]:
    """Shin (1993): p_i = (sqrt(z^2 + 4 (1 - z) pi_i^2 / S) - z) / (2 (1 - z)), z the insider share, chosen so
    that the p_i sum to one. Returns (probabilities, z)."""
    pi = implied(odds)
    s = sum(pi)

    def probs(z: float) -> list[float]:
        return [(math.sqrt(z * z + 4 * (1 - z) * x * x / s) - z) / (2 * (1 - z)) for x in pi]
    z = _bisect(lambda z: sum(probs(z)) - 1, 0.0, 0.99)
    return probs(z), z


def kelly(p: float, odds: float) -> float:
    """Fraction of wealth to stake at decimal odds for a win probability p (zero if no edge)."""
    return max(0.0, (p * odds - 1) / (odds - 1))


def exchange_payout(stake: float, odds: float, commission: float) -> float:
    """Net profit of a winning back bet on an exchange that charges commission on net winnings."""
    return stake * (odds - 1) * (1 - commission)


def hedge_equal(back_stake: float, back_odds: float, lay_odds: float,
                commission: float = 0.0) -> tuple[float, float, float]:
    """Lay stake that equalises the outcome of a back bet, and the profit if the selection wins or loses
    (commission charged on the winning side's net winnings, before it is netted)."""
    lay = back_stake * back_odds / lay_odds
    win = back_stake * (back_odds - 1) - lay * (lay_odds - 1)
    lose = lay - back_stake
    return lay, win * (1 - commission) if win > 0 else win, lose * (1 - commission) if lose > 0 else lose
