"""firm.hawkes -- exponential-kernel Hawkes processes (One Quant Book 4, chapter 7).

Univariate: lambda_t = mu + sum_{t_i < t} alpha exp(-beta (t - t_i)), branching ratio alpha / beta.
Multivariate: lambda^(i)_t = mu_i + sum_j sum_{t^j_k < t} alpha_ij exp(-beta_ij (t - t^j_k)).

API (stable):
    simulate_thinning(mu, alpha, beta, T, seed)            Ogata's thinning, exact
    simulate_branching(mu, alpha, beta, T, seed)           immigrants and Poisson offspring
    simulate_multivariate(mu, alpha, beta, T, seed)        thinning for d dimensions
    intensity(times, mu, alpha, beta, grid)                lambda on a grid of times
    loglik(params, times, T)                               O(n) log-likelihood, params = (mu, alpha, beta)
    fit(times, T, start=None)                              maximum likelihood (Nelder-Mead on logs)
    compensator(times, mu, alpha, beta)                    Lambda(t_i) at the event times
    residuals(times, mu, alpha, beta)                      increments of Lambda: Exp(1) if the model is right
    nelder_mead(f, x0, ...)                                the minimiser used by fit
"""
from __future__ import annotations

import math

import numpy as np


def simulate_thinning(mu: float, alpha: float, beta: float, T: float, seed: int) -> np.ndarray:
    """Ogata (1981): propose at the current upper bound of the intensity, accept with probability
    lambda(t) / bound. The intensity decays between events, so its value just after the last event
    bounds it until the next one."""
    rng = np.random.default_rng(seed)
    t, excite, out = 0.0, 0.0, []            # excite = sum of alpha exp(-beta (t - t_i)) at time t
    while True:
        bound = mu + excite
        w = rng.exponential(1.0 / bound)
        t += w
        if t > T:
            break
        excite *= math.exp(-beta * w)
        if rng.random() * bound <= mu + excite:
            out.append(t)
            excite += alpha
    return np.array(out)


