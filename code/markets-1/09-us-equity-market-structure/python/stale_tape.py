"""How stale is a consolidated tape? (Chapter 9). Parameters illustrative.

The fair price jumps by J ticks at Poisson times. Venue v reprices its one-tick-wide quote d_v
microseconds after each jump. A direct-feed reader sees each venue's new quote at once; the
consolidated tape shows it `sip_delay` microseconds later.
"""
from dataclasses import dataclass

import numpy as np

VENUE_DELAYS_US = (50.0, 120.0, 200.0, 400.0)


@dataclass(frozen=True)
class Market:
    seconds: float = 600.0
    jumps_per_second: float = 5.0
    venue_delays_us: tuple[float, ...] = VENUE_DELAYS_US


def jumps(m: Market, seed: int):
    rng = np.random.default_rng(seed)
    n = rng.poisson(m.seconds * m.jumps_per_second)
    times = np.sort(rng.uniform(0.0, m.seconds, n))
    sizes = rng.choice([1, 2, 3], size=n, p=[0.7, 0.2, 0.1]) * rng.choice([-1, 1], size=n)
    return times, np.cumsum(sizes), sizes


def venue_mid(times, level, delay_us, t):
    """Mid (in ticks) quoted by a venue at times t, given its repricing delay."""
    k = np.searchsorted(times + delay_us * 1e-6, t, side="right")
    return np.where(k > 0, level[np.maximum(k - 1, 0)], 0)


def best_bid(times, level, delays_us, t, extra_us=0.0):
    """Best bid across venues: each quotes mid - 1 tick."""
    return np.max([venue_mid(times, level, d + extra_us, t) for d in delays_us], axis=0) - 1


def stale_fraction(m: Market, sip_delay_us: float, seed: int = 9) -> float:
    """Fraction of time during which the tape's best bid differs from the direct-feed best bid."""
    times, level, _ = jumps(m, seed)
    cuts = np.sort(np.concatenate([times + (d + e) * 1e-6 for d in m.venue_delays_us for e in (0.0, sip_delay_us)]
                                  + [[0.0, m.seconds]]))
    cuts = cuts[(cuts >= 0.0) & (cuts <= m.seconds)]
    mids, widths = 0.5 * (cuts[1:] + cuts[:-1]), np.diff(cuts)
    direct = best_bid(times, level, m.venue_delays_us, mids)
    tape = best_bid(times, level, m.venue_delays_us, mids, extra_us=sip_delay_us)
    return float(widths[direct != tape].sum() / m.seconds)


def sniping_profit_ticks(m: Market, seed: int = 9) -> float:
    """Ticks per share-lot earned by hitting every stale quote after a jump of 2 or 3 ticks.

    After an up-jump of J ticks a slow venue still offers at old mid + 1: buying there and valuing
    at the new mid earns J - 1 ticks (nothing when J = 1). Every venue but the fastest is stale."""
    _, _, sizes = jumps(m, seed)
    per_jump = np.maximum(np.abs(sizes) - 1, 0)
    return float(per_jump.sum() * (len(m.venue_delays_us) - 1))


def net_price(quote: float, side: int, fee_per_share: float) -> float:
    """All-in price of taking liquidity: fee > 0 is paid by the taker, fee < 0 is a rebate to it."""
    return quote + side * fee_per_share
