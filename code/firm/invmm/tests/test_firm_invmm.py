import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_invmm as m  # noqa: E402


def test_as_closed_form():
    r, half, b, a = m.as_quotes(100.0, 2, 0.5, 0.1, 2.0, 1.5)
    assert math.isclose(r, 100.0 - 2 * 0.1 * 4.0 * 0.5)
    assert math.isclose(half, 0.5 * (0.1 * 4.0 * 0.5 + 20.0 * math.log(1 + 0.1 / 1.5)))
    assert math.isclose(a - b, 2 * half)


def test_cj_symmetry_and_skew():
    sol = m.CJSolution(A=1.0, k=2.0, phi=0.01, alpha=0.05, qmax=5, T=60.0, n=120)
    b0, a0 = sol.depths(0.0, 0)
    assert math.isclose(b0, a0, rel_tol=1e-9)                 # flat: symmetric
    bl, al = sol.depths(0.0, 3)
    assert al < a0 < bl                                        # long: sell cheaper, buy lower
    bs, as_ = sol.depths(0.0, -3)
    assert math.isclose(bl, as_, rel_tol=1e-9) and math.isclose(al, bs, rel_tol=1e-9)
    assert np.isnan(sol.depths(0.0, 5)[0]) and np.isnan(sol.depths(0.0, -5)[1])


def test_cj_zero_penalty_is_the_monopoly_depth_far_from_the_end():
    sol = m.CJSolution(A=1.0, k=2.0, phi=0.0, alpha=0.0, qmax=20, T=600.0, n=600)
    b, a = sol.depths(0.0, 0)
    assert abs(b - 0.5) < 2e-3 and abs(a - 0.5) < 2e-3        # inventory bounds tilt it slightly


def test_intensity_recovered():
    rng = np.random.default_rng(3)
    d = np.array([0.0, 0.5, 1.0, 1.5, 2.0])
    t = np.full(5, 2000.0)
    f = rng.poisson(0.8 * np.exp(-1.3 * d) * t)
    A, k = m.estimate_intensity(d, t, f)
    assert abs(A - 0.8) < 0.08 and abs(k - 1.3) < 0.1


def test_simulator_common_random_numbers_and_accounting():
    kw = dict(T=50.0, dt=0.1, sigma=0.3, A=1.0, k=2.0, paths=400, seed=5)
    a = m.simulate(m.symmetric(0.5), **kw)
    b = m.simulate(m.symmetric(0.5), **kw)
    assert np.array_equal(a["pnl"], b["pnl"])
    assert abs(a["fills"].mean() - 2 * 50 * math.exp(-1.0)) < 2.0       # 2 A e^{-k delta} T
    assert np.all(np.abs(a["spread_paid"] - 0.5 * a["fills"]) < 1e-9)


def test_touch_solution_posts_less_when_loaded():
    sol = m.TouchSolution(lam=0.03, c=0.05, phi=1e-4, alpha=0.0, qmax=10, T=3600.0, n=3600)
    assert sol.post(0.0, 0) == (True, True)
    b, a = sol.post(0.0, 10)
    assert not b and a                                          # at the bound: never buy
    long_side = [q for q in range(11) if not sol.post(0.0, q)[0]]
    assert long_side and all(sol.post(0.0, -q)[1] is False for q in long_side)   # symmetric
    free = m.TouchSolution(lam=0.03, c=0.05, phi=0.0, alpha=0.0, qmax=10, T=3600.0, n=3600)
    assert all(free.post(0.0, q)[0] for q in range(10))        # no penalty: always post, up to the bound
