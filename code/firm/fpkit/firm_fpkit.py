"""firm.fpkit -- floating-point and numerical linear algebra kit (One Quant Book 4, chapter 25).

Summation (naive, pairwise, Neumaier), Welford's streaming mean, variance and covariance, log-sum-exp, the Thomas
tridiagonal solver, Cholesky with a failure diagnostic and optional jitter, conjugate gradient, an exact fused
multiply-add reference, and the SplitMix64 stream that the C++20 and Rust twins share. The scalar routines are written
to perform the same floating-point operations in the same order in all three languages, so their results agree bit
for bit (no fused multiply-add, no reassociation). NumPy only for the matrix routines.

API (stable):
    SplitMix64(seed).next_u64(), .uniform()
    naive_sum(x), pairwise_sum(x), neumaier_sum(x)
    welford(x) -> (n, mean, var)          var with divisor n - 1
    welford_cov(x, y) -> cov              divisor n - 1
    logsumexp(x)
    thomas(a, b, c, d)                     sub-, main, super-diagonal (a[0], c[-1] unused) and right-hand side
    cholesky(A, jitter=0.0)               dict(L, ok, fail_index, pivot)
    cg(A, b, tol, max_iter, precond=None) dict(x, iters, residuals)
    fma_exact(a, b, c)                    a * b + c rounded once (exact rational arithmetic)
    bits(x)                               the IEEE 754 binary64 bit pattern as an int
"""
from __future__ import annotations

import math
import struct
from fractions import Fraction

import numpy as np

MASK = (1 << 64) - 1


class SplitMix64:
    def __init__(self, seed: int):
        self.state = seed & MASK

    def next_u64(self) -> int:
        self.state = (self.state + 0x9E3779B97F4A7C15) & MASK
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
        return z ^ (z >> 31)

    def uniform(self) -> float:
        return ((self.next_u64() >> 11) + 0.5) * (1.0 / (1 << 53))


def bits(x: float) -> int:
    return struct.unpack("<Q", struct.pack("<d", float(x)))[0]


def naive_sum(x) -> float:
    s = 0.0
    for v in x:
        s += float(v)
    return s


def pairwise_sum(x, block: int = 8) -> float:
    """Recursive halving down to blocks of `block`, summed left to right: error O(log n) instead of O(n)."""
    x = [float(v) for v in x]

    def rec(lo: int, hi: int) -> float:
        if hi - lo <= block:
            s = 0.0
            for i in range(lo, hi):
                s += x[i]
            return s
        mid = lo + (hi - lo) // 2
        return rec(lo, mid) + rec(mid, hi)
    return rec(0, len(x)) if x else 0.0


def neumaier_sum(x) -> float:
    """Kahan's compensated summation in Neumaier's form: the rounding error of each addition is carried in c."""
    s, c = 0.0, 0.0
    for v in x:
        v = float(v)
        t = s + v
        if abs(s) >= abs(v):
            c += (s - t) + v
        else:
            c += (v - t) + s
        s = t
    return s + c


def welford(x) -> tuple[int, float, float]:
    n, mean, m2 = 0, 0.0, 0.0
    for v in x:
        v = float(v)
        n += 1
        d = v - mean
        mean += d / n
        m2 += d * (v - mean)
    return n, mean, (m2 / (n - 1) if n > 1 else math.nan)


def welford_cov(x, y) -> float:
    n, mx, my, c = 0, 0.0, 0.0, 0.0
    for u, v in zip(x, y, strict=True):
        u, v = float(u), float(v)
        n += 1
        dx = u - mx
        mx += dx / n
        my += (v - my) / n
        c += dx * (v - my)
    return c / (n - 1) if n > 1 else math.nan


def logsumexp(x) -> float:
    x = [float(v) for v in x]
    m = max(x)
    if math.isinf(m):
        return m
    s = 0.0
    for v in x:
        s += math.exp(v - m)
    return m + math.log(s)


