"""Recombining binomial trees: CRR, Jarrow-Rudd, Leisen-Reimer (build of Book 5, Chapter 2).

European and American calls and puts, a continuous dividend yield q, and discrete cash dividends
by the escrowed model (Chapter 5): the tree is built on the spot minus the present value of the
dividends paid before expiry, and the exercise value at a node adds back the present value of the
dividends still to come. Backward induction is vectorised: O(n) memory, O(n^2) time.
"""
import math

import numpy as np


def _peizer_pratt(z: float, n: int) -> float:
    """Peizer-Pratt method-2 inversion: a binomial probability matching a normal cdf value."""
    if z == 0.0:
        return 0.5
    a = z / (n + 1.0 / 3.0 + 0.1 / (n + 1.0))
    return 0.5 + math.copysign(0.5, z) * math.sqrt(1.0 - math.exp(-a * a * (n + 1.0 / 6.0)))


def params(method: str, spot: float, strike: float, t: float, r: float, q: float, vol: float,
           n: int) -> tuple[float, float, float]:
    """(u, d, p): up and down factors per step and the risk-neutral up probability."""
    dt = t / n
    growth = math.exp((r - q) * dt)
    if method == "crr":
        u = math.exp(vol * math.sqrt(dt))
        d = 1.0 / u
    elif method == "jr":
        m = (r - q - 0.5 * vol * vol) * dt
        u, d = math.exp(m + vol * math.sqrt(dt)), math.exp(m - vol * math.sqrt(dt))
    elif method == "lr":
        if n % 2 == 0:
            raise ValueError("Leisen-Reimer needs an odd number of steps")
        s = vol * math.sqrt(t)
        d1 = (math.log(spot / strike) + (r - q) * t) / s + 0.5 * s
        p1, p = _peizer_pratt(d1, n), _peizer_pratt(d1 - s, n)
        u = growth * p1 / p
        d = (growth - p * u) / (1.0 - p)
        return u, d, p
    else:
        raise ValueError(method)
    p = (growth - d) / (u - d)
    if not 0.0 < p < 1.0:
        raise ValueError("arbitrage in the tree: need d < exp((r-q)dt) < u")
    return u, d, p


def price(spot: float, strike: float, t: float, r: float, vol: float, n: int, right: str = "C",
          american: bool = False, q: float = 0.0, method: str = "crr",
          dividends: tuple[tuple[float, float], ...] = ()) -> float:
    """Option value by backward induction; dividends are (time, cash amount) pairs, escrowed."""
    dt = t / n
    pv_divs = sum(a * math.exp(-r * s) for s, a in dividends if 0.0 < s <= t)
    base = spot - pv_divs
    u, d, p = params(method, base, strike, t, r, q, vol, n)
    disc = math.exp(-r * dt)
    sign = 1.0 if right == "C" else -1.0
    j = np.arange(n + 1)
    s_t = base * u ** j * d ** (n - j)
    v = np.maximum(sign * (s_t - strike), 0.0)
    for step in range(n - 1, -1, -1):
        v = disc * (p * v[1:] + (1.0 - p) * v[:-1])
        if american:
            tk = step * dt
            add = sum(a * math.exp(-r * (s - tk)) for s, a in dividends if tk < s <= t)
            j = np.arange(step + 1)
            s_k = base * u ** j * d ** (step - j) + add
            v = np.maximum(v, sign * (s_k - strike))
    return float(v[0])


def node_values(spot: float, strike: float, r_step: float, u: float, d: float, n: int, right: str = "C",
                american: bool = False) -> tuple[list[np.ndarray], list[np.ndarray]]:
    """Whiteboard tree with a per-step gross rate r_step: share prices and option values at every node."""
    p = (r_step - d) / (u - d)
    sign = 1.0 if right == "C" else -1.0
    shares = [spot * u ** np.arange(k + 1) * d ** (k - np.arange(k + 1)) for k in range(n + 1)]
    vals = [np.zeros(k + 1) for k in range(n + 1)]
    vals[n] = np.maximum(sign * (shares[n] - strike), 0.0)
    for k in range(n - 1, -1, -1):
        cont = (p * vals[k + 1][1:] + (1.0 - p) * vals[k + 1][:-1]) / r_step
        vals[k] = np.maximum(cont, sign * (shares[k] - strike)) if american else cont
    return shares, vals
