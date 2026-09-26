"""firm.futmm -- futures market making: pro-rata books and implied prices (One Quant Book 11, chapter 15).

Built on firm.match (Book 1): its pro-rata allocation and its implied-in and implied-out prices.

The over-quoting game: n makers rest at the best price of a pro-rata book; an aggressor of X lots (random, heavy
tailed) arrives and each maker receives s_i * min(X, S) / S, S the total shown. A maker earns `h` per lot filled
and pays gamma/2 per squared lot of inventory. Under time priority it would show the size it wants filled; under
pro rata it shows more, because its share depends on its size relative to the others'.

API (stable):
    fills(s, X)                                    continuous pro-rata fills of sizes s against aggressor sizes X
    utility(s_i, s_others, X, h, gamma)            mean of h f - gamma/2 f^2 for one maker
    best_response(s_others, X, h, gamma, grid)     the size maximising utility against the others' total
    equilibrium(n, X, h, gamma, grid, iters)       symmetric equilibrium size by best-response iteration
    fifo_size(X, h, gamma, grid)                   the size a maker first in a time-priority queue would show
    aggressors(n, seed, median, sigma)             lognormal aggressor sizes
    Strip(n_contracts, seed, ...)                  outright and calendar-spread books over time; spread books'
                                                   quotes lag the outrights by `lag` steps
    scan(strip)                                    implied-price arbitrages between spread and outright books
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "match"))
import firm_match as fm  # noqa: E402


def fills(s, X) -> np.ndarray:
    """Each maker's fill for each aggressor: s_i * min(X, S) / S (rows: aggressors)."""
    s = np.asarray(s, float)
    S = s.sum()
    return np.minimum(np.asarray(X, float), S)[:, None] * (s / S)[None, :]


def utility(s_i: float, s_others: float, X, h: float, gamma: float) -> float:
    S = s_i + s_others
    f = np.minimum(np.asarray(X, float), S) * (s_i / S)
    return float(np.mean(h * f - 0.5 * gamma * f * f))


def best_response(s_others: float, X, h: float, gamma: float, grid) -> float:
    g = np.asarray(grid, float)[None, :]
    X = np.asarray(X, float)[:, None]
    f = np.minimum(X, g + s_others) * g / (g + s_others)
    u = np.mean(h * f - 0.5 * gamma * f * f, axis=0)
    return float(grid[int(np.argmax(u))])


def equilibrium(n: int, X, h: float, gamma: float, grid, iters: int = 80) -> float:
    """Symmetric equilibrium on the grid: damped best-response iteration; the grid's top is the exchange's maximum
    order size, where the spiral stops if nothing else does."""
    s = float(grid[len(grid) // 4])
    for _ in range(iters):
        new = best_response((n - 1) * s, X, h, gamma, grid)
        if abs(new - s) < 1e-9:
            break
        s = 0.5 * (s + new)
    return s


def fifo_size(X, h: float, gamma: float, grid) -> float:
    X = np.asarray(X, float)
    u = [float(np.mean(h * np.minimum(X, g) - 0.5 * gamma * np.minimum(X, g) ** 2)) for g in grid]
    return float(grid[int(np.argmax(u))])


def aggressors(n: int = 20000, seed: int = 0, median: float = 200.0, sigma: float = 1.2) -> np.ndarray:
    return np.random.default_rng(seed).lognormal(np.log(median), sigma, n)


class Strip:
    """`n_contracts` quarterly futures in ticks: a common level plus a curve slope, each outright's book one tick wide
    (bid the value's floor). The spread books (each contract against the next) are quoted one tick wide by market
    makers around the outrights' value difference as it was `lag` steps earlier."""

    def __init__(self, n_contracts: int = 4, steps: int = 20000, seed: int = 0, lag: int = 3, level_vol: float = 0.6,
                 slope_vol: float = 0.4, qty: int = 100):
        rng = np.random.default_rng(seed)
        lvl = np.cumsum(rng.standard_normal(steps) * level_vol)
        slope = np.cumsum(rng.standard_normal(steps) * slope_vol)
        k = np.arange(n_contracts)
        self.value = 9600.0 + lvl[:, None] + slope[:, None] * k[None, :] / max(n_contracts - 1, 1)
        self.n, self.steps, self.lag, self.qty = n_contracts, steps, lag, qty

    def outright(self, t: int, i: int) -> fm.Quote:
        b = int(np.floor(self.value[t, i]))
        return fm.Quote(b, self.qty, b + 1, self.qty)

    def spread(self, t: int, i: int) -> fm.Quote:
        u = max(t - self.lag, 0)
        b = int(np.floor(self.value[u, i] - self.value[u, i + 1] - 0.5))
        return fm.Quote(b, self.qty, b + 1, self.qty)


def scan(strip: Strip) -> dict:
    """Count steps where a spread book's direct bid is above the spread implied by the outrights' offers
    (sell the spread, buy the front, sell the back), or its direct offer below the implied bid; edge in ticks."""
    n, edge = 0, []
    for t in range(strip.steps):
        for i in range(strip.n - 1):
            direct = strip.spread(t, i)
            imp = fm.implied_in(strip.outright(t, i), strip.outright(t, i + 1))
            if direct.bid > imp.ask:
                n += 1
                edge.append(direct.bid - imp.ask)
            elif direct.ask < imp.bid:
                n += 1
                edge.append(imp.bid - direct.ask)
    return {"count": n, "per_1000": 1000.0 * n / (strip.steps * (strip.n - 1)),
            "mean_edge": float(np.mean(edge)) if edge else 0.0}
