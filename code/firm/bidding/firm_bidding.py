"""firm.bidding -- auction simulator of the miniature firm (One Quant Book 4, chapter 29).

Symmetric independent private values drawn from a distribution on [0, 1] (uniform by default). Single-unit formats:
first-price (sealed, pay your bid), second-price (sealed, pay the second-highest bid), English (ascending clock) and
Dutch (descending clock), each with an optional reserve price; multi-unit formats with unit demand: uniform-price and
pay-as-bid (discriminatory). Equilibrium bid functions for the symmetric cases, revenue and efficiency statistics, a
Myerson reserve-price solver, and a common-value experiment that shows the winner's curse.

API (stable):
    fp_bid(v, n, reserve=0.0)                       first-price equilibrium bid, uniform values
    fp_bid_general(v, n, cdf, grid=2001)             first-price equilibrium bid for any value cdf on [0, 1]
    pab_bid(v, n, k)                                 pay-as-bid equilibrium bid with unit demand, uniform values
    simulate(fmt, n, n_auctions, seed, reserve=0.0, increment=0.0, values=None) -> dict
    simulate_multiunit(fmt, n, k, n_auctions, seed) -> dict
    expected_revenue_uniform(n, reserve=0.0)         closed form, second-price with reserve, uniform values
    myerson_reserve(cdf, pdf, seller_value=0.0)      root of r - (1 - F(r)) / f(r) = seller_value
    common_value(n, n_auctions, seed, noise, shade)  winners' average profit when bidding on signals
"""
from __future__ import annotations

import math

import numpy as np


