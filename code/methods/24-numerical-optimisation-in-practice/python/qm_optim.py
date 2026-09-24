"""Book 4, chapter 24: numerical optimisation in practice (teaching module).

Convergence rates on an ill-conditioned quadratic; a daily calibration of a two-exponential autocorrelation kernel
whose objective has a flat valley and two mirror-image valleys; a penalty toward yesterday's fit; proximal gradient
for the lasso; ADMM against alternating projections for the nearest correlation matrix; stochastic gradients.
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "optim"))
sys.path.insert(0, str(ROOT / "code" / "firm" / "portopt"))
from firm_optim import (  # noqa: E402
    Bounded,
    admm_nearest_correlation,
    gradient_descent,
    identifiability,
    lbfgs,
    levenberg_marquardt,
    newton,
    prox_l1,
    proximal_gradient,
    sgd,
    tikhonov,
)
from firm_portopt import nearest_correlation  # noqa: E402

LAGS = np.arange(1, 31)
TRUE = np.array([0.6, 3.0, 60.0])          # weight of the fast component, fast and slow time scales (days)
NOISE = 0.01
START = np.array([0.5, 2.0, 20.0])
BOUNDS = Bounded([0.0, 0.2, 0.2], [1.0, 1000.0, 1000.0])


def kernel(p) -> np.ndarray:
    return p[0] * np.exp(-LAGS / p[1]) + (1 - p[0]) * np.exp(-LAGS / p[2])


def days(n: int = 250, seed: int = 24) -> list:
    rng = np.random.default_rng(seed)
    return [kernel(TRUE) + NOISE * rng.standard_normal(LAGS.size) for _ in range(n)]


def fit(r, start, prev=None, weight: float = 0.0) -> dict:
    def res(u):
        return kernel(BOUNDS.from_free(u)) - r
    f = tikhonov(res, BOUNDS.to_free(prev), [weight] * 3) if prev is not None and weight > 0 else res
    with np.errstate(over="ignore", invalid="ignore"):
        out = levenberg_marquardt(f, BOUNDS.to_free(start))
    p = BOUNDS.from_free(out["x"])
    return {"p": p, "rmse": float(np.sqrt(np.mean((kernel(p) - r) ** 2))), "iters": out["iters"], "jac": out["jac"]}


def daily(weight: float = 0.0, n: int = 250) -> dict:
    """Refit every day: from the fixed start without a penalty, or from yesterday's fit with a penalty toward it."""
    P, E = [], []
    prev = None
    for r in days(n):
        out = fit(r, START if prev is None or weight == 0 else prev, prev, weight)
        P.append(out["p"])
        E.append(out["rmse"])
        prev = out["p"]
    P = np.array(P)
    jumps = np.abs(np.diff(P[:, 2]))
    k = int(np.argmax(jumps))
    return {"P": P, "rmse": np.array(E), "median_jump": float(np.median(jumps)), "max_jump": float(jumps.max()),
            "max_day": k + 1, "before": P[k], "after": P[k + 1], "rmse_before": E[k], "rmse_after": E[k + 1],
            "mean_rmse": float(np.mean(E)), "sd_tau2": float(P[:, 2].std())}


def multistart(n: int = 100, seed: int = 7) -> np.ndarray:
    """End points of fits of the first day's curve from n random starts: (a, tau1, tau2, rmse)."""
    rng = np.random.default_rng(seed)
    r = days(1)[0]
    rows = []
    for _ in range(n):
        st = [rng.uniform(0.05, 0.95), math.exp(rng.uniform(math.log(0.5), math.log(200))),
              math.exp(rng.uniform(math.log(0.5), math.log(200)))]
        out = fit(r, st)
        rows.append([*out["p"], out["rmse"]])
    return np.array(rows)


def classify(ends: np.ndarray, best: float) -> dict:
    good = ends[:, 3] < best * 1.001
    mirror = good & (ends[:, 1] > ends[:, 2])
    return {"best": int(np.sum(good & ~mirror)), "mirror": int(np.sum(mirror)), "boundary": int(np.sum(
        (np.maximum(ends[:, 1], ends[:, 2]) > 900) & ~good)), "other": int(np.sum(~good & (np.maximum(
            ends[:, 1], ends[:, 2]) <= 900)))}


def valley(r=None, n: int = 41) -> dict:
    """Profile of the fit error along the slow time scale: for each fixed tau2, the best (a, tau1)."""
    r = days(1)[0] if r is None else r
    out = []
    for t2 in np.geomspace(20, 400, n):
        def res(u, t2=t2):
            a = 1 / (1 + math.exp(-u[0]))
            return kernel([a, math.exp(u[1]), t2]) - r
        with np.errstate(over="ignore", invalid="ignore"):
            s = levenberg_marquardt(res, np.array([0.4, math.log(3.0)]))
        out.append((float(t2), float(np.sqrt(np.mean(res(s["x"]) ** 2)))))
    return {"profile": out}


