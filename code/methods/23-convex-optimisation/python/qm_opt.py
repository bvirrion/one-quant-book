"""Book 4, chapter 23: convex optimisation (teaching module).

A long-short portfolio of 200 stocks (the factor covariance of chapter 22, in annual units) with dollar and sector
neutrality, position, gross-exposure and turnover limits, solved by the firm's interior-point QP; shadow prices;
an infeasibility certificate; a risk limit as a second-order cone; the nearest correlation matrix.
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "portopt"))
sys.path.insert(0, str(ROOT / "code" / "methods" / "22-covariance-estimation-and-random-matrices" / "python"))
from firm_portopt import PortfolioProblem, admm, farkas, nearest_correlation, qp  # noqa: E402
from qm_covest import truth  # noqa: E402

N = 200
GAMMA = 10.0
BOX = 0.015
GROSS = 1.0
TURNOVER = 0.20
SECTOR = np.arange(N) // 40


def market(seed: int = 23) -> dict:
    """Annual covariance, yesterday's alphas and portfolio, today's alphas (yesterday's decayed plus news)."""
    rng = np.random.default_rng(seed)
    Sigma = truth() * 252
    a0 = 0.03 * rng.standard_normal(N)
    alpha = 0.8 * a0 + 0.6 * 0.03 * rng.standard_normal(N)
    return {"Sigma": Sigma, "alpha0": a0, "alpha": alpha}


def build(alpha, Sigma, w0, box=BOX, gross=GROSS, turnover=TURNOVER, sector=True, dollar=True):
    p = PortfolioProblem(alpha, Sigma, GAMMA, w0=w0)
    if dollar:
        p.add_budget(0.0, "dollar")
    if sector:
        for k in range(5):
            p.add_neutral((SECTOR == k).astype(float), f"sector{k}")
    if box is not None:
        p.add_box(box, "position")
    if gross is not None:
        p.add_gross(gross, "gross")
    if turnover is not None:
        p.add_turnover(turnover, "turnover")
    return p


_CACHE: dict = {}


def yesterday() -> np.ndarray:
    """Yesterday's portfolio: optimal for yesterday's alphas without a turnover limit."""
    if "w0" not in _CACHE:
        m = market()
        _CACHE["w0"] = build(m["alpha0"], m["Sigma"], np.zeros(N), turnover=None).solve()["w"]
    return _CACHE["w0"]


def today(**kw) -> dict:
    key = ("today", tuple(sorted(kw.items())))
    if key not in _CACHE:
        m = market()
        _CACHE[key] = build(m["alpha"], m["Sigma"], yesterday(), **kw).solve()
    return _CACHE[key]


def constraint_costs() -> dict:
    """Utility lost to each constraint group: re-solve without it; and the multiplier-based first-order estimate."""
    base = today()
    out = {"base": base["objective"]}
    for name, kw in (("turnover", {"turnover": None}), ("gross", {"gross": None}), ("position", {"box": None}),
                     ("sector", {"sector": False}), ("dollar", {"dollar": False})):
        out[name] = today(**kw)["objective"] - base["objective"]
    return out


def turnover_curve(limits=(0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.60, 0.80)) -> list:
    rows = []
    for L in limits:
        r = today(turnover=L)
        rows.append((L, r["objective"], r["expected_return"], r["duals"].get("turnover", 0.0), r["turnover"]))
    return rows


def infeasible() -> dict:
    """Contradictory limits: dollar and sector neutrality, positions within +-0.25%, and a demand that each of
    sector 0's forty stocks be at least 0.5% long (so sector 0 would be at least 20% long). The certificate names the
    rows that clash."""
    n = N
    A = np.vstack([np.ones(n)] + [(SECTOR == k).astype(float) for k in range(5)])
    b = np.zeros(6)
    G = np.vstack([-np.eye(n)[SECTOR == 0], np.eye(n), -np.eye(n)])
    h = np.concatenate([np.full(40, -0.005), np.full(n, 0.0025), np.full(n, 0.0025)])
    cert = farkas(A, b, G, h)
    lam, nu, t = cert
    return {"t": t, "lam": lam, "nu": nu, "stationarity": float(np.linalg.norm(G.T @ lam + A.T @ nu)),
            "value": float(h @ lam + b @ nu), "support": int(np.sum(lam > 1e-6)),
            "lam_min_sector0": float(lam[:40].sum()), "lam_upper": float(lam[40:40 + n].sum()),
            "lam_lower": float(lam[40 + n:].sum())}


def risk_limit(limit: float = 0.04, seed: int = 23) -> dict:
    """max alpha'w s.t. sqrt(w'Sigma w) <= limit, dollar neutral, |w_i| <= BOX, as an SOCP by ADMM; compared with the
    QP max alpha'w - gamma/2 w'Sigma w with gamma found by bisection to give the same risk."""
    m = market(seed)
    Sigma, alpha = m["Sigma"], m["alpha"]
    L = np.linalg.cholesky(Sigma)
    n = N
    # variables x = (w, tau); rows: dollar, boxes, tau fixed, cone [tau; L' w]
    C = np.vstack([np.concatenate([np.ones(n), [0.0]])[None, :],
                   np.hstack([np.eye(n), np.zeros((n, 1))]),
                   np.concatenate([np.zeros(n), [1.0]])[None, :],
                   np.concatenate([np.zeros(n), [1.0]])[None, :],
                   np.hstack([L.T, np.zeros((n, 1))])])
    lo = np.concatenate([[0.0], np.full(n, -BOX), [limit], np.full(n + 1, -np.inf)])
    up = np.concatenate([[0.0], np.full(n, BOX), [limit], np.full(n + 1, np.inf)])
    cone = np.arange(n + 2, 2 * n + 3)
    sol = admm(np.zeros((n + 1, n + 1)), np.concatenate([-alpha, [0.0]]), C, lo, up, cones=[cone], rho=1.0,
               tol=1e-9, max_iter=200_000)
    w_soc = sol["x"][:n]
    mult = float(np.linalg.norm(sol["y"][cone][1:]))                       # dual norm = shadow price of the limit

    def qp_risk(g):
        G = np.vstack([np.eye(n), -np.eye(n)])
        h = np.full(2 * n, BOX)
        x = qp(g * Sigma, -alpha, np.ones((1, n)), np.zeros(1), G, h)["x"]
        return x, math.sqrt(float(x @ Sigma @ x))
    lo_g, hi_g = 1e-3, 1e4
    for _ in range(80):
        g = math.sqrt(lo_g * hi_g)
        _, rk = qp_risk(g)
        if rk > limit:
            lo_g = g
        else:
            hi_g = g
    w_qp, rk = qp_risk(math.sqrt(lo_g * hi_g))
    return {"w_soc": w_soc, "w_qp": w_qp, "ret_soc": float(alpha @ w_soc), "ret_qp": float(alpha @ w_qp),
            "risk_soc": math.sqrt(float(w_soc @ Sigma @ w_soc)), "risk_qp": rk, "gamma": math.sqrt(lo_g * hi_g),
            "multiplier": mult, "gap": float(np.max(np.abs(w_soc - w_qp))), "iters": sol["iters"],
            "status": sol["status"]}


def broken_correlation(n: int = 50, T: int = 60, missing: float = 0.5, seed: int = 24) -> dict:
    """Pairwise-complete correlations of n series with half the observations missing at random: not positive
    semidefinite; its nearest correlation matrix."""
    rng = np.random.default_rng(seed)
    f = rng.standard_normal(T)
    X = 0.6 * f[:, None] + 0.8 * rng.standard_normal((T, n))
    X[rng.random((T, n)) < missing] = np.nan
    C = np.eye(n)
    for i in range(n):
        for j in range(i + 1, n):
            ok = ~np.isnan(X[:, i]) & ~np.isnan(X[:, j])
            C[i, j] = C[j, i] = np.corrcoef(X[ok, i], X[ok, j])[0, 1]
    Y, it = nearest_correlation(C)
    return {"C": C, "Y": Y, "iters": it, "eig_before": np.linalg.eigvalsh(C), "eig_after": np.linalg.eigvalsh(Y),
            "distance": float(np.linalg.norm(C - Y)), "max_change": float(np.max(np.abs(C - Y))),
            "n_negative": int(np.sum(np.linalg.eigvalsh(C) < 0))}
