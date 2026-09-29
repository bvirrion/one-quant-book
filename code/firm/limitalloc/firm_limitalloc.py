"""firm.limitalloc -- a limit framework, and the allocation and pricing of risk capital
(build of One Quant Book 16, chapter 7).

Limits. A framework is a tree of nodes (firm, desks, strategies); each node carries limits, one per measure
(value at risk, stress loss, gross notional, a sensitivity), each with a soft and a hard threshold, and optional
temporary increases that expire. Utilisation is exposure over the effective hard limit; a soft breach warns, a
hard breach must be cured or escalated (chapter 12). A node's exposure may not exceed its parent's limit
either: children are checked against their own limits and their sum against the parent's.

Capital. Economic capital is the expected shortfall of the firm's annual P&L at a high confidence, computed on
scenarios. It is allocated to strategies stand-alone (each strategy's own ES), by Euler contributions (each
strategy's expected loss in the firm's tail scenarios, which add up to the firm's ES), or incrementally (the
firm's ES minus the firm's ES without the strategy). RAROC is expected P&L over allocated capital; the capital
charge is the hurdle rate times allocated capital. `best_scales` maximises the firm's expected P&L less the
capital charge on its ES over position scales within limits (scipy).

API (stable):
    Limit(measure, soft, hard); Node(name, limits, children=(), temp=())  temp: ((measure, extra, expires_day), ...)
    check(node, exposures, day) -> list of (node, measure, utilisation, status)  status: ok | soft | hard
    es(pnl, alpha) ; allocate_capital(scen, alpha) -> dict(standalone, euler, incremental, firm)
    raroc(mu, capital) ; capital_charge(capital, h_k)
    best_scales(scen, alpha, h_k, lo, hi) -> scales
    to_riskctl(node) -> dict in the shape of firm.riskctl's limits snapshot (loss and position limits only)
"""
from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize


@dataclass(frozen=True)
class Limit:
    measure: str
    soft: float
    hard: float


@dataclass(frozen=True)
class Node:
    name: str
    limits: tuple
    children: tuple = ()
    temp: tuple = ()          # (measure, extra amount, last day it applies)

    def hard(self, measure: str, day: int) -> float:
        base = next(lim.hard for lim in self.limits if lim.measure == measure)
        return base + sum(x for m, x, until in self.temp if m == measure and day <= until)

    def soft(self, measure: str) -> float:
        return next(lim.soft for lim in self.limits if lim.measure == measure)


def check(node: Node, exposures: dict, day: int) -> list:
    """exposures[name][measure] for leaves; a parent's exposure is the sum of its children's (for additive
    measures) unless given. Returns every (node, measure, utilisation of the hard limit, status)."""
    out = []

    def expo(n: Node, measure: str) -> float:
        if n.name in exposures and measure in exposures[n.name]:
            return exposures[n.name][measure]
        return sum(expo(c, measure) for c in n.children)

    def walk(n: Node):
        for lim in n.limits:
            x = expo(n, lim.measure)
            hard = n.hard(lim.measure, day)
            status = "hard" if x > hard else ("soft" if x > lim.soft else "ok")
            out.append((n.name, lim.measure, x / hard, status))
        for c in n.children:
            walk(c)

    walk(node)
    return out


def es(pnl, alpha: float = 0.99) -> float:
    """Expected shortfall of a P&L sample at confidence alpha (a positive number for a loss)."""
    x = np.sort(np.asarray(pnl, float))
    k = max(1, int(round((1 - alpha) * len(x))))
    return float(-x[:k].mean())


def allocate_capital(scen: np.ndarray, alpha: float = 0.99) -> dict:
    """scen: (n scenarios, m strategies) annual P&L. Stand-alone, Euler and incremental ES allocations."""
    firm = scen.sum(1)
    n = len(firm)
    k = max(1, int(round((1 - alpha) * n)))
    tail = np.argsort(firm)[:k]
    euler = -scen[tail].mean(0)
    stand = np.array([es(scen[:, i], alpha) for i in range(scen.shape[1])])
    total = es(firm, alpha)
    incr = np.array([total - es(firm - scen[:, i], alpha) for i in range(scen.shape[1])])
    return {"standalone": stand, "euler": euler, "incremental": incr, "firm": total}


def raroc(mu, capital):
    return np.asarray(mu, float) / np.asarray(capital, float)


def capital_charge(capital, h_k: float):
    return h_k * np.asarray(capital, float)


def best_scales(scen: np.ndarray, alpha: float, h_k: float, lo: float = 0.0, hi: float = 2.0) -> np.ndarray:
    """Scales w in [lo, hi] maximising sum(w * mean P&L) - h_k * ES(firm P&L with scales w)."""
    mu = scen.mean(0)

    def obj(w):
        return -(w @ mu - h_k * es(scen @ w, alpha))

    m = scen.shape[1]
    res = minimize(obj, np.ones(m), bounds=[(lo, hi)] * m, method="Powell",
                   options={"xtol": 1e-4, "ftol": 1e-8, "maxiter": 20_000})
    return res.x


def to_riskctl(node: Node) -> dict:
    """The loss and position limits of a framework in the shape of firm.riskctl's snapshot (strategies as keys)."""
    out = {}

    def walk(n: Node):
        lims = {lim.measure: lim.hard for lim in n.limits}
        if not n.children:
            out[n.name] = {k: lims[k] for k in ("loss", "position") if k in lims}
        for c in n.children:
            walk(c)

    walk(node)
    return out