def thomas(a, b, c, d) -> list[float]:
    """Solve the tridiagonal system with sub-diagonal a (a[0] unused), diagonal b, super-diagonal c (c[-1] unused)."""
    n = len(b)
    cp, dp = [0.0] * n, [0.0] * n
    cp[0] = float(c[0]) / float(b[0])
    dp[0] = float(d[0]) / float(b[0])
    for i in range(1, n):
        m = float(b[i]) - float(a[i]) * cp[i - 1]
        cp[i] = float(c[i]) / m if i < n - 1 else 0.0
        dp[i] = (float(d[i]) - float(a[i]) * dp[i - 1]) / m
    x = [0.0] * n
    x[-1] = dp[-1]
    for i in range(n - 2, -1, -1):
        x[i] = dp[i] - cp[i] * x[i + 1]
    return x


def cholesky(A, jitter: float = 0.0) -> dict:
    """A = L L'. Stops at the first non-positive pivot and reports where; `jitter` adds jitter * mean(diag) to the
    diagonal."""
    A = np.array(A, dtype=float)
    n = A.shape[0]
    A = A + jitter * float(np.mean(np.diag(A))) * np.eye(n)
    L = np.zeros_like(A)
    for j in range(n):
        piv = A[j, j] - float(L[j, :j] @ L[j, :j])
        if piv <= 0:
            return {"L": L, "ok": False, "fail_index": j, "pivot": piv}
        L[j, j] = math.sqrt(piv)
        L[j + 1:, j] = (A[j + 1:, j] - L[j + 1:, :j] @ L[j, :j]) / L[j, j]
    return {"L": L, "ok": True, "fail_index": -1, "pivot": float(L[-1, -1] ** 2)}


def cg(A, b, tol: float = 1e-10, max_iter: int | None = None, precond=None) -> dict:
    """Conjugate gradient for symmetric positive-definite A; precond, if given, is the inverse diagonal (Jacobi)."""
    A, b = np.asarray(A, dtype=float), np.asarray(b, dtype=float)
    n = b.size
    max_iter = n if max_iter is None else max_iter
    x = np.zeros(n)
    r = b.copy()
    z = r * precond if precond is not None else r.copy()
    p = z.copy()
    rz = float(r @ z)
    res = [float(np.linalg.norm(r))]
    it = 0
    for it in range(1, max_iter + 1):  # noqa: B007 (the count is returned)
        Ap = A @ p
        alpha = rz / float(p @ Ap)
        x += alpha * p
        r -= alpha * Ap
        res.append(float(np.linalg.norm(r)))
        if res[-1] < tol * res[0]:
            break
        z = r * precond if precond is not None else r
        rz_new = float(r @ z)
        p = z + (rz_new / rz) * p
        rz = rz_new
    return {"x": x, "iters": it, "residuals": res}


def fma_exact(a: float, b: float, c: float) -> float:
    return float(Fraction(a) * Fraction(b) + Fraction(c))


POW10 = (1.0, 10.0, 100.0, 1000.0, 10000.0, 100000.0, 1000000.0, 10000000.0, 100000000.0)


def reference_vectors() -> dict:
    """The cross-language test data: P&L-like values over nine orders of magnitude, prices near 10,000, exponents for
    log-sum-exp, and a diagonally dominant tridiagonal system; all from SplitMix64 so C++20 and Rust rebuild them."""
    g = SplitMix64(2025)
    pnl = [(g.uniform() - 0.5) * POW10[i % 9] for i in range(10_000)]
    g = SplitMix64(7)
    prices = [10000.0 + g.uniform() for _ in range(10_000)]
    g = SplitMix64(11)
    expo = [1000.0 * (g.uniform() - 0.5) for _ in range(1000)]
    g = SplitMix64(13)
    n = 100
    b = [2.5 + g.uniform() for _ in range(n)]
    d = [g.uniform() for _ in range(n)]
    return {"pnl": pnl, "prices": prices, "expo": expo, "a": [-1.0] * n, "b": b, "c": [-1.0] * n, "d": d}


def reference_results() -> dict:
    v = reference_vectors()
    x = thomas(v["a"], v["b"], v["c"], v["d"])
    n, mean, var = welford(v["prices"])
    return {"naive": naive_sum(v["pnl"]), "pairwise": pairwise_sum(v["pnl"]), "neumaier": neumaier_sum(v["pnl"]),
            "mean": mean, "var": var, "lse": logsumexp(v["expo"]), "x0": x[0], "xlast": x[-1]}
