import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_execcontrol import OWScheduler, aim, liquidity_dp, lqr_signal, simulate  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "acexec"))
from firm_acexec import ACScheduler, discrete  # noqa: E402, I001


def test_lqr_without_signal_is_almgren_chriss():
    n, tau, eta, sigma, lam = 20, 0.05, 0.01, 0.5, 0.1
    g = lqr_signal(n, tau, eta, sigma, lam, phi=0.9)
    x = [1.0]
    for k in range(n):
        x.append(x[-1] - g[k][0] * x[-1])
    assert np.allclose(x, discrete(1.0, 1.0, n, eta, sigma, lam), atol=1e-6)
    assert all(gk[1] < 0 for gk in g[:-1])          # a positive drift slows the sale down


def test_signal_saves_cost_and_ow_and_aim():
    n, tau, eta, sigma, lam, phi, s = 20, 0.05, 0.01, 0.5, 0.1, 0.9, 1.0
    g = lqr_signal(n, tau, eta, sigma, lam, phi)
    ac = lqr_signal(n, tau, eta, sigma, lam, 0.0)

    def with_signal(k, x, a, dp):
        return g[k][0] * x + g[k][1] * a

    def without(k, x, a, dp):
        return ac[k][0] * x
    c1 = simulate(with_signal, 1.0, n, tau, eta, sigma, phi, s, paths=3000)
    c0 = simulate(without, 1.0, n, tau, eta, sigma, phi, s, paths=3000)
    assert c1.mean() < c0.mean()
    ow = OWScheduler(1.0, 3.0, 1.0)
    assert np.isclose(ow.targets([0.0])[0], 1.0) and np.isclose(ow.targets([1e-9])[0], 0.8, atol=1e-6)
    assert np.isclose(ow.targets([1.0])[0], 0.0)
    pol = aim(2.0, 0.5, 0.5, 1.0, 20)
    assert pol(10, 0.5, 0.0, 0.2) > pol(10, 0.5, 0.0, 0.0) > pol(10, 0.5, 0.0, -0.2) > 0
    x = [1.0]
    for k in range(20):
        x.append(x[-1] - pol(k, x[-1], 0.0, 0.0))
    assert np.allclose(x, ACScheduler(1.0, 1.0, 2.0).targets(np.linspace(0, 1, 21)), atol=1e-9)


def test_stochastic_liquidity_sells_more_when_liquid():
    r = liquidity_dp(1.0, 10, 0.1, (0.01, 0.05), 0.5, 0.1, (0.9, 0.8), grid=41)
    k, i = 5, 30
    assert r["policy_normal"][k, i] > r["policy_dry"][k, i]
    assert math.isclose(r["policy_normal"][k, 0], 0.0)
