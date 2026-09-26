"""firm.rebatemm -- rebates, inverted venues and tiers (One Quant Book 11, chapter 17).

Where to rest a passive order, given each venue's fee and queue, and how much volume to add to reach a tier. Built on
firm.feesched (Book 1). Prices in cents a share; a positive fee is paid by the member, a negative one is a rebate.

A resting bid joins the back of a queue of Q shares. Sell orders that take liquidity reach the venue at `lam` shares
a second; the price level is swept (every order at it filled, then the price moves a tick lower) at rate
`mu_through`; the level is abandoned (the bid rises away, the order is cancelled unfilled) at rate `mu_away`. A fill
from ordinary flow earns the half-spread less a mark-out `adverse`; a fill in a sweep earns the half-spread less
one tick. The venue's passive fee is added to every fill.

API (stable):
    queue_edge(Q, lam, mu_through, mu_away, fee, half_spread, adverse, lot, n, seed) -> dict
                                                  fill probability, share of fills from sweeps, edge per fill and per
                                                  order (cents a share), mean time to fill
    monthly_bill(schedule, adav, tcv, days)       the month's passive fees at an average daily added volume
    marginal_fee(schedule, adav, tcv, step)       cents per extra share added a day (the cliff shows as a spike)
    chase(schedule, natural, tcv, days_left, days, loss)
                                                  extra shares a day to reach the next tier over the days left, the
                                                  month's gain and cost, and whether it pays
    last_day_to_chase(schedule, natural, tcv, days, loss)
                                                  the latest day of the month on which starting to chase still pays
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "feesched"))
import firm_feesched as fs  # noqa: E402


def queue_edge(Q: float, lam: float, mu_through: float, mu_away: float, fee: float, half_spread: float = 0.5,
               adverse: float = 0.2, lot: float = 100.0, n: int = 20000, seed: int = 0) -> dict:
    """Competing exponential clocks: the queue ahead plus our lot is consumed at rate lam; the level is swept at rate
    mu_through or abandoned at rate mu_away, whichever first."""
    rng = np.random.default_rng(seed)
    t_fill = rng.gamma(shape=max((Q + lot) / lot, 1.0), scale=lot / lam, size=n)   # our lot filled by flow
    t_sweep = rng.exponential(1.0 / mu_through, n)
    t_away = rng.exponential(1.0 / mu_away, n)
    by_flow = (t_fill < t_sweep) & (t_fill < t_away)
    by_sweep = (t_sweep < t_fill) & (t_sweep < t_away)
    filled = by_flow | by_sweep
    gross = np.where(by_flow, half_spread - adverse, np.where(by_sweep, half_spread - 1.0, 0.0))
    edge = gross - np.where(filled, fee, 0.0)
    p = float(filled.mean())
    return {"fill_prob": p, "sweep_share": float(by_sweep.sum() / max(filled.sum(), 1)),
            "edge_per_fill": float(edge[filled].mean()) if filled.any() else 0.0, "edge_per_order": float(edge.mean()),
            "time_to_fill": float(np.minimum(t_fill, t_sweep)[filled].mean()) if filled.any() else math.inf}


def monthly_bill(s: fs.Schedule, adav: float, tcv: float, days: int = 21) -> float:
    return days * adav * s.add_rate(adav, tcv)


def marginal_fee(s: fs.Schedule, adav: float, tcv: float, step: float = 1000.0) -> float:
    """Cents a share of the change in the daily passive bill for `step` more shares added a day."""
    return (s.daily_bill(adav + step, 0.0, tcv) - s.daily_bill(adav, 0.0, tcv)) / step


def chase(s: fs.Schedule, natural: float, tcv: float, days_left: int, days: int = 21, loss: float = 0.3) -> dict:
    """Natural added volume `natural` a day all month. To reach the next tier's average by month end the member adds
    extra volume only on the days left, at `loss` cents a share (before fees). Gain: the better rate on every share
    added all month, plus the rate earned on the extra shares."""
    nxt = s.next_tier(natural, tcv)
    if nxt is None:
        return {"extra_per_day": 0.0, "gain": 0.0, "cost": 0.0, "pays": False}
    need_total = max(nxt.min_adav_share * tcv * days - natural * days, 0.0)
    extra = need_total / max(days_left, 1)
    now = -days * natural * s.add_rate(natural, tcv)
    then = -(days * natural + need_total) * nxt.add_rate
    gain = then - now
    cost = need_total * loss
    return {"extra_per_day": extra, "gain": gain, "cost": cost, "pays": gain > cost, "net": gain - cost}


def last_day_to_chase(s: fs.Schedule, natural: float, tcv: float, days: int = 21, loss: float = 0.3,
                      max_share_of_tcv: float = 0.002) -> int | None:
    """The latest trading day (1..days) on which the member can still start chasing: the extra a day must stay under
    `max_share_of_tcv` of consolidated volume (what the market can absorb from it) and the chase must pay."""
    best = None
    for d in range(1, days + 1):
        c = chase(s, natural, tcv, days - d + 1, days, loss)
        if c["pays"] and c["extra_per_day"] <= max_share_of_tcv * tcv:
            best = d
    return best
