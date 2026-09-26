"""firm.mmhedge -- hedging a market maker's inventory in practice (One Quant Book 11, chapter 11).

A one-factor book: name i has price p_i, beta b_i to a common factor that the index future tracks, and idiosyncratic
volatility s_i (all volatilities are daily, returns are arithmetic over a day). The market maker's inventory q_i
comes from client fills; it can sell the future (cheap, removes only the factor risk), trade the single stocks
(dearer, removes everything), or keep the risk.

API (stable):
    delta_equivalent(q, p, beta) -> float        sum_i q_i p_i b_i: dollars of index exposure
    book_var(q, p, beta, sf, se, hedge=0.0)      daily variance of the book after selling `hedge` dollars of future
    choose(q, p, beta, sf, se, c_fut, c_stk, lam, horizon)
                                                 'none' | 'future' | 'stocks' by cost + lam * variance over horizon
    partial_hedge(D, c, lam, var)                argmin_h c|h| + lam var (D - h)^2 (soft threshold)
    FlowDay(n, seed, ...)                        a simulated day of client fills across n names with a common factor
    FlowDay.inventory(stock_band, c_stk, eod_from, eod_skew)
                                                 per-step inventories, single-stock hedge costs if a band is set, and
                                                 a harder skew from eod_from (flattening through the quotes)
    hedge_future(D, rule, band, notional, c)     the future position under 'none' | 'zero' | 'band', and its cost
    day_pnl(day, policy, ..., **eod) -> dict     spread, hedge cost, inventory P&L, intraday risk, end-of-day book
    overnight(q, p, beta, sf, se, hedge, n, seed, df) -> losses
                                                 overnight loss draws of a kept book (Student-t gaps)
    flatten_cost(q, p, half_spread, eta, adv, minutes)
                                                 cost of end-of-day flattening: half-spread plus square-root impact
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "impulse"))
import firm_impulse as imp  # noqa: E402


def delta_equivalent(q, p, beta) -> float:
    return float(np.sum(np.asarray(q) * np.asarray(p) * np.asarray(beta)))


def book_var(q, p, beta, sf: float, se, hedge: float = 0.0) -> float:
    x = np.asarray(q) * np.asarray(p)
    d = float(np.sum(x * np.asarray(beta))) - hedge
    return d * d * sf * sf + float(np.sum((x * np.asarray(se)) ** 2))


def choose(q, p, beta, sf, se, c_fut: float, c_stk: float, lam: float, horizon: float = 1.0) -> dict:
    """Hedge-instrument choice for a book held over `horizon` days: cost plus lam times the variance left.
    c_fut and c_stk are costs per dollar traded (half-spread plus fees)."""
    x = np.asarray(q) * np.asarray(p)
    d = delta_equivalent(q, p, beta)
    out = {"none": lam * horizon * book_var(q, p, beta, sf, se),
           "future": c_fut * abs(d) + lam * horizon * book_var(q, p, beta, sf, se, hedge=d),
           "stocks": c_stk * float(np.sum(np.abs(x)))}
    out["best"] = min(("none", "future", "stocks"), key=out.get)
    return out


def partial_hedge(D: float, c: float, lam: float, var: float) -> float:
    """Minimise c |h| + lam var (D - h)^2: hedge down to the edge of a dead zone of half-width c / (2 lam var)."""
    z = c / (2.0 * lam * var)
    return math.copysign(max(abs(D) - z, 0.0), D)


class FlowDay:
    """Client fills across n names over one session, in steps of `dt` seconds.

    Each name trades `rate` fills a second of `lot` shares; the market maker earns `half_spread` dollars a share on
    each. The chance that a fill makes it long falls with its inventory (the quotes skew: `skew` per `qscale` shares)
    and rises after the factor falls (clients sell into a falling market: `tilt` per standard deviation of the
    last minute's factor return). Prices follow the one-factor model."""

    def __init__(self, n: int = 40, seed: int = 0, T: float = 23400.0, dt: float = 5.0, sf: float = 0.01,
                 rate: float = 0.05, lot: int = 100, half_spread: float = 0.01, skew: float = 0.25,
                 qscale: float = 2000.0, tilt: float = 0.15):
        rng = np.random.default_rng(seed)
        prm = np.random.default_rng(1000)          # the names are the same every day
        self.n, self.T, self.dt, self.sf, self.lot, self.hs = n, T, dt, sf, lot, half_spread
        self.p0 = prm.uniform(20.0, 150.0, n)
        self.beta = prm.uniform(0.6, 1.4, n)
        self.se = prm.uniform(0.01, 0.02, n)
        self.m = int(round(T / dt))
        sd = math.sqrt(dt / T)
        self.f = rng.standard_normal(self.m) * sf * sd                       # factor return per step
        self.e = rng.standard_normal((self.m, n)) * self.se * sd             # idiosyncratic returns
        self.p = self.p0 * np.cumprod(1.0 + self.beta * self.f[:, None] + self.e, axis=0)
        self.fills = rng.poisson(rate * dt, (self.m, n))
        self.u = rng.random((self.m, n, int(self.fills.max()) + 1))
        k = max(1, int(round(60.0 / dt)))
        c = np.concatenate([[0.0], np.cumsum(self.f)])
        self.z = (c[k:] - c[:-k]) / (sf * math.sqrt(k * dt / T))
        self.z = np.concatenate([np.zeros(k - 1), self.z])[: self.m]
        self.skew, self.qscale, self.tilt = skew, qscale, tilt

    def inventory(self, stock_band: float | None = None, c_stk: float = 0.0, eod_from: float | None = None,
                  eod_skew: float = 1.0):
        """Inventories after each step; with `stock_band` (dollars), a name whose position exceeds the band is
        traded back to the band's edge in the stock itself at c_stk per dollar; from `eod_from` seconds into the
        session the quotes skew `eod_skew` times harder (flattening through the quotes)."""
        q = np.zeros(self.n)
        out = np.empty((self.m, self.n))
        nfill = np.zeros(self.n)
        cost = 0.0
        K = self.u.shape[2]
        slot = np.arange(K)[None, :]
        t0 = self.m if eod_from is None else int(round(eod_from / self.dt))
        for t in range(self.m):
            sk = self.skew * (eod_skew if t >= t0 else 1.0)
            pb = np.clip(0.5 - sk * q / self.qscale - self.tilt * self.z[t], 0.02, 0.98)
            k = self.fills[t]
            nb = ((self.u[t] < pb[:, None]) & (slot < k[:, None])).sum(axis=1)
            q = q + self.lot * (2 * nb - k)
            nfill += k
            if stock_band is not None:
                x = q * self.p[t]
                over = np.abs(x) > stock_band
                if over.any():
                    tgt = np.sign(x[over]) * stock_band / self.p[t][over]
                    cost += c_stk * float(np.sum(np.abs(q[over] - tgt) * self.p[t][over]))
                    q[over] = tgt
            out[t] = q
        return out, nfill, cost


def hedge_future(D, rule: str, band: float = 0.0, notional: float = 50000.0, c: float = 0.00005):
    """Future position (dollars, sold against a long exposure) along a path of delta-equivalent exposures D.
    'zero' keeps the unhedged exposure within half a contract; 'band' trades back to +-band when |D - H| > band.
    Returns (H path, cost in dollars, contracts traded)."""
    H = np.zeros(len(D))
    h, cost, traded = 0.0, 0.0, 0
    for t, d in enumerate(D):
        x = d - h
        if rule == "zero" and abs(x) > 0.5 * notional:
            k = int(round(x / notional))
        elif rule == "band" and abs(x) > band + 0.5 * notional:
            k = int(round((x - math.copysign(band, x)) / notional))
        else:
            k = 0
        if k:
            h += k * notional
            cost += c * abs(k) * notional
            traded += abs(k)
        H[t] = h
    return H, cost, traded


def day_pnl(day: FlowDay, policy: str, band: float = 0.0, notional: float = 50000.0, c_fut: float = 0.00005,
            stock_band: float = 20000.0, c_stk: float = 0.00017, **eod) -> dict:
    """One day under a policy: 'none', 'future zero', 'future band', 'stocks'. Inventory P&L is marked every step
    on the stocks' and the factor's returns; intraday risk is the standard deviation of the one-minute P&L."""
    if policy == "stocks":
        Q, nfill, hc = day.inventory(stock_band=stock_band, c_stk=c_stk, **eod)
        H = np.zeros(day.m)
        traded = 0
    else:
        Q, nfill, hc = day.inventory(**eod)
        D = np.sum(Q * day.p * day.beta, axis=1)
        rule = {"none": "none", "future zero": "zero", "future band": "band"}[policy]
        H, hc, traded = hedge_future(D, rule, band, notional, c_fut)
    r = day.beta * day.f[:, None] + day.e                     # return over each step
    x = Q[:-1] * day.p[:-1]
    step = np.sum(x * r[1:], axis=1) - H[:-1] * day.f[1:]
    k = max(1, int(round(60.0 / day.dt)))
    mins = step[: (len(step) // k) * k].reshape(-1, k).sum(axis=1)
    spread = float(np.sum(nfill) * day.lot * day.hs)
    return {"spread": spread, "hedge_cost": hc, "inventory": float(np.sum(step)), "contracts": traded,
            "total": spread - hc + float(np.sum(step)), "risk_min": float(np.std(mins)),
            "q_end": Q[-1].copy(), "p_end": day.p[-1].copy(), "D_end": float(np.sum(Q[-1] * day.p[-1] * day.beta)),
            "H_end": float(H[-1])}


def overnight(q, p, beta, sf: float, se, hedge: float = 0.0, n: int = 100000, seed: int = 0,
              df: float = 4.0) -> np.ndarray:
    """Overnight losses (positive = loss) of a book kept to the open: factor and idiosyncratic gaps are Student-t
    with `df` degrees of freedom scaled to standard deviations sf and se."""
    rng = np.random.default_rng(seed)
    s = math.sqrt((df - 2.0) / df)
    x = np.asarray(q) * np.asarray(p)
    f = rng.standard_t(df, n) * sf * s
    e = rng.standard_t(df, (n, len(x))) * np.asarray(se) * s
    pnl = (float(np.sum(x * np.asarray(beta))) - hedge) * f + e @ x
    return -pnl


def flatten_cost(q, p, half_spread: float = 0.01, eta: float = 0.1, adv=None, sigma=0.015, minutes: float = 10.0,
                 day_minutes: float = 390.0) -> float:
    """Half-spread on every share plus square-root impact eta * sigma * sqrt(Q / V) on a traded value, V the
    volume traded in the window (adv * minutes / day_minutes)."""
    q, p = np.abs(np.asarray(q, float)), np.asarray(p, float)
    adv = np.full(len(q), 2_000_000.0) if adv is None else np.asarray(adv, float)
    v = adv * minutes / day_minutes
    impact = eta * np.asarray(sigma) * np.sqrt(q / v)
    return float(np.sum(q * half_spread) + np.sum(q * p * impact))


def optimal_band(sigma_D: float, lam: float, sf: float, c: float) -> float:
    """No-trade band on the delta-equivalent exposure with a proportional cost c per dollar: firm.impulse's
    reflected-band optimum with risk charge gamma = lam sf^2 per day and exposure volatility sigma_D per day."""
    return imp.optimal_proportional_band(sigma_D, lam * sf * sf, c)[0]
