"""firm.projsel -- a research portfolio and the attribution of credit (build of One Quant Book 16, chapter 9).

Projects. A research project costs c, succeeds with probability p and is then worth V (the present value of the
P&L it adds, net of running costs); it may overlap a strategy the firm already runs, which cuts its value by a
share `overlap`. `select` chooses projects under a budget: by expected net value per unit of cost, greedily, which
is the standard approximation to the knapsack; `simulate_year` draws which ones succeed.

Credit. Several contributors' signals are combined into one forecast; the combined P&L is a game v(S) on the
set of contributors: the P&L of the best combination of the signals in S. Leave-one-out credit is
v(N) - v(N minus i); order-dependent credit is v(first k) - v(first k-1) in a given order; the Shapley value is the
average of the order-dependent credits over all orders (exact for few contributors, sampled for many). It is the
only split that adds up to v(N), treats identical contributors equally and gives nothing to a contributor who adds
nothing (One Quant Book 12, chapter 6). NumPy only.

API (stable):
    Project(name, cost, p, value, overlap=0.0); expected_net(pr)
    select(projects, budget) -> list of chosen projects ; select_random(projects, budget, rng)
    simulate_year(chosen, rng) -> realised value
    game(signals, target) -> v: frozenset -> float      P&L of the least-squares combination of the signals in S
    leave_one_out(v, n), ordered(v, order), shapley(v, n, samples=None, rng=None)
"""
import itertools
import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Project:
    name: str
    cost: float
    p: float
    value: float
    overlap: float = 0.0


def expected_net(pr: Project) -> float:
    return pr.p * pr.value * (1 - pr.overlap) - pr.cost


def select(projects, budget: float) -> list:
    """Greedy by expected net value per unit of cost, skipping projects with non-positive expected net value."""
    cand = sorted((x for x in projects if expected_net(x) > 0), key=lambda x: expected_net(x) / x.cost, reverse=True)
    out, spent = [], 0.0
    for x in cand:
        if spent + x.cost <= budget:
            out.append(x)
            spent += x.cost
    return out


def select_random(projects, budget: float, rng) -> list:
    out, spent = [], 0.0
    for i in rng.permutation(len(projects)):
        x = projects[i]
        if spent + x.cost <= budget:
            out.append(x)
            spent += x.cost
    return out


def simulate_year(chosen, rng) -> float:
    return float(sum((rng.random() < x.p) * x.value * (1 - x.overlap) - x.cost for x in chosen))


def game(signals: np.ndarray, target: np.ndarray):
    """signals (T, n), target (T,): v(S) = sum over t of the fitted forecast times the target, i.e. the in-sample P&L of
    trading the least-squares combination of the signals in S (units of target times forecast)."""
    cache = {}

    def v(S) -> float:
        S = frozenset(S)
        if not S:
            return 0.0
        if S not in cache:
            X = signals[:, sorted(S)]
            beta, *_ = np.linalg.lstsq(X, target, rcond=None)
            cache[S] = float((X @ beta) @ target)
        return cache[S]
    return v


def leave_one_out(v, n: int) -> np.ndarray:
    full = frozenset(range(n))
    return np.array([v(full) - v(full - {i}) for i in range(n)])


def ordered(v, order) -> np.ndarray:
    out = np.zeros(len(order))
    seen = set()
    for i in order:
        before = v(seen)
        seen.add(i)
        out[i] = v(seen) - before
    return out


def shapley(v, n: int, samples: int | None = None, rng=None) -> np.ndarray:
    if samples is None:
        tot = np.zeros(n)
        for order in itertools.permutations(range(n)):
            tot += ordered(v, order)
        return tot / math.factorial(n)
    tot = np.zeros(n)
    for _ in range(samples):
        tot += ordered(v, list(rng.permutation(n)))
    return tot / samples
