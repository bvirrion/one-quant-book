"""firm.portopt -- convex portfolio optimisation (One Quant Book 4, chapter 23).

A primal-dual interior-point solver for quadratic programmes
    minimise 1/2 x'Px + q'x   subject to   Ax = b,  Gx <= h,
with Mehrotra's predictor-corrector, KKT residuals and dual variables; a phase-one linear programme that returns a
Farkas infeasibility certificate; an ADMM solver (OSQP-style) for the same objective with constraints Cx in K,
K a product of boxes and second-order cones (tracking-error and risk limits); a formulation layer for long-short
portfolios; and Higham's nearest correlation matrix. NumPy only.

API (stable):
    qp(P, q, A=None, b=None, G=None, h=None, tol=1e-9)    dict(x, y, z, s, status, iters, history, kkt)
    farkas(A, b, G, h)                                   None if feasible, else (lam >= 0, nu) with G'lam + A'nu = 0 and
                                                         h'lam + b'nu < 0
    admm(P, q, C, lower, upper, cones=(), rho=0.1, ...)  dict(x, y, iters, status); cones = list of index arrays whose
                                                         rows of Cx form second-order cones (t, u): |u| <= t
    PortfolioProblem(alpha, Sigma, gamma)                .add_budget, .add_neutral, .add_box, .add_gross, .add_turnover,
                                                         .solve() -> dict(w, objective, expected_return, risk, duals)
    nearest_correlation(C, tol, max_iter)                Higham's alternating projections with Dykstra's correction
"""
from __future__ import annotations

import math

import numpy as np


def _kkt_residuals(P, q, A, b, G, h, x, y, z, s):
    rd = P @ x + q + A.T @ y + G.T @ z
    rp = A @ x - b
    ri = G @ x + s - h
    return rd, rp, ri


def _newton(K, G, n, p, rd, rp, ri, s, z, rc):
    """One Newton direction for the relaxed KKT system, with (s, z) eliminated; K is the reduced KKT matrix."""
    rhs1 = -rd - G.T @ ((-rc + z * ri) / s)
    rhs = np.concatenate([rhs1, -rp]) if p else rhs1
    sol = np.linalg.solve(K, rhs)
    dx, dy = sol[:n], sol[n:]
    ds = -ri - G @ dx
    dz = (-rc - z * ds) / s
    return dx, dy, ds, dz


def _step_len(v, dv) -> float:
    neg = dv < 0
    return min(1.0, float(np.min(-v[neg] / dv[neg]))) if np.any(neg) else 1.0


def qp(P, q, A=None, b=None, G=None, h=None, tol: float = 1e-9, max_iter: int = 100) -> dict:
    P = np.atleast_2d(np.asarray(P, dtype=float))
    q = np.asarray(q, dtype=float)
    n = q.size
    A = np.zeros((0, n)) if A is None else np.atleast_2d(np.asarray(A, dtype=float))
    b = np.zeros(0) if b is None else np.asarray(b, dtype=float)
    G = np.zeros((0, n)) if G is None else np.atleast_2d(np.asarray(G, dtype=float))
    h = np.zeros(0) if h is None else np.asarray(h, dtype=float)
    m, p = G.shape[0], A.shape[0]
    x, y = np.zeros(n), np.zeros(p)
    s, z = np.ones(m), np.ones(m)
    history = []
    status = "max_iter"
    scale = 1 + max(np.abs(q).max(initial=0), np.abs(h).max(initial=0), np.abs(b).max(initial=0))
    for it in range(max_iter):
        rd, rp, ri = _kkt_residuals(P, q, A, b, G, h, x, y, z, s)
        mu = float(s @ z) / m if m else 0.0
        feas = float(np.linalg.norm(np.concatenate([rp, ri])))
        history.append((it, float(np.linalg.norm(rd)), feas, mu))
        if np.linalg.norm(rd) < tol * scale and feas < tol * scale and mu < 1e-3 * tol:
            status = "optimal"
            break
        Hm = P + G.T @ (G * (z / s)[:, None])
        K = np.block([[Hm, A.T], [A, np.zeros((p, p))]]) if p else Hm
        K = K + 1e-12 * np.eye(K.shape[0])
        dx, dy, ds, dz = _newton(K, G, n, p, rd, rp, ri, s, z, s * z)                   # affine (predictor)
        a = min(_step_len(s, ds), _step_len(z, dz)) if m else 1.0
        mu_aff = float((s + a * ds) @ (z + a * dz)) / m if m else 0.0
        sigma = (mu_aff / mu) ** 3 if m and mu > 0 else 0.0
        dx, dy, ds, dz = _newton(K, G, n, p, rd, rp, ri, s, z, s * z + ds * dz - sigma * mu)  # corrector
        a = 0.99 * min(_step_len(s, ds), _step_len(z, dz)) if m else 1.0
        x, y, s, z = x + a * dx, y + a * dy, s + a * ds, z + a * dz
    rd, rp, ri = _kkt_residuals(P, q, A, b, G, h, x, y, z, s)
    kkt = {"stationarity": float(np.linalg.norm(rd)), "primal": float(np.linalg.norm(np.concatenate([rp, ri]))),
           "complementarity": float(s @ z)}
    return {"x": x, "y": y, "z": z, "s": s, "status": status, "iters": len(history), "history": history,
            "kkt": kkt, "objective": float(0.5 * x @ P @ x + q @ x)}


