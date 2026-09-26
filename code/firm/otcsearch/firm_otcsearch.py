"""firm.otcsearch -- over-the-counter markets: a search-and-bargaining model in the manner of Duffie, Garleanu and
Pedersen, requests for quote with private and common values and leakage, information chasing, and a core-periphery
dealer network (build of One Quant Book 10, chapter 23; extends Book 2's firm.rfq by composition).

API (stable):
    dgp(lam_u, lam_d, rho, s, r, delta, z)   steady state and prices of a dealer market: investors switch between a
                                   high type and a low type (holding cost delta) at rates lam_u (to high) and lam_d (to
                                   low), meet dealers at rate rho; low owners sell, high non-owners buy; dealers keep
                                   a share z of each trade's surplus; with s below the high types' share the buyers are
                                   the long side and the inter-dealer price is their reservation value. Returns masses
                                   mu (ho, hn, lo, ln), reservation values dV (h, l), bid, ask, spread (per unit of the
                                   asset, which pays 1 a year), and the spread as a share of the mid
    rfq_cost(n, markup, sigma_p, sigma_c, leak)   the client's expected cost of selling to the best of n dealers:
                                   markup - (sqrt(sigma_c^2 + sigma_p^2) - sigma_c) E[max of n] + leak (n - 1); the
                                   common-value part of the dealers' estimates adds noise the winner shades away
    best_n(markup, sigma_p, sigma_c, leak, n_max)
    rfq_simulate(n, markup, sigma_p, sigma_c, leak, trials, seed)   the same by simulation: every dealer bids its
                                   estimate of the common value plus its private value, less the markup and its
                                   winner's-curse shading sigma_c E[max of n]
    chase(cost, adverse, info_value)   spreads a competitive dealer quotes an uninformed and an informed client when
                                   an informed trade teaches it info_value (to use with others): cost, and cost +
                                   adverse - info_value
    core_periphery(n_core, n_periph, links, seed)   adjacency: a complete core, each periphery dealer linked to
                                   `links` core dealers
    intermediation(adj, n_core, markup_core, markup_periph, trials, seed)   trades from a random seller's dealer to a
                                   random buyer's dealer along shortest paths: hops and total markup, by the buyer's
                                   dealer's type
"""
from __future__ import annotations

import math
import pathlib
import sys
from collections import deque

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "rfq"))
from firm_rfq import expected_cost, expected_max_normal  # noqa: E402


def dgp(lam_u: float, lam_d: float, rho: float, s: float, r: float, delta: float, z: float) -> dict:
    phi = lam_u / (lam_u + lam_d)
    if s >= phi:
        raise ValueError("this version needs s below the high types' share")
    mu_lo = lam_d * s / (lam_u + lam_d + rho)   # in from switching, out to high and dealers
    mu_ho = s - mu_lo
    mu_hn = phi - mu_ho
    mu_ln = 1 - phi - mu_lo
    # r dVh = 1 + lam_d (dVl - dVh) - rho (dVh - A), A = M = dVh
    # r dVl = 1 - delta + lam_u (dVh - dVl) + rho (1 - z) (M - dVl)
    k = rho * (1 - z)
    a = np.array([[r + lam_d, -lam_d], [-lam_u - k, r + lam_u + k]])
    dvh, dvl = np.linalg.solve(a, [1.0, 1.0 - delta])
    ask = dvh
    bid = z * dvl + (1 - z) * dvh
    return {"mu": (mu_ho, mu_hn, mu_lo, mu_ln), "dV": (dvh, dvl), "bid": bid, "ask": ask,
            "spread": ask - bid, "spread_share": (ask - bid) / ((ask + bid) / 2)}


def rfq_cost(n: int, markup: float, sigma_p: float, sigma_c: float, leak: float) -> float:
    sd = math.sqrt(sigma_p**2 + sigma_c**2)
    return expected_cost(n, markup, sd, leak) + sigma_c * expected_max_normal(n)


def best_n(markup: float, sigma_p: float, sigma_c: float, leak: float,
           n_max: int = 20) -> int:
    def cost(n):
        return rfq_cost(n, markup, sigma_p, sigma_c, leak)
    return min(range(1, n_max + 1), key=cost)


def rfq_simulate(n: int, markup: float, sigma_p: float, sigma_c: float, leak: float, trials: int = 100_000,
                 seed: int = 1) -> float:
    rng = np.random.default_rng(seed)
    est = sigma_c * rng.standard_normal((trials, n)) + sigma_p * rng.standard_normal((trials, n))
    bids = est - markup - sigma_c * expected_max_normal(n)     # relative to the common value
    return float(np.mean(-bids.max(axis=1)) + leak * (n - 1))


def chase(cost: float, adverse: float, info_value: float) -> dict:
    return {"uninformed": cost, "informed": cost + adverse - info_value}


def core_periphery(n_core: int, n_periph: int, links: int, seed: int = 1) -> list:
    rng = np.random.default_rng(seed)
    adj = [set() for _ in range(n_core + n_periph)]
    for i in range(n_core):
        for j in range(i + 1, n_core):
            adj[i].add(j)
            adj[j].add(i)
    for p in range(n_core, n_core + n_periph):
        for c in rng.choice(n_core, links, replace=False):
            adj[p].add(int(c))
            adj[int(c)].add(p)
    return adj


def _path(adj, a: int, b: int) -> list:
    prev = {a: None}
    q = deque([a])
    while q:
        u = q.popleft()
        if u == b:
            break
        for v in sorted(adj[u]):
            if v not in prev:
                prev[v] = u
                q.append(v)
    out, u = [], b
    while u is not None:
        out.append(u)
        u = prev[u]
    return out[::-1]


def intermediation(adj, n_core: int, markup_core: float, markup_periph: float, trials: int = 5000,
                   seed: int = 1) -> dict:
    """Each dealer on the path that passes the bond on charges its markup (core or periphery); the buyer's dealer
    charges the client too. Hops = dealers on the path minus one."""
    rng = np.random.default_rng(seed)
    n = len(adj)
    res = {"core": [], "periphery": []}
    for _ in range(trials):
        a, b = rng.choice(n, 2, replace=False)
        path = _path(adj, int(a), int(b))
        mk = sum(markup_core if d < n_core else markup_periph for d in path)
        res["core" if b < n_core else "periphery"].append((len(path) - 1, mk))
    return {k: {"hops": float(np.mean([x[0] for x in v])), "markup": float(np.mean([x[1] for x in v])),
                "n": len(v)} for k, v in res.items()}
