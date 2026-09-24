"""Corporate-action adjustment and index maintenance (Chapter 8)."""
from dataclasses import dataclass

import numpy as np


def split_factor(new_for_old: float) -> float:
    """k-for-1 split: prices before the ex-date are multiplied by 1/k."""
    return 1.0 / new_for_old


def dividend_factor(cum_price: float, dividend: float) -> float:
    """Cash dividend D on a stock closing cum-dividend at P: (P - D) / P."""
    return (cum_price - dividend) / cum_price


def reinvest_factor(ex_price: float, dividend: float) -> float:
    """Exact total-return factor: a holder reinvesting D at the ex price owns 1 + D / P_ex shares."""
    return ex_price / (ex_price + dividend)


def terp(cum_price: float, old_shares: float, new_shares: float, subscription: float) -> float:
    """Theoretical ex-rights price of an n-for-N rights issue at price S."""
    return (old_shares * cum_price + new_shares * subscription) / (old_shares + new_shares)


def rights_factor(cum_price: float, old_shares: float, new_shares: float, subscription: float) -> float:
    return terp(cum_price, old_shares, new_shares, subscription) / cum_price


def back_adjust(raw: np.ndarray, events: dict[int, float]) -> np.ndarray:
    """Back-adjusted series. events[i] = factor of an action whose ex-date is day i:
    every price strictly before day i is multiplied by it."""
    adj = np.asarray(raw, dtype=float).copy()
    for i, f in events.items():
        adj[:i] *= f
    return adj


@dataclass
class CapIndex:
    """Float-adjusted capitalisation-weighted index maintained with a divisor."""
    shares: dict[str, float]          # shares outstanding
    floats: dict[str, float]          # investable weight factors in [0, 1]
    divisor: float

    def market_value(self, prices: dict[str, float]) -> float:
        return sum(prices[s] * self.shares[s] * self.floats[s] for s in self.shares)

    def level(self, prices: dict[str, float]) -> float:
        return self.market_value(prices) / self.divisor

    def rebase(self, prices: dict[str, float], change) -> None:
        """Apply `change(self)` (add/remove a constituent, change shares or float) at the
        given prices, and move the divisor so that the level is unchanged."""
        before = self.market_value(prices)
        change(self)
        self.divisor *= self.market_value(prices) / before


def weights_cap(prices, shares, floats):
    mv = {s: prices[s] * shares[s] * floats[s] for s in prices}
    tot = sum(mv.values())
    return {s: v / tot for s, v in mv.items()}


def weights_price(prices):
    tot = sum(prices.values())
    return {s: p / tot for s, p in prices.items()}