def farkas(A, b, G, h, tol: float = 1e-7):
    """Phase one: minimise t subject to Ax = b, Gx <= h + t. If the optimum t* > 0 the system is infeasible, and the
    duals (lam, nu) satisfy G'lam + A'nu = 0, sum(lam) = 1, h'lam + b'nu = -t* < 0: a Farkas certificate."""
    A, G = np.atleast_2d(np.asarray(A, float)), np.atleast_2d(np.asarray(G, float))
    b, h = np.asarray(b, float), np.asarray(h, float)
    n, m = G.shape[1], G.shape[0]
    Gt = np.hstack([G, -np.ones((m, 1))])
    At = np.hstack([A, np.zeros((A.shape[0], 1))])
    q = np.zeros(n + 1)
    q[-1] = 1.0
    P = 1e-10 * np.eye(n + 1)                          # a whisper of curvature keeps the KKT matrix regular
    t_box = np.zeros(n + 1)
    t_box[-1] = -1.0                                                    # t >= -1 keeps the phase-one problem bounded
    sol = qp(P, q, At, b, np.vstack([Gt, t_box]), np.concatenate([h, [1.0]]), tol=1e-10)
    t = sol["x"][-1]
    if t <= tol:
        return None
    lam, nu = sol["z"][:m], sol["y"]
    return lam, nu, float(t)


def _proj_soc(v):
    t, u = v[0], v[1:]
    nu = float(np.linalg.norm(u))
    if nu <= t:
        return v
    if nu <= -t:
        return np.zeros_like(v)
    a = (nu + t) / 2
    return np.concatenate([[a], a * u / nu])


def admm(P, q, C, lower, upper, cones=(), rho: float = 0.1, sigma: float = 1e-6, alpha: float = 1.6,
         tol: float = 1e-7, max_iter: int = 20_000) -> dict:
    """OSQP-style ADMM for min 1/2 x'Px + q'x s.t. z = Cx, z in K: rows not in a cone must satisfy lower <= z <= upper,
    each index array in `cones` lists rows (t first) that must lie in a second-order cone."""
    P, C = np.atleast_2d(np.asarray(P, float)), np.atleast_2d(np.asarray(C, float))
    q, lower, upper = (np.asarray(v, float) for v in (q, lower, upper))
    n, m = q.size, C.shape[0]
    x, z, y = np.zeros(n), np.zeros(m), np.zeros(m)
    M = P + sigma * np.eye(n) + rho * C.T @ C
    Minv = np.linalg.inv(M)
    in_cone = np.zeros(m, dtype=bool)
    for c in cones:
        in_cone[np.asarray(c)] = True
    status = "max_iter"
    it = 0
    for it in range(1, max_iter + 1):  # noqa: B007 (the count is returned)
        xt = Minv @ (sigma * x - q + C.T @ (rho * z - y))
        zt = C @ xt
        x_new = alpha * xt + (1 - alpha) * x
        v = alpha * zt + (1 - alpha) * z + y / rho
        z_new = np.where(in_cone, v, np.clip(v, lower, upper))
        for c in cones:
            z_new[np.asarray(c)] = _proj_soc(v[np.asarray(c)])
        y = y + rho * (alpha * zt + (1 - alpha) * z - z_new)
        x, z = x_new, z_new
        rp = float(np.linalg.norm(C @ x - z, np.inf))
        rd = float(np.linalg.norm(P @ x + q + C.T @ y, np.inf))
        if rp < tol * (1 + np.abs(z).max()) and rd < tol * (1 + np.abs(q).max()):
            status = "optimal"
            break
    return {"x": x, "y": y, "z": z, "iters": it, "status": status, "objective": float(0.5 * x @ P @ x + q @ x)}


