"""Balancing-group position keeper (build of Book 3, Chapter 6).

A balance responsible party's schedule for each market time unit (MTU) is the net of its trades
(positive = bought, i.e. energy scheduled into the group) plus its forecast own production; its
metered position is its actual production minus consumption. The imbalance volume is metered
minus scheduled: positive = long (more energy than scheduled), settled at the imbalance price.
Energy in MWh per MTU, prices in EUR/MWh.
"""
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class BalancingGroup:
    trades: dict[int, float] = field(default_factory=lambda: defaultdict(float))     # net purchases per MTU
    production: dict[int, float] = field(default_factory=lambda: defaultdict(float))  # scheduled own production
    cash: dict[int, float] = field(default_factory=lambda: defaultdict(float))

    def trade(self, mtu: int, qty: float, price: float) -> None:
        """Buy (qty > 0) or sell (qty < 0) energy for an MTU at a price."""
        self.trades[mtu] += qty
        self.cash[mtu] -= qty * price

    def schedule_production(self, mtu: int, qty: float) -> None:
        self.production[mtu] += qty

    def schedule(self, mtu: int) -> float:
        """Net energy the group has scheduled to deliver into the grid: production minus net sales.
        A balanced schedule for a pure producer is zero: it sells what it will produce."""
        return self.production[mtu] + self.trades[mtu]


def imbalance(scheduled_production: float, net_trades: float, metered_production: float) -> float:
    """Imbalance of a producer: metered production minus what it sold (-net_trades), i.e. the energy
    it delivered beyond (long) or short of its sales."""
    return metered_production + net_trades


def settle(volume: float, price_long: float, price_short: float | None = None) -> float:
    """Cash from the operator for an imbalance: a long position is bought by the operator at the
    long price, a short one is sold to the group at the short price (single price if one is given)."""
    p = price_long if volume >= 0 or price_short is None else price_short
    return volume * p


def day_settlement(sales: dict[int, tuple[float, float]], metered: dict[int, float],
                   imbalance_price: dict[int, float]) -> dict[str, float]:
    """A producer's day: `sales` maps MTU to (MWh sold, price), `metered` its actual output. Returns
    trading revenue, imbalance cash and the total."""
    revenue = sum(q * p for q, p in sales.values())
    imb = sum(settle(metered.get(m, 0.0) - sales.get(m, (0.0, 0.0))[0], imbalance_price[m]) for m in imbalance_price)
    return {"revenue": revenue, "imbalance": imb, "total": revenue + imb}


def capture_price(prices: list[float], output: list[float]) -> float:
    """Output-weighted average price: what a producer with this profile earned per MWh on the spot."""
    total = sum(output)
    if total <= 0:
        raise ValueError("no output")
    return sum(p * q for p, q in zip(prices, output, strict=True)) / total
