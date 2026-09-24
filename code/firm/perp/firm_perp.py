"""Perpetual contract engine (build of Book 3, Chapter 17).

Index from constituent venues with outlier capping and stale-source exclusion; impact prices;
premium index; time-weighted average premium; funding rate with the interest component and clamp;
mark price as the median of a funding-basis price, a moving-average-basis price and the last trade;
P&L of linear, inverse and quanto contracts. Rates are per funding interval.
"""
from dataclasses import dataclass
from statistics import median


@dataclass(frozen=True)
class Source:
    price: float
    weight: float
    age_s: float                                   # seconds since the venue's last update


def index_price(sources: list[Source], cap: float = 0.03, stale_s: float = 300.0) -> float:
    """Weighted mean of fresh sources, each capped within +-cap of the median of fresh sources."""
    fresh = [s for s in sources if s.age_s <= stale_s]
    if not fresh:
        raise ValueError("no fresh index source")
    med = median(s.price for s in fresh)
    lo, hi = med * (1 - cap), med * (1 + cap)
    w = sum(s.weight for s in fresh)
    return sum(s.weight * min(max(s.price, lo), hi) for s in fresh) / w


def impact_price(levels: list[tuple[float, float]], notional: float) -> float:
    """Average price of filling `notional` (quote currency) through levels [(price, size in base)]."""
    left, base = notional, 0.0
    for p, q in levels:
        take = min(left, p * q)
        base += take / p
        left -= take
        if left <= 0:
            return notional / base
    raise ValueError("book too thin for the impact notional")


def premium_index(impact_bid: float, impact_ask: float, index: float) -> float:
    return (max(0.0, impact_bid - index) - max(0.0, index - impact_ask)) / index


def average_premium(samples: list[float]) -> float:
    """Time-weighted: the k-th sample of the interval has weight k."""
    n = len(samples)
    return sum((k + 1) * p for k, p in enumerate(samples)) / (n * (n + 1) / 2)


def funding_rate(avg_premium: float, interest: float = 0.0001, clamp: float = 0.0005,
                 cap: float = 0.02) -> float:
    """F = P + clamp(I - P, -clamp, +clamp), then bounded by +-cap."""
    f = avg_premium + min(max(interest - avg_premium, -clamp), clamp)
    return min(max(f, -cap), cap)


def mark_price(index: float, last_funding: float, frac_to_funding: float, basis_ma: float,
               last_trade: float) -> float:
    """Median of index x (1 + F x time-to-funding fraction), index + moving-average basis, last trade."""
    return median([index * (1 + last_funding * frac_to_funding), index + basis_ma, last_trade])


def funding_payment(position_base: float, mark: float, rate: float) -> float:
    """Paid by the holder (negative = received): longs pay shorts when the rate is positive."""
    return position_base * mark * rate


def pnl_linear(size_base: float, entry: float, exit_: float) -> float:
    """In the quote currency."""
    return size_base * (exit_ - entry)


def pnl_inverse(contracts_usd: float, entry: float, exit_: float) -> float:
    """In coin: each contract is worth one dollar of the coin; long N contracts."""
    return contracts_usd * (1 / entry - 1 / exit_)


def pnl_quanto(contracts: float, coin_per_usd: float, entry: float, exit_: float) -> float:
    """In the settlement coin: a fixed amount of it per dollar of price move, whatever the coin's price."""
    return contracts * coin_per_usd * (exit_ - entry)