def fp_bid(v, n: int, reserve: float = 0.0):
    """b(v) = v - (v^n - r^n) / (n v^(n-1)) for v >= r (uniform values); bidders below the reserve do not bid."""
    v = np.asarray(v, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        b = v - (v**n - reserve**n) / (n * v ** (n - 1))
    return np.where(v >= reserve, b, np.nan)


def fp_bid_general(v, n: int, cdf, grid: int = 2001):
    """b(v) = v - int_0^v F(x)^(n-1) dx / F(v)^(n-1), by the trapezoidal rule on a grid of [0, v]."""
    out = []
    for vi in np.atleast_1d(np.asarray(v, dtype=float)):
        x = np.linspace(0.0, vi, grid)
        Fx = np.asarray(cdf(x), dtype=float) ** (n - 1)
        integral = float(np.sum(0.5 * (Fx[1:] + Fx[:-1]) * np.diff(x)))
        Fv = float(cdf(vi)) ** (n - 1)
        out.append(vi - integral / Fv if Fv > 0 else 0.0)
    return np.array(out)


def pab_bid(v, n: int, k: int, grid: int = 4001):
    """Pay-as-bid with k units and n unit-demand bidders: b(v) = E[Y | Y < v], Y the k-th highest of the other
    n - 1 values (uniform)."""
    out = []
    for vi in np.atleast_1d(np.asarray(v, dtype=float)):
        y = np.linspace(0.0, vi, grid)
        m = n - 1
        # density of the k-th highest of m uniforms: m C(m-1, k-1) y^(m-k) (1-y)^(k-1)
        dens = m * math.comb(m - 1, k - 1) * y ** (m - k) * (1 - y) ** (k - 1)
        num = float(np.sum(0.5 * ((y * dens)[1:] + (y * dens)[:-1]) * np.diff(y)))
        den = float(np.sum(0.5 * (dens[1:] + dens[:-1]) * np.diff(y)))
        out.append(num / den if den > 0 else 0.0)
    return np.array(out)


def simulate(fmt: str, n: int, n_auctions: int, seed: int, reserve: float = 0.0, increment: float = 0.0,
             values=None) -> dict:
    """Revenue, efficiency and bid shading of a single-unit auction format with symmetric equilibrium bidding.
    fmt in {"first", "second", "english", "dutch"}; `values` overrides the uniform draws (shape (n_auctions, n))."""
    rng = np.random.default_rng(seed)
    V = rng.uniform(size=(n_auctions, n)) if values is None else np.asarray(values, dtype=float)
    order = np.sort(V, axis=1)
    top, second = order[:, -1], order[:, -2]
    sold = top >= reserve
    if fmt in ("first", "dutch"):
        price = fp_bid(top, n, reserve)
        if fmt == "dutch" and increment > 0:          # the clock stops at the first tick at or below the bid
            price = np.floor(price / increment) * increment
    elif fmt in ("second", "english"):
        price = np.maximum(second, reserve)
        if fmt == "english" and increment > 0:        # the clock stops one tick after the second-last drops out
            price = np.maximum(np.ceil(second / increment) * increment, reserve)
    else:
        raise ValueError(fmt)
    revenue = np.where(sold, price, 0.0)
    shading = np.where(sold, 1 - fp_bid(top, n, reserve) / top, np.nan) if fmt in ("first", "dutch") else None
    return {"revenue": float(revenue.mean()), "revenue_se": float(revenue.std(ddof=1) / math.sqrt(n_auctions)),
            "efficiency": float(np.mean(sold)), "sold": float(sold.mean()),
            "shading": float(np.nanmean(shading)) if shading is not None else 0.0, "values": V}


def simulate_multiunit(fmt: str, n: int, k: int, n_auctions: int, seed: int) -> dict:
    """k identical units, n bidders with unit demand and uniform values. 'uniform': bids equal values (weakly
    dominant with unit demand), every winner pays the (k+1)-th highest bid; 'payasbid': equilibrium bids, winners
    pay their own bids."""
    rng = np.random.default_rng(seed)
    V = rng.uniform(size=(n_auctions, n))
    order = np.sort(V, axis=1)
    if fmt == "uniform":
        revenue = k * order[:, n - k - 1]
        bids = V
    elif fmt == "payasbid":
        grid = np.linspace(0.0, 1.0, 2001)
        table = pab_bid(grid, n, k)
        bids = np.interp(V, grid, table)
        revenue = np.sort(bids, axis=1)[:, n - k:].sum(axis=1)
    else:
        raise ValueError(fmt)
    winners = np.sort(bids, axis=1)[:, n - k:]
    spread = winners.max(axis=1) - winners.min(axis=1)
    return {"revenue": float(revenue.mean()), "revenue_se": float(revenue.std(ddof=1) / math.sqrt(n_auctions)),
            "revenue_sd": float(revenue.std(ddof=1)), "winning_bid_spread": float(spread.mean())}


def expected_revenue_uniform(n: int, reserve: float = 0.0) -> float:
    """Second-price (or any standard format) revenue with uniform values and reserve r:
    (n - 1)/(n + 1) - 2 n r^(n+1)/(n + 1) + r^n."""
    return (n - 1) / (n + 1) - 2 * n * reserve ** (n + 1) / (n + 1) + reserve**n


def myerson_reserve(cdf, pdf, seller_value: float = 0.0, lo: float = 1e-9, hi: float = 1.0 - 1e-9) -> float:
    """Optimal reserve: the root of the virtual value r - (1 - F(r))/f(r) = seller value (regular distributions)."""
    def g(r):
        return r - (1 - cdf(r)) / pdf(r) - seller_value
    a, b = lo, hi
    for _ in range(200):
        m = 0.5 * (a + b)
        if g(a) * g(m) <= 0:
            b = m
        else:
            a = m
    return 0.5 * (a + b)


def common_value(n: int, n_auctions: int, seed: int, noise: float = 0.1, shade: float = 0.0) -> dict:
    """V ~ U[0, 1] common to all; bidder i sees s_i = V + e_i, e_i ~ U[-noise, noise]; each bids s_i - shade in a
    first-price auction. Returns the winners' average profit V - bid and the probability of a loss."""
    rng = np.random.default_rng(seed)
    V = rng.uniform(size=n_auctions)
    S = V[:, None] + rng.uniform(-noise, noise, size=(n_auctions, n))
    win = S.max(axis=1) - shade
    profit = V - win
    return {"profit": float(profit.mean()), "p_loss": float(np.mean(profit < 0)),
            "profit_se": float(profit.std(ddof=1) / math.sqrt(n_auctions))}
