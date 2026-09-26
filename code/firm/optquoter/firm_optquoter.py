"""firm.optquoter -- automated options market making: live surface, mass quotes, protection (One Quant Book 11, ch. 19).

Built on Book 5's firm.optmm (theoretical values and vegas on a firm.volpnl.SkewSurface), firm.svi (the slice fit)
and firm.bs. A chain of calls and puts across strikes and expiries is quoted at once (a mass quote: one message per
side per series); an exchange-side protection counts the market maker's executions in a window and cancels all its
quotes in the class when a threshold is reached.

API (stable):
    Chain(spot, strikes, expiries_days)              the listed series
    surface(atm=..., skew=...)                       a firm.volpnl.SkewSurface
    mass_quote(chain, spot, surf, half_width_vol, size)
                                                     per series: theo, vega, delta, bid, ask (per share)
    refit_slice(strikes, spot, tau, vols)            SVI fit of one expiry's implied vols (firm.svi), and its RMS error
    Protection(count, window_ms)                     cancel-all after `count` executions within `window_ms`
    sweep(quotes, jump, chain, surf, protection, gap_us, size, dvol, vega_limit, react_us)
                                                     an informed sweep after the underlying (or the volatility) jumps:
                                                     which quotes fill before the exchange's protection or the market
                                                     maker's per-expiry vega limit stops it, and the loss (dollars)
    normal_day(quotes, protection, seed, hours, rate, legs, requote_ms, edge)
                                                     uninformed orders over a day: fills, fills given up while the
                                                     protection has pulled the quotes, and the edge given up
    bucket_vega(quotes, fills, chain)                vega by expiry of a set of fills
"""
from __future__ import annotations

import math
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

FIRM = pathlib.Path(__file__).resolve().parents[1]
for comp in ("optmm", "volpnl", "bs", "svi"):
    sys.path.insert(0, str(FIRM / comp))
import firm_optmm as om  # noqa: E402
import firm_svi as fsvi  # noqa: E402
from firm_bs import greeks  # noqa: E402
from firm_volpnl import Option, SkewSurface  # noqa: E402

MULT = 100


@dataclass
class Chain:
    spot: float = 100.0
    strikes: tuple = tuple(np.arange(80.0, 120.01, 2.5))
    expiries_days: tuple = (7, 14, 30, 60, 90)

    def series(self) -> list[Option]:
        out = []
        for d in self.expiries_days:
            for k in self.strikes:
                for right in ("C", "P"):
                    out.append(Option(float(k), d / 365.0, right, 1.0))
        return out


def surface(atm: float = 0.25, term: float = 0.02, skew: float = -0.08, ref: float | None = 100.0) -> SkewSurface:
    return SkewSurface(lambda tau: atm + term * math.sqrt(tau), skew, ref)


def mass_quote(chain: Chain, spot: float, surf: SkewSurface, half_width_vol: float = 0.005,
               size: int = 10) -> list[dict]:
    """Bid and ask at theo -+ half_width_vol vol points times vega (floor one cent), for every series."""
    out = []
    for o in chain.series():
        th, vega = om.theo(o, spot, 0.0, surf)
        tau = o.expiry
        g = greeks(spot, o.strike, tau, 0.0, 0.0, surf.vol(o.strike, tau, spot), o.right)
        hw = max(half_width_vol * 100.0 * vega, 0.01)
        out.append({"opt": o, "theo": th, "vega": vega, "delta": g["delta"], "bid": max(th - hw, 0.0), "ask": th + hw,
                    "size": size})
    return out


def refit_slice(strikes, spot: float, tau: float, vols) -> tuple[tuple, float]:
    k = np.log(np.asarray(strikes, float) / spot)
    w = np.asarray(vols, float) ** 2 * tau
    params, _ = fsvi.fit_svi(k, w)
    fit = np.sqrt(np.maximum(fsvi.svi(k, *params), 0.0) / tau)
    return params, float(np.sqrt(np.mean((fit - np.asarray(vols)) ** 2)))


@dataclass
class Protection:
    count: int = 10**9
    window_ms: float = 100.0