class PortfolioProblem:
    """max alpha'w - gamma/2 w'Sigma w with linear constraints, as a QP in (w, u, v) where w - w0 = u - v for the
    turnover and w = a - c for the gross exposure (all split variables nonnegative)."""

    def __init__(self, alpha, Sigma, gamma: float, w0=None):
        self.alpha, self.Sigma, self.gamma = np.asarray(alpha, float), np.asarray(Sigma, float), float(gamma)
        self.n = self.alpha.size
        self.w0 = np.zeros(self.n) if w0 is None else np.asarray(w0, float)
        self.eq, self.ineq, self.names = [], [], {}

    def add_budget(self, total: float = 0.0, name: str = "budget"):
        self.eq.append((name, np.ones(self.n), total))

    def add_neutral(self, exposures, name: str):
        self.eq.append((name, np.asarray(exposures, float), 0.0))

    def add_box(self, bound: float, name: str = "position"):
        self.box = (bound, name)

    def add_gross(self, limit: float, name: str = "gross"):
        self.gross = (limit, name)

    def add_turnover(self, limit: float, name: str = "turnover"):
        self.turnover = (limit, name)

    def solve(self, tol: float = 1e-9) -> dict:
        n = self.n
        N = 5 * n                                                   # w, a, c (gross split), u, v (turnover split)
        P = np.zeros((N, N))
        P[:n, :n] = self.gamma * self.Sigma
        q = np.zeros(N)
        q[:n] = -self.alpha
        A_rows, b_vals, eq_names = [], [], []
        for name, row, val in self.eq:
            r = np.zeros(N)
            r[:n] = row
            A_rows.append(r)
            b_vals.append(val)
            eq_names.append(name)
        link_g = np.hstack([np.eye(n), -np.eye(n), np.eye(n), np.zeros((n, 2 * n))])     # w - a + c = 0
        link_t = np.hstack([np.eye(n), np.zeros((n, 2 * n)), -np.eye(n), np.eye(n)])    # w - u + v = w0
        A = np.vstack([np.array(A_rows).reshape(-1, N), link_g, link_t])
        b = np.concatenate([b_vals, np.zeros(n), self.w0])
        G_rows, h_vals, ineq_names = [], [], []
        bound, bname = getattr(self, "box", (None, None))
        if bound is not None:
            G_rows += [np.hstack([np.eye(n), np.zeros((n, 4 * n))]), np.hstack([-np.eye(n), np.zeros((n, 4 * n))])]
            h_vals += [np.full(n, bound), np.full(n, bound)]
            ineq_names += [bname] * (2 * n)
        G_rows.append(np.hstack([np.zeros((4 * n, n)), -np.eye(4 * n)]))                   # a, c, u, v >= 0
        h_vals.append(np.zeros(4 * n))
        ineq_names += ["nonneg"] * (4 * n)
        glim, gname = getattr(self, "gross", (None, None))
        if glim is not None:
            G_rows.append(np.concatenate([np.zeros(n), np.ones(2 * n), np.zeros(2 * n)])[None, :])
            h_vals.append([glim])
            ineq_names.append(gname)
        tlim, tname = getattr(self, "turnover", (None, None))
        if tlim is not None:
            G_rows.append(np.concatenate([np.zeros(3 * n), np.ones(2 * n)])[None, :])
            h_vals.append([tlim])
            ineq_names.append(tname)
        G, h = np.vstack(G_rows), np.concatenate(h_vals)
        sol = qp(P, q, A, b, G, h, tol=tol)
        w = sol["x"][:n]
        duals = {}
        for k, name in enumerate(eq_names):
            duals[name] = float(sol["y"][k])
        names = np.array(ineq_names)
        for name in set(ineq_names) - {"nonneg"}:
            duals[name] = float(np.sum(sol["z"][names == name]))
        return {"w": w, "objective": -sol["objective"], "expected_return": float(self.alpha @ w),
                "risk": math.sqrt(float(w @ self.Sigma @ w)), "duals": duals, "status": sol["status"],
                "iters": sol["iters"], "kkt": sol["kkt"], "history": sol["history"],
                "gross": float(np.abs(w).sum()), "turnover": float(np.abs(w - self.w0).sum()),
                "binding_positions": int(np.sum(np.abs(w) > (bound - 1e-6))) if bound is not None else 0,
                "qp": (P, q, A, b, G, h)}


def nearest_correlation(C, tol: float = 1e-10, max_iter: int = 10_000) -> tuple[np.ndarray, int]:
    """Higham (2002): alternate projections onto the positive semidefinite cone and the unit-diagonal set, with
    Dykstra's correction on the semidefinite step, to the nearest correlation matrix in the Frobenius norm."""
    Y = np.asarray(C, dtype=float).copy()
    dS = np.zeros_like(Y)
    for it in range(1, max_iter + 1):
        R = Y - dS
        lam, V = np.linalg.eigh((R + R.T) / 2)
        X = (V * np.maximum(lam, 0)) @ V.T
        dS = X - R
        Y_new = X.copy()
        np.fill_diagonal(Y_new, 1.0)
        if np.linalg.norm(Y_new - Y) < tol * np.linalg.norm(Y):
            return Y_new, it
        Y = Y_new
    return Y, max_iter
