"""Static-arbitrage checker for a chain of European quotes (build of Book 5, Chapter 1).

A quote set is arbitrage-free only if a list of model-free inequalities holds at executable prices
(buy at the ask, sell at the bid). Each check that fails returns the portfolio that exploits it and
its edge: the cash it brings in today while paying nothing negative at expiry. A tiny linear
programme solver by vertex enumeration (exact, for the handful of variables of these problems) is
included, since the series' environment has no optimisation library.
"""
import itertools
import math
from dataclasses import dataclass

import numpy as np


def lp_max(c, a_ub, b_ub, tol: float = 1e-9):
    """Maximise c.x subject to a_ub x <= b_ub (a bounded polytope), by enumerating basic solutions.

    Exact for small problems: every vertex is the solution of n active constraints. Returns
    (value, x) or (None, None) when the polytope is empty."""
    c, a, b = np.asarray(c, float), np.asarray(a_ub, float), np.asarray(b_ub, float)
    n = len(c)
    best, arg = None, None
    for rows in itertools.combinations(range(len(b)), n):
        sub = a[list(rows)]
        if abs(np.linalg.det(sub)) < 1e-12:
            continue
        x = np.linalg.solve(sub, b[list(rows)])
        if np.all(a @ x <= b + tol) and (best is None or c @ x > best + tol):
            best, arg = float(c @ x), x
    return best, arg


@dataclass(frozen=True)
class Quote:
    strike: float
    right: str          # "C" or "P"
    bid: float
    ask: float


@dataclass(frozen=True)
class Violation:
    kind: str           # "bound", "monotone", "slope", "convexity", "box"
    strikes: tuple[float, ...]
    edge: float         # cash received today by the arbitrage portfolio (> 0)
    legs: tuple[tuple[str, float, float], ...]   # (right, strike, quantity); + = buy


def _px(q: Quote, qty: float) -> float:
    """Cash paid for qty of the quote (buy at ask, sell at bid)."""
    return qty * (q.ask if qty > 0 else q.bid)


def check_chain(quotes: list[Quote], forward: float, df: float, tol: float = 1e-9) -> list[Violation]:
    """Model-free checks on one expiry: call bounds, monotonicity, slope, convexity (calls and puts)."""
    out = []
    for right in ("C", "P"):
        qs = sorted((q for q in quotes if q.right == right), key=lambda q: q.strike)
        sign = 1 if right == "C" else -1
        for q in qs:   # lower bound: discounted intrinsic value, upper: df*F (call) or df*K (put)
            lo = df * max(sign * (forward - q.strike), 0.0)
            hi = df * (forward if right == "C" else q.strike)
            if q.ask < lo - tol:   # buy the option, sell the forward exposure: receive lo - ask
                out.append(Violation("bound", (q.strike,), lo - q.ask, ((right, q.strike, 1.0),)))
            if q.bid > hi + tol:
                out.append(Violation("bound", (q.strike,), q.bid - hi, ((right, q.strike, -1.0),)))
        for a, b in zip(qs, qs[1:], strict=False):
            # calls decrease in strike, puts increase: the dearer-by-rule option cannot be cheaper
            dear, cheap = (a, b) if right == "C" else (b, a)
            edge = -(_px(dear, 1.0) + _px(cheap, -1.0))
            if edge > tol:
                out.append(Violation("monotone", (a.strike, b.strike), edge,
                                     ((right, dear.strike, 1.0), (right, cheap.strike, -1.0))))
            # slope: the spread is worth at most df * (K2 - K1)
            spread_bid = -_px(dear, -1.0) - _px(cheap, 1.0)
            edge = spread_bid - df * (b.strike - a.strike)
            if edge > tol:
                out.append(Violation("slope", (a.strike, b.strike), edge,
                                     ((right, dear.strike, -1.0), (right, cheap.strike, 1.0))))
        for a, b, c in zip(qs, qs[1:], qs[2:], strict=False):
            wa, wc = (c.strike - b.strike), (b.strike - a.strike)
            tot = wa + wc
            cost = _px(a, wa / tot) + _px(b, -1.0) + _px(c, wc / tot)
            if cost < -tol:
                out.append(Violation("convexity", (a.strike, b.strike, c.strike), -cost,
                                     ((right, a.strike, wa / tot), (right, b.strike, -1.0),
                                      (right, c.strike, wc / tot))))
    return out


def box_cost(quotes: dict[tuple[str, float], Quote], k1: float, k2: float, buy: bool = True) -> float:
    """Cash paid to buy (or received to sell) the box: long K1 call, short K2 call, short K1 put, long K2 put."""
    s = 1.0 if buy else -1.0
    legs = ((("C", k1), s), (("C", k2), -s), (("P", k1), -s), (("P", k2), s))
    cash = sum(_px(quotes[key], qty) for key, qty in legs)
    return cash if buy else -cash


def box_rate(price: float, width: float, years: float) -> float:
    """Continuously compounded rate implied by a box costing `price` that pays `width` in `years`."""
    return -math.log(price / width) / years


def check_box(quotes: dict[tuple[str, float], Quote], k1: float, k2: float, df: float,
              tol: float = 1e-9) -> list[Violation]:
    """The box must cost df*(K2-K1): buying it below, or selling it above, is an arbitrage."""
    out, width = [], k2 - k1
    buy, sell = box_cost(quotes, k1, k2, True), box_cost(quotes, k1, k2, False)
    if buy < df * width - tol:
        out.append(Violation("box", (k1, k2), df * width - buy,
                             (("C", k1, 1.0), ("C", k2, -1.0), ("P", k1, -1.0), ("P", k2, 1.0))))
    if sell > df * width + tol:
        out.append(Violation("box", (k1, k2), sell - df * width,
                             (("C", k1, -1.0), ("C", k2, 1.0), ("P", k1, 1.0), ("P", k2, -1.0))))
    return out
