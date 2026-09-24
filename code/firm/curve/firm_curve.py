"""Single-curve OIS bootstrap and swap pricing (build of Book 2, Chapter 9).

Swaps pay annually on both legs, actual/360, from a spot date (no business-day adjustment in this
teaching version). In a single-curve world the compounded overnight leg of a period is worth
P(t_{i-1}) - P(t_i), so the floating leg telescopes to P(start) - P(end). Discount factors are
interpolated log-linearly in time between pillars. Rates are decimals.
"""
import datetime as dt
import math
from dataclasses import dataclass


def add_years(d: dt.date, n: int) -> dt.date:
    try:
        return d.replace(year=d.year + n)
    except ValueError:                        # 29 February
        return d.replace(year=d.year + n, day=28)


@dataclass
class Curve:
    spot: dt.date
    times: list[float]              # pillar times in years (actual/365)
    dfs: list[float]                # discount factors at the pillars

    def t(self, d: dt.date) -> float:
        return (d - self.spot).days / 365.0

    def df(self, d: dt.date) -> float:
        x = self.t(d)
        if x <= 0:
            return 1.0
        ts, ls = [0.0] + self.times, [0.0] + [math.log(p) for p in self.dfs]
        if x >= ts[-1]:                       # flat forward beyond the last pillar
            slope = (ls[-1] - ls[-2]) / (ts[-1] - ts[-2])
            return math.exp(ls[-1] + slope * (x - ts[-1]))
        k = next(i for i in range(1, len(ts)) if x <= ts[i])
        w = (x - ts[k - 1]) / (ts[k] - ts[k - 1])
        return math.exp(ls[k - 1] + w * (ls[k] - ls[k - 1]))

    def zero(self, d: dt.date) -> float:
        """Continuously compounded zero rate to d."""
        return -math.log(self.df(d)) / self.t(d)


def schedule(start: dt.date, years: int) -> list[dt.date]:
    return [add_years(start, k) for k in range(years + 1)]


def annuity(curve: Curve, dates: list[dt.date]) -> float:
    """Sum of accrual fraction times discount factor over the fixed leg (actual/360)."""
    return sum((b - a).days / 360.0 * curve.df(b) for a, b in zip(dates, dates[1:], strict=False))


def par_rate(curve: Curve, dates: list[dt.date]) -> float:
    return (curve.df(dates[0]) - curve.df(dates[-1])) / annuity(curve, dates)


def swap_pv(curve: Curve, dates: list[dt.date], fixed: float, notional: float, payer: bool = True) -> float:
    """Value to the payer of fixed (receiver of floating), or the reverse."""
    floating = curve.df(dates[0]) - curve.df(dates[-1])
    v = notional * (floating - fixed * annuity(curve, dates))
    return v if payer else -v


def bootstrap(spot: dt.date, tenors: list[int], rates: list[float]) -> Curve:
    """Pillars at the swaps' maturities; each pillar's discount factor solved so that its swap
    reprices at par, earlier pillars fixed (bisection on the log discount factor)."""
    curve = Curve(spot, [], [])
    for n, r in zip(tenors, rates, strict=True):
        end = add_years(spot, n)
        curve.times.append(curve.t(end))
        curve.dfs.append(1.0)
        lo, hi = -1.0, 0.0                    # bounds on log(df)
        dates = schedule(spot, n)
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            curve.dfs[-1] = math.exp(mid)
            if par_rate(curve, dates) > r:    # df too low -> par rate too high -> raise df
                lo = mid
            else:
                hi = mid
        curve.dfs[-1] = math.exp(0.5 * (lo + hi))
    return curve


def bucket_dv01(spot: dt.date, tenors: list[int], rates: list[float], dates: list[dt.date],
                fixed: float, notional: float, payer: bool = True, bump: float = 1e-4) -> list[float]:
    """Change in value for a one-basis-point rise of each par input in turn (rebuild the curve)."""
    base = swap_pv(bootstrap(spot, tenors, rates), dates, fixed, notional, payer)
    out = []
    for k in range(len(rates)):
        bumped = [r + (bump if i == k else 0.0) for i, r in enumerate(rates)]
        out.append(swap_pv(bootstrap(spot, tenors, bumped), dates, fixed, notional, payer) - base)
    return out
