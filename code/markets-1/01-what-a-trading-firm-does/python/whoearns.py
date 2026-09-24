"""Who earns what from a day of trading in one stock (Chapter 1 tutorial).

A market maker quotes mid -/+ half_spread. Customers send market orders of
fixed size. A fraction `informed` of them know the next move of the mid: after
an informed buy the mid jumps up by `jump`, after an informed sell it jumps
down. Everyone else is noise. Fees follow a maker-taker schedule.
"""
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Day:
    n_orders: int = 20_000
    size: int = 100
    half_spread: float = 0.01
    informed: float = 0.15
    jump: float = 0.03
    noise: float = 0.004
    taker_fee: float = 0.0030
    maker_rebate: float = 0.0020
    commission: float = 0.0010
    clearing_fee: float = 0.0002


BASE = Day()


def simulate_day(seed: int, day: Day = BASE) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    mid, inventory, cash = 50.0, 0, 0.0
    shares = day.n_orders * day.size
    for _ in range(day.n_orders):
        side = 1 if rng.random() < 0.5 else -1          # customer buys (+1) or sells
        price = mid + side * day.half_spread            # customer pays the spread
        cash += side * price * day.size                 # market maker takes the other side
        inventory -= side * day.size
        if rng.random() < day.informed:
            mid += side * day.jump                      # the informed were right
        mid += rng.normal(0.0, day.noise)
    trading = cash + inventory * mid                    # marked at the closing mid
    spread = day.half_spread * shares
    return {
        "mm_spread_earned": spread,
        "mm_position_pnl": trading - spread,
        "mm_rebates": day.maker_rebate * shares,
        "mm_clearing": -day.clearing_fee * shares,
        "mm_net": trading + (day.maker_rebate - day.clearing_fee) * shares,
        "exchange_net": (day.taker_fee - day.maker_rebate) * shares,
        "broker_commission": day.commission * shares,
        "clearing_house": 2 * day.clearing_fee * shares,
        "customers_cost": -(day.half_spread + day.commission) * shares,
        "shares": float(shares),
    }


def break_even_volume(fixed_cost: float, net_capture: float) -> float:
    """Shares per day at which net capture per share pays the fixed cost."""
    if net_capture <= 0:
        raise ValueError("no volume pays for a non-positive capture")
    return fixed_cost / net_capture
