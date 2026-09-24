"""firm.optim -- optimisation and calibration harness (One Quant Book 4, chapter 24).

Gradient descent (plain and Nesterov-accelerated), Newton, L-BFGS with a Wolfe line search, Levenberg-Marquardt for
nonlinear least squares, the proximal gradient method (with FISTA acceleration) and the l1 proximal operator, ADMM
for the nearest correlation matrix, stochastic gradient descent with Robbins-Monro steps, bounded-parameter
transforms, multistart, a Tikhonov penalty toward the previous fit, and identifiability diagnostics. NumPy only.

API (stable):
    gradient_descent(grad, x0, step, n_iter, nesterov=False)        iterates (n_iter + 1, d)
    newton(grad, hess, x0, tol, max_iter)                           (x, iters)
    lbfgs(f, grad, x0, m=10, tol=1e-8, max_iter=500)               dict(x, f, iters, status)
    levenberg_marquardt(resid, x0, jac=None, tol, max_iter)         dict(x, cost, iters, jac)
    prox_l1(v, t), proximal_gradient(grad_f, prox_g, x0, L, n_iter, accel=True)
    admm_nearest_correlation(C, rho=1.0, tol, max_iter)             (X, iters)
    sgd(grad_i, x0, n, n_steps, a, b, rng)                          x after steps a / (b + k)
    Bounded(lower, upper)                                           .to_free(p), .from_free(u): logit/log maps
    multistart(solve, starts)                                       list of results sorted by cost
    identifiability(J)                                              dict(cond, smallest_sv, corr)
    tikhonov(resid, prev, weight)                                   residual function with the penalty rows appended
"""
from __future__ import annotations

import math

import numpy as np


def gradient_descent(grad, x0, step: float, n_iter: int, nesterov: bool = False) -> np.ndarray:
    x = np.asarray(x0, dtype=float).copy()
    y, out = x.copy(), [x.copy()]
    for k in range(n_iter):
        if nesterov:
            x_new = y - step * grad(y)
            y = x_new + k / (k + 3) * (x_new - x)
            x = x_new
        else:
            x = x - step * grad(x)
        out.append(x.copy())
    return np.array(out)


def newton(grad, hess, x0, tol: float = 1e-12, max_iter: int = 100) -> tuple[np.ndarray, int]:
    x = np.asarray(x0, dtype=float).copy()
    for it in range(1, max_iter + 1):
        dx = np.linalg.solve(hess(x), -grad(x))
        x = x + dx
        if np.linalg.norm(dx) < tol * (1 + np.linalg.norm(x)):
            return x, it
    return x, max_iter


def _wolfe(f, grad, x, fx, gx, d, c1=1e-4, c2=0.9, max_iter=50):
    """Bracketing line search for the strong Wolfe conditions."""
    lo, hi, t = 0.0, math.inf, 1.0
    gd = float(gx @ d)
    for _ in range(max_iter):
        ft = f(x + t * d)
        if ft > fx + c1 * t * gd or not np.isfinite(ft):
            hi = t
        else:
            gt = float(grad(x + t * d) @ d)
            if abs(gt) <= -c2 * gd:
                return t
            if gt > 0:
                hi = t
            else:
                lo = t
        t = 0.5 * (lo + hi) if np.isfinite(hi) else 2 * t
    return t


def lbfgs(f, grad, x0, m: int = 10, tol: float = 1e-8, max_iter: int = 500) -> dict:
    """Limited-memory BFGS: the two-loop recursion applies the inverse-Hessian approximation built from the last m
    pairs (s, y); the Wolfe line search keeps s'y > 0, so every update is positive definite."""
    x = np.asarray(x0, dtype=float).copy()
    fx, gx = f(x), grad(x)
    S, Y = [], []
    for it in range(1, max_iter + 1):
        if np.linalg.norm(gx, np.inf) < tol:
            return {"x": x, "f": fx, "iters": it - 1, "status": "optimal"}
        q = gx.copy()
        alphas = []
        for s, y in zip(reversed(S), reversed(Y), strict=True):
            a = float(s @ q) / float(y @ s)
            alphas.append(a)
            q -= a * y
        gamma = float(S[-1] @ Y[-1]) / float(Y[-1] @ Y[-1]) if S else 1.0 / max(1.0, np.linalg.norm(gx))
        r = gamma * q
        for (s, y), a in zip(zip(S, Y, strict=True), reversed(alphas), strict=True):
            b = float(y @ r) / float(y @ s)
            r += s * (a - b)
        d = -r
        t = _wolfe(f, grad, x, fx, gx, d)
        x_new = x + t * d
        g_new = grad(x_new)
        s, y = x_new - x, g_new - gx
        if float(s @ y) > 1e-12:
            S.append(s)
            Y.append(y)
            if len(S) > m:
                S.pop(0)
                Y.pop(0)
        x, fx, gx = x_new, f(x_new), g_new
    return {"x": x, "f": fx, "iters": max_iter, "status": "max_iter"}


def numerical_jacobian(resid, x, h: float = 1e-7) -> np.ndarray:
    r0 = resid(x)
    J = np.empty((r0.size, x.size))
    for j in range(x.size):
        e = np.zeros(x.size)
        e[j] = h * max(1.0, abs(x[j]))
        J[:, j] = (resid(x + e) - r0) / e[j]
    return J


