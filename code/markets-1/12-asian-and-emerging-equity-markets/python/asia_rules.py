"""Price limits, lots and transaction taxes (Chapter 12)."""
import math

import numpy as np


def locked_days(shock: float, limit: float) -> int:
    """Full limit-days needed before a price can reach a shock of relative size `shock`
    (same sign as the shock) when each day's move is capped at `limit`."""
    if shock == 0:
        return 0
    n = math.log(1.0 + abs(shock)) / math.log(1.0 + limit) if shock > 0 else \
        math.log(1.0 - abs(shock)) / math.log(1.0 - limit)
    return max(0, math.ceil(n - 1e-12) - 1)


def truncate(true_returns: np.ndarray, limit: float) -> np.ndarray:
    """Observed daily returns when the price cannot move more than `limit` a day and the
    untraded remainder carries over to the following days."""
    obs = np.empty_like(true_returns)
    gap = 0.0                                   # log distance between fair and observed price
    for t, r in enumerate(true_returns):
        want = gap + math.log1p(r)
        capped = min(max(want, math.log(1.0 - limit)), math.log(1.0 + limit))
        obs[t] = math.expm1(capped)
        gap = want - capped
    return obs


def autocorr(x: np.ndarray) -> float:
    x = x - x.mean()
    return float((x[1:] * x[:-1]).sum() / (x * x).sum())


def round_to_lot(quantity: float, lot: int) -> int:
    """Largest whole number of board lots not exceeding the wanted quantity."""
    return int(quantity // lot) * lot


def round_trip_tax_bp(buy_rate: float, sell_rate: float) -> float:
    return (buy_rate + sell_rate) * 1e4


# Transaction taxes verified for the dated box (fractions of traded value); ledger rows F3, F5.
TAXES = {
    "Hong Kong shares (stamp duty)": (0.0010, 0.0010),
    "India shares for delivery (STT)": (0.0010, 0.0010),
    "India index futures (STT)": (0.0, 0.0005),
}


def breakeven_trades_per_year(gross_edge_bp: float, tax_bp: float, other_cost_bp: float) -> float:
    """Net edge per round trip; non-positive means the strategy cannot exist in this market."""
    return gross_edge_bp - tax_bp - other_cost_bp