def simulate_branching(mu: float, alpha: float, beta: float, T: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Cluster representation: immigrants form a Poisson(mu) process; every event has
    Poisson(alpha / beta) children at Exp(beta) delays. Returns (times, generation)."""
    rng = np.random.default_rng(seed)
    n0 = rng.poisson(mu * T)
    gen_times = [np.sort(rng.uniform(0, T, n0))]
    gens = [np.zeros(n0, dtype=int)]
    k = 0
    while gen_times[-1].size:
        parents = gen_times[-1]
        n_kids = rng.poisson(alpha / beta, parents.size)
        kids = np.repeat(parents, n_kids) + rng.exponential(1.0 / beta, n_kids.sum())
        kids = kids[kids <= T]
        k += 1
        gen_times.append(kids)
        gens.append(np.full(kids.size, k))
    times, g = np.concatenate(gen_times), np.concatenate(gens)
    order = np.argsort(times)
    return times[order], g[order]


def simulate_multivariate(mu, alpha, beta, T: float, seed: int) -> list[np.ndarray]:
    """Thinning for a d-dimensional exponential Hawkes process; alpha[i, j] is the jump in the
    intensity of i caused by an event of j."""
    mu, alpha, beta = np.asarray(mu, float), np.asarray(alpha, float), np.asarray(beta, float)
    d = mu.size
    rng = np.random.default_rng(seed)
    t, excite = 0.0, np.zeros((d, d))
    out: list[list[float]] = [[] for _ in range(d)]
    while True:
        lam = mu + excite.sum(axis=1)
        bound = lam.sum()
        w = rng.exponential(1.0 / bound)
        t += w
        if t > T:
            break
        excite *= np.exp(-beta * w)
        lam = mu + excite.sum(axis=1)
        u = rng.random() * bound
        if u <= lam.sum():
            i = int(np.searchsorted(np.cumsum(lam), u))
            out[i].append(t)
            excite[:, i] += alpha[:, i]
    return [np.array(x) for x in out]


def intensity(times: np.ndarray, mu: float, alpha: float, beta: float, grid: np.ndarray) -> np.ndarray:
    """lambda_t on a grid (left limits at event times)."""
    out = np.full(grid.size, mu, dtype=float)
    for ti in times:
        m = grid > ti
        out[m] += alpha * np.exp(-beta * (grid[m] - ti))
    return out


def loglik(params, times: np.ndarray, T: float) -> float:
    """sum_i log lambda(t_i) - int_0^T lambda dt, with A_i = sum_{j<i} exp(-beta (t_i - t_j)) computed
    by the recursion A_i = exp(-beta (t_i - t_{i-1})) (1 + A_{i-1}): O(n)."""
    mu, alpha, beta = params
    if mu <= 0 or alpha < 0 or beta <= 0:
        return -math.inf
    total, a, prev = 0.0, 0.0, None
    for t in times:
        if prev is not None:
            a = math.exp(-beta * (t - prev)) * (1.0 + a)
        total += math.log(mu + alpha * a)
        prev = t
    integral = mu * T + alpha / beta * float(np.sum(1.0 - np.exp(-beta * (T - times))))
    return total - integral


def nelder_mead(f, x0, step: float = 0.2, tol: float = 1e-9, max_iter: int = 2000) -> tuple[np.ndarray, float]:
    """Minimise f by the Nelder-Mead simplex (reflection 1, expansion 2, contraction 1/2, shrink 1/2)."""
    x0 = np.asarray(x0, dtype=float)
    n = x0.size
    simplex = [x0] + [x0 + step * np.eye(n)[i] for i in range(n)]
    vals = [f(x) for x in simplex]
    for _ in range(max_iter):
        order = np.argsort(vals)
        simplex = [simplex[i] for i in order]
        vals = [vals[i] for i in order]
        if abs(vals[-1] - vals[0]) < tol * (1 + abs(vals[0])):
            break
        centroid = np.mean(simplex[:-1], axis=0)
        xr = centroid + (centroid - simplex[-1])
        fr = f(xr)
        if fr < vals[0]:
            xe = centroid + 2 * (centroid - simplex[-1])
            fe = f(xe)
            simplex[-1], vals[-1] = (xe, fe) if fe < fr else (xr, fr)
        elif fr < vals[-2]:
            simplex[-1], vals[-1] = xr, fr
        else:
            xc = centroid + 0.5 * (simplex[-1] - centroid)
            fc = f(xc)
            if fc < vals[-1]:
                simplex[-1], vals[-1] = xc, fc
            else:
                simplex = [simplex[0]] + [simplex[0] + 0.5 * (x - simplex[0]) for x in simplex[1:]]
                vals = [vals[0]] + [f(x) for x in simplex[1:]]
    i = int(np.argmin(vals))
    return simplex[i], vals[i]


def fit(times: np.ndarray, T: float, start=None) -> dict:
    """Maximum likelihood over (mu, alpha, beta), searched on the logs of (mu, n, beta) with the
    branching ratio n = alpha / beta kept below one."""
    n_ev = times.size
    if start is None:
        start = (0.5 * n_ev / T, 0.5, 1.0)
    mu0, n0, b0 = start

    def neg(z):
        mu, br, beta = math.exp(z[0]), 1 / (1 + math.exp(-z[1])), math.exp(z[2])
        return -loglik((mu, br * beta, beta), times, T)

    z0 = np.array([math.log(mu0), math.log(n0 / (1 - n0)), math.log(b0)])
    z, val = nelder_mead(neg, z0)
    mu, br, beta = math.exp(z[0]), 1 / (1 + math.exp(-z[1])), math.exp(z[2])
    return {"mu": mu, "alpha": br * beta, "beta": beta, "branching": br, "loglik": -val}


def compensator(times: np.ndarray, mu: float, alpha: float, beta: float) -> np.ndarray:
    """Lambda(t_i) = mu t_i + (alpha / beta) sum_{j<i} (1 - exp(-beta (t_i - t_j))), in O(n)."""
    out = np.empty(times.size)
    a, prev, count = 0.0, None, 0
    for k, t in enumerate(times):
        if prev is not None:
            a = math.exp(-beta * (t - prev)) * (1.0 + a)
        out[k] = mu * t + alpha / beta * (count - a)
        count += 1
        prev = t
    return out


def residuals(times: np.ndarray, mu: float, alpha: float, beta: float) -> np.ndarray:
    """Time-rescaled inter-event times: independent Exp(1) when the model is the true one."""
    return np.diff(np.concatenate([[0.0], compensator(times, mu, alpha, beta)]))
