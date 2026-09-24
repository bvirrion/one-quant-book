"""Borrow fees, the cost of carrying a short, and a covering cascade (Chapter 16). Illustrative."""
import numpy as np


def fee_from_utilisation(u: float, gc: float = 0.003, kink: float = 0.75, max_fee: float = 0.80) -> float:
    """Annual borrow fee: general collateral below the kink, then convex up to `max_fee` at u = 1."""
    if u <= kink:
        return gc
    x = (min(u, 1.0) - kink) / (1.0 - kink)
    return gc + (max_fee - gc) * x**2


def carry_short(prices: np.ndarray, fees: np.ndarray, shares: float, day_count: int = 360):
    """Daily marked short: price P&L and cumulative borrow cost, charged on the day's market value."""
    price_pnl = shares * (prices[0] - prices)
    cost = np.cumsum(shares * prices * fees / day_count)
    return price_pnl, cost


def breakeven_days(expected_fall: float, fee: float, day_count: int = 360) -> float:
    """Holding period after which the fee has consumed the expected fall (fee on a constant value)."""
    return expected_fall / fee * day_count


def days_to_cover(short_interest_shares: float, adv_shares: float) -> float:
    return short_interest_shares / adv_shares


def squeeze_return(shock: float, k: float, a: float, b: float) -> float:
    """Equilibrium return x = shock + k F(x), F uniform between stop levels a < b (as returns).
    k is the price impact of all shorts covering. Smallest equilibrium, reached from below."""
    if shock <= a:
        return shock
    if k >= b - a:                                   # each cover triggers more than one cover
        return shock + k
    x = (shock - k * a / (b - a)) / (1.0 - k / (b - a))
    return x if x < b else shock + k


def cascade_path(shock: float, k: float, a: float, b: float, rounds: int = 60) -> list[float]:
    """Iterate x <- shock + k F(x): the rounds of covering."""
    x, out = shock, [shock]
    for _ in range(rounds):
        f = min(1.0, max(0.0, (x - a) / (b - a)))
        x = shock + k * f
        out.append(x)
    return out