def diagnostics() -> dict:
    out = fit(days(1)[0], START)
    d = identifiability(out["jac"])
    return {"cond": d["cond"], "corr": d["corr"], "p": out["p"]}


# --- convergence rates -------------------------------------------------------------------------------------

def rates(kappa: float = 100.0, n_iter: int = 200) -> dict:
    """f(x) = (x1^2 + kappa x2^2) / 2 from (1, 1): gradient descent with step 1 / kappa, Nesterov, L-BFGS, Newton."""
    H = np.diag([1.0, kappa])

    def f(x):
        return 0.5 * float(x @ H @ x)

    def g(x):
        return H @ x
    x0 = np.array([1.0, 1.0])
    gd = [f(x) for x in gradient_descent(g, x0, 1 / kappa, n_iter)]
    ns = [f(x) for x in gradient_descent(g, x0, 1 / kappa, n_iter, nesterov=True)]
    lb = lbfgs(f, g, x0, tol=1e-14)
    nx, nit = newton(g, lambda x: H, x0)
    return {"gd": np.array(gd), "nesterov": np.array(ns), "lbfgs_iters": lb["iters"], "newton_iters": nit,
            "theory_gd": 0.5 * (1 - 1 / kappa) ** (2 * np.arange(n_iter + 1)), "kappa": kappa}


def lasso_prox(seed: int = 3, n: int = 200, p: int = 50, lam: float = 0.1, n_iter: int = 300) -> dict:
    """min |y - Xb|^2 / (2n) + lam |b|_1 by ISTA and FISTA; objective gap to a long FISTA run."""
    rng = np.random.default_rng(seed)
    X = rng.standard_normal((n, p))
    X[:, 1] = X[:, 0] + 0.1 * rng.standard_normal(n)                  # a near-collinear pair slows things down
    beta = np.zeros(p)
    beta[:5] = [1.0, -0.5, 0.8, 0.0, 0.3]
    y = X @ beta + rng.standard_normal(n)
    L = float(np.linalg.eigvalsh(X.T @ X / n)[-1])

    def grad_f(b):
        return X.T @ (X @ b - y) / n

    def obj(b):
        return float(np.sum((y - X @ b) ** 2) / (2 * n) + lam * np.abs(b).sum())

    def prox(v, t):
        return prox_l1(v, lam * t)
    best = obj(proximal_gradient(grad_f, prox, np.zeros(p), L, 5000)[-1])
    ista = [obj(b) - best for b in proximal_gradient(grad_f, prox, np.zeros(p), L, n_iter, accel=False)]
    fista = [obj(b) - best for b in proximal_gradient(grad_f, prox, np.zeros(p), L, n_iter, accel=True)]
    return {"ista": np.maximum(ista, 1e-16), "fista": np.maximum(fista, 1e-16), "L": L,
            "nonzero": int(np.sum(np.abs(proximal_gradient(grad_f, prox, np.zeros(p), L, 5000)[-1]) > 1e-8))}


def ncm_compare() -> dict:
    """The chapter-23 broken correlation matrix repaired by ADMM and by alternating projections."""
    sys.path.insert(0, str(ROOT / "code" / "methods" / "23-convex-optimisation" / "python"))
    from qm_opt import broken_correlation
    C = broken_correlation()["C"]
    Xa, ia = admm_nearest_correlation(C, rho=1.0, tol=1e-9)
    Xh, ih = nearest_correlation(C, tol=1e-10)
    return {"iters_admm": ia, "iters_ap": ih, "dist_admm": float(np.linalg.norm(C - Xa)),
            "dist_ap": float(np.linalg.norm(C - Xh)), "gap": float(np.max(np.abs(Xa - Xh))),
            "mineig_admm": float(np.linalg.eigvalsh(Xa).min())}


def sgd_demo(seed: int = 5, n: int = 1000, steps: int = 20_000) -> dict:
    """Least squares by SGD with Robbins-Monro steps a / (b + k) against a constant step."""
    rng = np.random.default_rng(seed)
    X = rng.standard_normal((n, 3))
    beta = np.array([0.5, -1.0, 2.0])
    y = X @ beta + rng.standard_normal(n)
    ols = np.linalg.lstsq(X, y, rcond=None)[0]

    def gi(b, i):
        return X[i] * (X[i] @ b - y[i])
    rm = sgd(gi, np.zeros(3), n, steps, 1.0, 10.0, np.random.default_rng(seed + 1))
    const = sgd(gi, np.zeros(3), n, steps, 0.05 * steps, steps, np.random.default_rng(seed + 1))   # ~ constant 0.05
    return {"err_rm": float(np.linalg.norm(rm - ols)), "err_const": float(np.linalg.norm(const - ols)), "ols": ols}
