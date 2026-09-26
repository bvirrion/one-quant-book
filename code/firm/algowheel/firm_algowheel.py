"""firm.algowheel -- an algo wheel: allocating orders across brokers at random, by strata or by Thompson sampling,
and evaluating the brokers with difficulty adjustment (build of One Quant Book 10, chapter 20; on firm.tca).

Costs in basis points, positive when paid; `difficulty` is each order's pre-trade cost estimate.

API (stable):
    random_allocation(n, k, rng)                       brokers drawn uniformly
    stratified_allocation(difficulty, k, buckets, rng) within each difficulty bucket, a random permutation of the
                                                       brokers repeated: every broker gets the same mix of orders
    Thompson(k, prior_mean, prior_sd, noise_sd)         Gaussian posterior of each broker's adjusted mean cost;
                                                       .choose(rng) samples the posteriors and picks the cheapest;
                                                       .update(broker, adjusted_cost)
    evaluate(cost, broker, difficulty, k, adjust, clusters)   per broker (mean, se, n): the broker effects of a
                                                       regression on broker dummies (and difficulty if adjust), the
                                                       cheapest broker as reference 0 in the output's 'diff'
    months_needed(delta, sd, orders_per_month, k, alpha, power)   the months of a uniform wheel for a two-sided test
                                                       of a difference delta between two brokers
    scorecard(cost, broker, difficulty, k, names, clusters)       rows: broker, orders, raw mean, adjusted
                                                       mean, standard error, rank
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np
from scipy.stats import norm

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tca"))
from firm_tca import cluster_ols  # noqa: E402


def random_allocation(n: int, k: int, rng) -> np.ndarray:
    return rng.integers(0, k, n)


def stratified_allocation(difficulty, k: int, buckets: int, rng) -> np.ndarray:
    d = np.asarray(difficulty, float)
    edges = np.quantile(d, np.linspace(0, 1, buckets + 1)[1:-1])
    b = np.searchsorted(edges, d)
    out = np.empty(len(d), int)
    for j in range(buckets):
        idx = np.nonzero(b == j)[0]
        reps = np.concatenate([rng.permutation(k) for _ in range(len(idx) // k + 1)])
        out[idx] = reps[:len(idx)]
    return out


class Thompson:
    def __init__(self, k: int, prior_mean: float, prior_sd: float, noise_sd: float):
        self.m = np.full(k, float(prior_mean))
        self.v = np.full(k, float(prior_sd) ** 2)
        self.s2 = float(noise_sd) ** 2

    def choose(self, rng) -> int:
        return int(np.argmin(rng.normal(self.m, np.sqrt(self.v))))

    def update(self, broker: int, cost: float) -> None:
        prec = 1 / self.v[broker] + 1 / self.s2
        self.m[broker] = (self.m[broker] / self.v[broker] + cost / self.s2) / prec
        self.v[broker] = 1 / prec


def evaluate(cost, broker, difficulty, k: int, adjust: bool = True, clusters=None) -> dict:
    y = np.asarray(cost, float)
    b = np.asarray(broker)
    dummies = (b[:, None] == np.arange(k)[None, :]).astype(float)
    x = np.c_[dummies, np.asarray(difficulty, float)] if adjust else dummies
    if adjust:
        x[:, -1] -= x[:, -1].mean()                    # broker effects at the average difficulty
    g = np.arange(len(y)) if clusters is None else np.asarray(clusters)
    beta, cov = cluster_ols(y, x, g)
    se = np.sqrt(np.diag(cov))[:k]
    n = dummies.sum(axis=0).astype(int)
    return {"mean": beta[:k], "se": se, "n": n, "cov": cov[:k, :k]}


def months_needed(delta: float, sd: float, orders_per_month: float, k: int,
                  alpha: float = 0.05, power: float = 0.8) -> float:
    z = norm.ppf(1 - alpha / 2) + norm.ppf(power)
    per_broker = 2 * sd**2 * z**2 / delta**2
    return per_broker * k / orders_per_month


def scorecard(cost, broker, difficulty, k: int, names, clusters=None) -> list:
    y, b = np.asarray(cost, float), np.asarray(broker)
    ev = evaluate(y, b, difficulty, k, True, clusters)
    order = np.argsort(ev["mean"])
    rank = np.empty(k, int)
    rank[order] = np.arange(1, k + 1)
    return [(names[j], int(ev["n"][j]), float(y[b == j].mean()), float(ev["mean"][j]), float(ev["se"][j]),
             int(rank[j])) for j in range(k)]