def levenberg_marquardt(resid, x0, jac=None, tol: float = 1e-10, max_iter: int = 500, lam: float = 1e-3) -> dict:
    """Minimise |r(x)|^2 / 2: solve (J'J + lam diag(J'J)) dx = -J'r, accept if the cost falls (then lam / 10),
    otherwise lam * 10."""
    x = np.asarray(x0, dtype=float).copy()
    r = resid(x)
    cost = 0.5 * float(r @ r)
    J = jac(x) if jac else numerical_jacobian(resid, x)
    for it in range(1, max_iter + 1):
        A = J.T @ J
        g = J.T @ r
        dx = np.linalg.solve(A + lam * np.diag(np.maximum(np.diag(A), 1e-12)), -g)
        x_new = x + dx
        r_new = resid(x_new)
        c_new = 0.5 * float(r_new @ r_new)
        if np.isfinite(c_new) and c_new < cost:
            x, r, lam = x_new, r_new, lam / 10
            done = cost - c_new < tol * max(cost, 1e-300)
            cost = c_new
            J = jac(x) if jac else numerical_jacobian(resid, x)
            if done or np.linalg.norm(dx) < tol * (1 + np.linalg.norm(x)):
                return {"x": x, "cost": cost, "iters": it, "jac": J, "status": "optimal"}
        else:
            lam *= 10
            if lam > 1e12:
                break
    return {"x": x, "cost": cost, "iters": max_iter, "jac": J, "status": "stalled"}


def prox_l1(v, t: float) -> np.ndarray:
    return np.sign(v) * np.maximum(np.abs(v) - t, 0.0)


def proximal_gradient(grad_f, prox_g, x0, L: float, n_iter: int, accel: bool = True) -> np.ndarray:
    """x_{k+1} = prox_{g / L}(y_k - grad f(y_k) / L); with accel (FISTA), y_k extrapolates by (t_k - 1) / t_{k+1}."""
    x = np.asarray(x0, dtype=float).copy()
    y, t = x.copy(), 1.0
    out = [x.copy()]
    for _ in range(n_iter):
        x_new = prox_g(y - grad_f(y) / L, 1.0 / L)
        if accel:
            t_new = (1 + math.sqrt(1 + 4 * t * t)) / 2
            y = x_new + (t - 1) / t_new * (x_new - x)
            t = t_new
        else:
            y = x_new
        x = x_new
        out.append(x.copy())
    return np.array(out)


def _proj_psd(X):
    lam, V = np.linalg.eigh((X + X.T) / 2)
    return (V * np.maximum(lam, 0)) @ V.T


def admm_nearest_correlation(C, rho: float = 1.0, tol: float = 1e-10, max_iter: int = 10_000) -> tuple[np.ndarray, int]:
    """min |X - C|_F^2 / 2 over X PSD with unit diagonal, split as X = Z with X PSD and Z of unit diagonal."""
    C = np.asarray(C, dtype=float)
    Z, U = np.eye(C.shape[0]), np.zeros_like(C)
    for it in range(1, max_iter + 1):
        X = _proj_psd((C + rho * (Z - U)) / (1 + rho))
        Z_old = Z
        Z = X + U
        np.fill_diagonal(Z, 1.0)
        U = U + X - Z
        if np.linalg.norm(X - Z) < tol and rho * np.linalg.norm(Z - Z_old) < tol:
            return Z, it
    return Z, max_iter


def sgd(grad_i, x0, n: int, n_steps: int, a: float, b: float, rng: np.random.Generator) -> np.ndarray:
    """Stochastic gradient descent with steps a / (b + k), which satisfy sum = inf and sum of squares < inf."""
    x = np.asarray(x0, dtype=float).copy()
    for k in range(n_steps):
        x = x - a / (b + k) * grad_i(x, int(rng.integers(n)))
    return x


class Bounded:
    """Unconstrained coordinates for bounded parameters: logit for (lower, upper), log for (lower, inf)."""

    def __init__(self, lower, upper):
        self.lo, self.hi = np.asarray(lower, dtype=float), np.asarray(upper, dtype=float)

    def from_free(self, u):
        u = np.clip(np.asarray(u, dtype=float), -700, 700)
        fin = np.isfinite(self.hi)
        out = self.lo + np.exp(u)
        out[fin] = self.lo[fin] + (self.hi[fin] - self.lo[fin]) / (1 + np.exp(-u[fin]))
        return out

    def to_free(self, p):
        p = np.asarray(p, dtype=float)
        fin = np.isfinite(self.hi)
        out = np.log(p - self.lo)
        z = (p[fin] - self.lo[fin]) / (self.hi[fin] - self.lo[fin])
        out[fin] = np.log(z / (1 - z))
        return out


def multistart(solve, starts) -> list:
    """Run a local solver from each start; results sorted by their cost (best first)."""
    return sorted((solve(s) for s in starts), key=lambda r: r["cost"])


def identifiability(J) -> dict:
    """Condition number and smallest singular value of the Jacobian, and the parameter correlation implied by
    (J'J)^-1: near-collinear columns mean a flat valley in the objective."""
    J = np.asarray(J, dtype=float)
    sv = np.linalg.svd(J, compute_uv=False)
    cov = np.linalg.pinv(J.T @ J)
    d = np.sqrt(np.maximum(np.diag(cov), 1e-300))
    return {"cond": float(sv[0] / sv[-1]), "smallest_sv": float(sv[-1]), "corr": cov / np.outer(d, d)}


def tikhonov(resid, prev, weight):
    """Append sqrt-weighted deviations from the previous parameters to the residuals: the fit then minimises
    |r(x)|^2 + sum_j weight_j (x_j - prev_j)^2."""
    prev, w = np.asarray(prev, dtype=float), np.sqrt(np.asarray(weight, dtype=float))

    def r(x):
        return np.concatenate([resid(x), w * (np.asarray(x) - prev)])
    return r
