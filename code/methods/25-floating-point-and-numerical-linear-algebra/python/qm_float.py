"""Book 4, chapter 25: floating point and numerical linear algebra (teaching module).

The Vancouver index's truncation drift, summation of many P&L entries, variance on large offsets, conditioning and
the normal equations, Cholesky on a pairwise correlation matrix, and conjugate gradient with and without a
preconditioner.
"""
from __future__ import annotations

import math
import pathlib
import sys
from fractions import Fraction

import numpy as np

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "fpkit"))
from firm_fpkit import SplitMix64, cg, cholesky, fma_exact, naive_sum, neumaier_sum, pairwise_sum, welford  # noqa: E402

UPDATES_PER_DAY = 2400            # "about 3,000" reported; 25 points a month of drift implies about 2,400
DAYS = 480                         # about 22.7 months of trading days, January 1982 to late November 1983
START, TRUE_END = 1000.0, 1098.892
DOCUMENTED = (524.811, 1098.892)   # Friday close before the correction, and the corrected value


def vancouver(seed: int = 1982, updates_per_day: int = UPDATES_PER_DAY, days: int = DAYS,
              mode: str = "truncate") -> dict:
    """Index recomputed after every trade: exact (no rounding), truncated to three decimals, or rounded."""
    rng = np.random.default_rng(seed)
    n = updates_per_day * days
    sigma = 0.01 / math.sqrt(updates_per_day)
    eps = rng.standard_normal(n) * sigma
    eps += (math.log(TRUE_END / START) - eps.sum()) / n          # the exact index ends at the corrected value
    growth = np.exp(eps)
    exact = START * float(np.prod(growth))
    idx = START
    path, exact_path = [START], [START]
    e = START
    for k in range(n):
        x = idx * growth[k]
        idx = math.floor(x * 1000) / 1000 if mode == "truncate" else round(x, 3)
        e *= growth[k]
        if (k + 1) % updates_per_day == 0:
            path.append(idx)
            exact_path.append(e)
    return {"final": idx, "exact": exact, "n": n, "path": np.array(path), "exact_path": np.array(exact_path)}


def expected_drift(updates: int) -> float:
    """Truncating to three decimals removes, on average, half a thousandth per recalculation."""
    return 0.0005 * updates


# --- summation ------------------------------------------------------------------------------------------

def pnl_entries(n: int, seed: int = 25) -> list[float]:
    g = SplitMix64(seed)
    scale = (1.0, 10.0, 100.0, 1000.0, 10000.0, 100000.0, 1000000.0)
    return [(g.uniform() - 0.5) * scale[i % 7] for i in range(n)]


def summation_errors(ns=(1_000, 10_000, 100_000, 1_000_000)) -> list[tuple]:
    rows = []
    for n in ns:
        x = pnl_entries(n)
        exact = sum(Fraction(v) for v in x)
        err = [abs(Fraction(f(x)) - exact) for f in (naive_sum, pairwise_sum, neumaier_sum)]
        rows.append((n, float(err[0]), float(err[1]), float(err[2]), float(exact)))
    return rows


# --- variance on an offset ------------------------------------------------------------------------------

def variance_errors(offsets=(1.0, 1e2, 1e4, 1e6, 1e8), n: int = 10_000, seed: int = 7) -> list[tuple]:
    """Relative error of three variance formulas on offset + U(0, 1) data: the textbook one-pass
    E[x^2] - E[x]^2, the two-pass formula, and Welford's update."""
    g = SplitMix64(seed)
    u = [g.uniform() for _ in range(n)]
    rows = []
    for c in offsets:
        x = [c + v for v in u]
        xf = [Fraction(v) for v in x]
        m = sum(xf) / n
        exact = sum((v - m) ** 2 for v in xf) / (n - 1)
        s1 = naive_sum(x)
        s2 = naive_sum([v * v for v in x])
        textbook = (s2 - s1 * s1 / n) / (n - 1)
        mean = s1 / n
        two_pass = naive_sum([(v - mean) ** 2 for v in x]) / (n - 1)
        wf = welford(x)[2]
        rel = [abs(Fraction(v) - exact) / exact if math.isfinite(v) else Fraction(1) for v in (textbook, two_pass, wf)]
        rows.append((c, float(rel[0]), float(rel[1]), float(rel[2]), textbook, float(exact)))
    return rows


# --- conditioning and the normal equations ----------------------------------------------------------------

def normal_equations(conds=(1e1, 1e2, 1e3, 1e4, 1e5, 1e6, 1e7), n: int = 500, seed: int = 3) -> list[tuple]:
    """Least squares with a design of prescribed condition number: relative error of the coefficients from the
    normal equations (Cholesky of X'X) and from QR, for an exactly consistent right-hand side."""
    rng = np.random.default_rng(seed)
    U, _ = np.linalg.qr(rng.standard_normal((n, 5)))
    V, _ = np.linalg.qr(rng.standard_normal((5, 5)))
    beta = np.array([1.0, -2.0, 0.5, 3.0, -1.0])
    rows = []
    for k in conds:
        s = np.geomspace(1.0, 1.0 / k, 5)
        X = (U * s) @ V.T
        y = X @ beta
        ne = np.linalg.solve(X.T @ X, X.T @ y)
        Q, R = np.linalg.qr(X)
        qr = np.linalg.solve(R, Q.T @ y)
        rows.append((k, float(np.linalg.norm(ne - beta) / np.linalg.norm(beta)),
                     float(np.linalg.norm(qr - beta) / np.linalg.norm(beta)), float(np.linalg.cond(X.T @ X))))
    return rows


def cholesky_on_pairwise() -> dict:
    sys.path.insert(0, str(ROOT / "code" / "methods" / "23-convex-optimisation" / "python"))
    from qm_opt import broken_correlation
    b = broken_correlation()
    C = b["C"]
    raw = cholesky(C)
    jit = None
    for j in (1e-3, 1e-2, 0.1, 0.5, 1.0, 2.0):
        if cholesky(C, jitter=j)["ok"]:
            jit = j
            break
    fixed = cholesky(b["Y"] + 1e-8 * np.eye(C.shape[0]))
    return {"ok": raw["ok"], "fail_index": raw["fail_index"], "pivot": raw["pivot"], "jitter_needed": jit,
            "fixed_ok": fixed["ok"], "min_eig": float(np.linalg.eigvalsh(C).min())}


def cg_demo(n: int = 400, seed: int = 4) -> dict:
    """An SPD system with condition number about 10^4 and a badly scaled diagonal: conjugate gradient with and
    without a Jacobi preconditioner."""
    rng = np.random.default_rng(seed)
    Q, _ = np.linalg.qr(rng.standard_normal((n, n)))
    lam = np.geomspace(1.0, 1e-2, n)
    A0 = (Q * lam) @ Q.T
    D = np.diag(np.geomspace(1.0, 100.0, n))
    A = D @ A0 @ D
    b = rng.standard_normal(n)
    plain = cg(A, b, tol=1e-8, max_iter=5 * n)
    pre = cg(A, b, tol=1e-8, max_iter=5 * n, precond=1.0 / np.diag(A))
    return {"cond": float(np.linalg.cond(A)), "iters_plain": plain["iters"], "iters_pre": pre["iters"],
            "res_plain": plain["residuals"], "res_pre": pre["residuals"],
            "cond_pre": float(np.linalg.cond(A / np.sqrt(np.outer(np.diag(A), np.diag(A)))))}


def fma_example() -> dict:
    return {"separate": 0.1 * 10.0 - 1.0, "fused": fma_exact(0.1, 10.0, -1.0), "two_pow": math.ldexp(1.0, -54)}
