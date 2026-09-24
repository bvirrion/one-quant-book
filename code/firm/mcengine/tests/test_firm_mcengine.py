"""Acceptance tests of firm.mcengine (Python), stage 1: Brownian paths and bridges."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_mcengine import (
    NormalStream,
    SplitMix64,
    bridge_crossing_probability,
    bridge_paths,
    brownian_paths,
    reference_path,
)


def test_splitmix_test_vector_and_reference_stream():
    g = SplitMix64(1234567)
    assert [g.next_u64() for _ in range(5)] == [6457827717110365317, 3203168211198807973, 9817491932198370423,
                                                4593380528125082431, 16408922859458223821]
    s = NormalStream(42)
    assert [s.next() for _ in range(2)] == [0.41471975043153037, 0.6526812221519428]
    assert reference_path(4, 1.0, 7)[4] == 0.44269661601997956          # also asserted in C++ and Rust


def test_increment_paths_have_brownian_covariance():
    w = brownian_paths(40_000, 8, 2.0, seed=1)
    assert w.shape == (40_000, 9) and np.all(w[:, 0] == 0)
    assert abs(w[:, 8].var() - 2.0) < 0.05
    assert abs(np.mean(w[:, 4] * w[:, 8]) - 1.0) < 0.03                    # Cov(W_s, W_t) = min(s, t)


def test_correlated_paths():
    c = np.array([[1.0, 0.6], [0.6, 1.0]])
    w = brownian_paths(40_000, 4, 1.0, seed=2, corr=c)
    assert w.shape == (40_000, 5, 2)
    assert abs(np.corrcoef(w[:, 4, 0], w[:, 4, 1])[0, 1] - 0.6) < 0.02


def test_bridge_construction_has_the_same_law():
    b = bridge_paths(40_000, 3, 2.0, seed=3)
    assert abs(b[:, 8].var() - 2.0) < 0.05 and abs(b[:, 4].var() - 1.0) < 0.03
    assert abs(np.mean(b[:, 2] * b[:, 6]) - 0.5) < 0.03                    # min(0.5, 1.5)
    inc = np.diff(b, axis=1)
    assert np.all(np.abs(inc.var(axis=0) - 0.25) < 0.01)


def test_crossing_probability_against_fine_simulation():
    """A bridge from 0.3 to 0.2 over unit variance touches 0 with probability exp(-0.12)."""
    rng = np.random.default_rng(4)
    n, m = 20_000, 2000
    z = rng.standard_normal((n, m)) / math.sqrt(m)
    w = np.cumsum(z, axis=1)
    t = np.arange(1, m + 1) / m
    bridge = 0.3 + w - t * w[:, -1:] + t * (0.2 - 0.3)
    hit = (bridge.min(axis=1) <= 0).mean()
    p = float(bridge_crossing_probability(0.3, 0.2, 0.0, 1.0))
    assert abs(p - math.exp(-0.12)) < 1e-15
    assert abs(hit - p) < 0.03                                              # discrete grid slightly under
    assert float(bridge_crossing_probability(0.5, -0.1, 0.0, 1.0)) == 1.0


# ---- stage 2 ------------------------------------------------------------------------------
from firm_mcengine import euler_maruyama, feller_ratio, ou_exact, sqrt_euler, sqrt_exact  # noqa: E402


def test_ou_exact_stationary_law():
    x = ou_exact(1.0, 2.0, 0.1, 0.4, 5.0, 10, 40_000, seed=5)[:, -1]
    assert abs(x.mean() - 0.1) < 0.005 and abs(x.var() - 0.04) < 0.002


def test_euler_converges_to_the_exact_ou_mean():
    x = euler_maruyama(lambda t, x: 2.0 * (0.1 - x), lambda t, x: 0.4 + 0 * x, 1.0, 0.5, 400, 20_000, seed=6)
    assert abs(x[:, -1].mean() - (0.1 + 0.9 * np.exp(-1.0))) < 0.01


def test_sqrt_exact_moments_and_positivity():
    v = sqrt_exact(0.04, 2.0, 0.04, 0.6, 1.0, 12, 40_000, seed=7)
    assert np.all(v >= 0) and abs(v[:, -1].mean() - 0.04) < 0.002
    # stationary variance vbar eta^2 / (2 kappa) = 0.0036
    assert abs(sqrt_exact(0.04, 2.0, 0.04, 0.6, 5.0, 10, 40_000, seed=8)[:, -1].var() - 0.0036) < 0.0004


def test_sqrt_euler_schemes():
    plain = sqrt_euler(0.04, 2.0, 0.04, 0.6, 1.0, 252, 4000, seed=9)
    ft = sqrt_euler(0.04, 2.0, 0.04, 0.6, 1.0, 252, 4000, seed=9, scheme="full_truncation")
    assert np.isnan(plain).any(axis=1).mean() > 0.05
    assert not np.isnan(ft).any() and ft.min() >= 0
    assert abs(feller_ratio(2.0, 0.04, 0.6) - 4 / 9) < 1e-15


# --- stage 3 (chapter 26) --------------------------------------------------------------------------

def test_philox_matches_numpy_and_is_counter_based():
    from firm_mcengine import philox4x64, philox_uniforms
    raw = np.random.Philox(key=np.array([7, 0], dtype=np.uint64)).random_raw(8)   # NumPy counts from 1
    assert list(philox4x64((1, 0, 0, 0), (7, 0))) == [int(x) for x in raw[:4]]
    assert list(philox4x64((2, 0, 0, 0), (7, 0))) == [int(x) for x in raw[4:]]
    assert [hex(x) for x in philox4x64((0, 0, 0, 0), (2600, 0))][0] == "0x6574e96a9536cfeb"   # C++ and Rust too
    whole = philox_uniforms(1000, 9, seed=5)
    part = philox_uniforms(300, 9, seed=5, first_path=700)
    assert np.array_equal(whole[700:], part)                      # any split of paths gives the same numbers
    assert abs(whole.mean() - 0.5) < 0.01 and not np.array_equal(whole, philox_uniforms(1000, 9, seed=5, stream=1))


def test_sobol_reference_points_and_scrambling():
    from firm_mcengine import owen_scramble, sobol_points
    X = sobol_points(10, 3) / 2.0**32
    want = [[0, 0, 0], [0.5, 0.5, 0.5], [0.75, 0.25, 0.25], [0.25, 0.75, 0.75], [0.375, 0.375, 0.625],
            [0.875, 0.875, 0.125], [0.625, 0.125, 0.875], [0.125, 0.625, 0.375], [0.1875, 0.3125, 0.9375],
            [0.6875, 0.8125, 0.4375]]                              # Joe and Kuo's published output of sobol.cc
    assert np.array_equal(X, np.array(want))
    Xi = sobol_points(16, 8)
    Y = (owen_scramble(Xi, 2600) * 2.0**32 - 0.5).astype(np.uint64)
    assert (int(Y.sum()), int(Y[5, 3]), int(Y[15, 7])) == (275744286821, 1066785506, 4087102229)
    # a scrambled (0, m, 2)-net: 2^8 points in dimensions 1-2, one per dyadic box of area 2^-8, all shapes
    U = owen_scramble(sobol_points(256, 2), 17)
    for a in range(9):
        cells = (np.floor(U[:, 0] * 2**a) * 2 ** (8 - a) + np.floor(U[:, 1] * 2 ** (8 - a))).astype(int)
        assert np.unique(cells).size == 256
    means = [owen_scramble(sobol_points(64, 4), s).mean() for s in range(200)]
    assert abs(np.mean(means) - 0.5) < 3 * np.std(means) / math.sqrt(200) + 1e-12


def test_inverse_normal_and_bridge():
    import statistics

    from firm_mcengine import bridge_from_normals, increment_from_normals, norm_ppf
    p = np.concatenate([np.linspace(1e-12, 1e-3, 500), np.linspace(1e-3, 1 - 1e-3, 5000)])
    ref = np.array([statistics.NormalDist().inv_cdf(x) for x in p])
    assert np.max(np.abs(norm_ppf(p) - ref)) < 1e-8 and np.allclose(norm_ppf(1 - p), -norm_ppf(p), atol=1e-8)
    Z = np.random.default_rng(3).standard_normal((100_000, 16))
    for W in (bridge_from_normals(Z, 2.0), increment_from_normals(Z, 2.0)):
        t = np.linspace(0, 2.0, 17)
        C = np.cov(W[:, 1:].T)
        assert np.allclose(C, np.minimum.outer(t[1:], t[1:]), atol=0.03)
    assert np.allclose(bridge_from_normals(Z, 2.0)[:, 16], math.sqrt(2.0) * Z[:, 0])


def test_asian_control_variate_and_mlmc():
    from firm_mcengine import asian_payoffs, control_variate, geometric_asian_price, increment_from_normals, mlmc
    Z = np.random.default_rng(9).standard_normal((200_000, 12))
    a, g = asian_payoffs(increment_from_normals(Z, 1.0), 100.0, 95.0, 0.02, 0.3, 1.0)
    geo = geometric_asian_price(100.0, 95.0, 0.02, 0.3, 1.0, 12)
    assert abs(g.mean() - geo) < 3 * g.std() / math.sqrt(g.size)
    assert np.all(a >= g - 1e-12)                                  # arithmetic mean >= geometric mean
    cv = control_variate(a, g, geo)
    assert cv["rho"] > 0.99 and cv["se"] < 0.2 * a.std() / math.sqrt(a.size)
    # one-step geometric average: n = 1 is the Black-Scholes call
    d1 = (math.log(100 / 95) + (0.02 + 0.045) * 1.0) / 0.3
    bs = 100 * 0.5 * math.erfc(-d1 / math.sqrt(2)) - 95 * math.exp(-0.02) * 0.5 * math.erfc(-(d1 - 0.3) / math.sqrt(2))
    assert abs(geometric_asian_price(100.0, 95.0, 0.02, 0.3, 1.0, 1) - bs) < 1e-12
    rng = np.random.default_rng(1)

    def sampler(lev, n):                                           # E Y_l = 2^-l, Var Y_l = 4^-l: a known answer
        return 2.0**-lev * (1 + rng.standard_normal(n)), float(2**lev)

    res = mlmc(sampler, 0.01, L0=2, N0=1000)
    assert res["L"] >= 7 and abs(res["est"] - (2 - 2.0 ** -res["L"])) < 0.03
    assert res["N"][0] > res["N"][-1]
