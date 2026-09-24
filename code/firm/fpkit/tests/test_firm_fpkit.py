"""Acceptance tests of firm.fpkit (Python twin); the C++20 and Rust twins assert the same bit patterns."""
import math
import pathlib
import sys
from fractions import Fraction

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_fpkit import (
    SplitMix64,
    bits,
    cg,
    cholesky,
    fma_exact,
    logsumexp,
    neumaier_sum,
    reference_results,
    reference_vectors,
    thomas,
    welford,
    welford_cov,
)


def test_reference_bits():
    r = reference_results()
    want = {"naive": 0xC1BA1FB24E533D44, "pairwise": 0xC1BA1FB24E533D64, "neumaier": 0xC1BA1FB24E533D69,
            "mean": 0x40C3883FD5280542, "var": 0x3FB4F5102E312730, "lse": 0x407F4AF53BA8F1FB,
            "x0": 0x3FCA6DA43E350286, "xlast": 0x3FD69C02E4172C65}
    assert {k: bits(v) for k, v in r.items()} == want
    g = SplitMix64(1234567)
    assert g.next_u64() == 6457827717110365317


def test_summation_and_moments_against_exact():
    v = reference_vectors()
    exact = float(sum(Fraction(a) for a in v["pnl"]))
    assert neumaier_sum(v["pnl"]) == exact
    x = v["prices"]
    xf = [Fraction(a) for a in x]
    m = sum(xf) / len(x)
    var = float(sum((a - m) ** 2 for a in xf) / (len(x) - 1))
    assert abs(welford(x)[2] / var - 1) < 1e-11
    y = [2 * a + 1 for a in x]
    assert abs(welford_cov(x, y) / (2 * var) - 1) < 1e-10
    assert abs(logsumexp([1000.0, 1000.0]) - (1000 + math.log(2))) < 1e-12 and math.isfinite(logsumexp([-1e4, -1e4]))


def test_thomas_cholesky_cg():
    rng = np.random.default_rng(1)
    n = 50
    a, b, c, d = -np.ones(n), 3 + rng.random(n), -np.ones(n), rng.random(n)
    T = np.diag(b) + np.diag(a[1:], -1) + np.diag(c[:-1], 1)
    assert np.allclose(thomas(a, b, c, d), np.linalg.solve(T, d), atol=1e-13)
    B = rng.standard_normal((20, 20))
    S = B @ B.T + np.eye(20)
    ch = cholesky(S)
    assert ch["ok"] and np.allclose(ch["L"] @ ch["L"].T, S)
    bad = np.array([[1.0, 0.9, 0.2], [0.9, 1.0, 0.9], [0.2, 0.9, 1.0]])
    f = cholesky(bad)
    assert not f["ok"] and f["fail_index"] == 2 and f["pivot"] < 0 and cholesky(bad, jitter=0.5)["ok"]
    rhs = rng.standard_normal(20)
    out = cg(S, rhs, tol=1e-12, max_iter=200)
    assert np.allclose(out["x"], np.linalg.solve(S, rhs), atol=1e-8) and out["iters"] <= 100


def test_fma():
    assert 0.1 * 10.0 - 1.0 == 0.0 and fma_exact(0.1, 10.0, -1.0) == math.ldexp(1.0, -54)