def sweep(quotes: list[dict], jump: float, chain: Chain, surf: SkewSurface, protection: Protection, gap_us: float = 5.0,
          size: int | None = None, dvol: float = 0.0, vega_limit: float | None = None, react_us: float = 50.0) -> dict:
    """The underlying moves by `jump` (relative) and implied volatility by `dvol` before the market maker updates. An
    informed trader hits every quote now mispriced (buys asks below the new theo, sells bids above it), most
    profitable first, one series every `gap_us` microseconds. The exchange cancels all remaining quotes once
    `protection.count` executions have occurred within its window; the market maker's own per-expiry vega limit, if
    set, cancels an expiry's quotes `react_us` after the fill that breaches it."""
    s1 = chain.spot * (1.0 + jump)
    s_new = SkewSurface(lambda tau, f=surf.atm: f(tau) + dvol, surf.skew, surf.ref)
    targets = []
    for q in quotes:
        new, _ = om.theo(q["opt"], s1, 0.0, s_new)
        if new > q["ask"]:
            targets.append((new - q["ask"], q, new, +1))
        elif new < q["bid"]:
            targets.append((q["bid"] - new, q, new, -1))
    targets.sort(key=lambda x: -x[0])
    fills, loss, delta, vega = 0, 0.0, 0.0, 0.0
    by_exp: dict[float, float] = {}
    closed_at: dict[float, float] = {}
    for i, (edge, q, _new, side) in enumerate(targets):
        t_us = i * gap_us
        if fills >= protection.count and t_us / 1000.0 <= protection.window_ms:
            break
        e = q["opt"].expiry
        if e in closed_at and t_us >= closed_at[e]:
            continue
        n = q["size"] if size is None else size
        fills += 1
        loss += edge * n * MULT
        delta += -side * q["delta"] * n * MULT                 # the market maker is on the other side
        v = -side * q["vega"] * n * MULT
        vega += v
        by_exp[e] = by_exp.get(e, 0.0) + v
        if vega_limit is not None and abs(by_exp[e]) > vega_limit and e not in closed_at:
            closed_at[e] = t_us + react_us
    return {"targets": len(targets), "fills": fills, "loss": loss, "delta_shares": delta, "vega_dollars": vega,
            "max_loss": sum(t[0] * (t[1]["size"] if size is None else size) * MULT for t in targets),
            "vega_by_expiry": {round(k * 365): v for k, v in sorted(by_exp.items())}}


def normal_day(n_series: int, protection: Protection, seed: int = 0, hours: float = 6.5, rate: float = 0.2,
               legs=(1, 2, 4, 12), leg_p=(0.70, 0.18, 0.09, 0.03), requote_ms: float = 500.0, edge: float = 4.0,
               burst_ms: float = 2.0) -> dict:
    """Uninformed orders arrive at `rate` a second; each executes against `legs` series (a spread or a strip order)
    within `burst_ms`. If an order's legs bring the count in the window to the threshold, the exchange pulls every
    quote and the market maker is out for `requote_ms`; orders arriving then are lost. Edge in dollars a fill."""
    rng = np.random.default_rng(seed)
    T = hours * 3600.0
    t, times = 0.0, []
    while True:
        t += rng.exponential(1.0 / rate)
        if t >= T:
            break
        times.append(t)
    k = rng.choice(legs, size=len(times), p=leg_p)
    recent: list[float] = []
    out_until = -1.0
    fills = lost = pulls = 0
    for ti, ki in zip(times, k, strict=True):
        if ti < out_until:
            lost += int(ki)
            continue
        recent = [x for x in recent if x > ti - protection.window_ms / 1000.0]
        for j in range(int(ki)):
            recent.append(ti + j * burst_ms / 1000.0)
            fills += 1
            if len(recent) >= protection.count:
                pulls += 1
                out_until = ti + requote_ms / 1000.0
                lost += int(ki) - j - 1
                recent = []
                break
    return {"fills": fills, "lost": lost, "pulls": pulls, "edge_lost": lost * edge, "edge_kept": fills * edge}


def bucket_vega(quotes: list[dict], chain: Chain, sides: dict[int, int]) -> dict:
    """Vega (dollars per vol point) by expiry of fills: {quote index: +1 bought, -1 sold by the market maker}."""
    out = {d: 0.0 for d in chain.expiries_days}
    for i, s in sides.items():
        q = quotes[i]
        out[round(q["opt"].expiry * 365)] += s * q["vega"] * q["size"] * MULT
    return out
