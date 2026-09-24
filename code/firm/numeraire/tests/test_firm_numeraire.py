"""Acceptance tests of firm.numeraire."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_numeraire import change_of_numeraire_weights, deflated_martingale_test, girsanov_weights, reweighted_mean


def test_cameron_martin_shifts_the_mean_not_the_variance():
    rng = np.random.default_rng(1)
    w = rng.standard_normal(400_000)
    z = girsanov_weights(w[:, None], 0.7, 1.0)
    mean, se = reweighted_mean(w, z)
    assert abs(z.mean() - 1) < 0.01 and abs(mean - 0.7) < 4 * se
    var = np.mean(z * (w - 0.7) ** 2)
    assert abs(var - 1) < 0.02


def test_ou_short_rate_bonds_are_martingales_after_discounting():
    rng = np.random.default_rng(2)
    n, steps, T, kappa, rbar, sigma, r0 = 40_000, 40, 4.0, 0.5, 0.04, 0.01, 0.03
    dt = T / steps
    a = math.exp(-kappa * dt)
    sd = sigma * math.sqrt((1 - a * a) / (2 * kappa))
    r = np.full(n, r0)
    bank = np.ones((n, steps + 1))
    rates = np.empty((n, steps + 1))
    rates[:, 0] = r
    for k in range(steps):
        r_new = rbar + (r - rbar) * a + sd * rng.standard_normal(n)
        bank[:, k + 1] = bank[:, k] * np.exp(0.5 * (r + r_new) * dt)
        r = r_new
        rates[:, k + 1] = r
    tau = T - np.arange(steps + 1) * dt
    B = (1 - np.exp(-kappa * tau)) / kappa
    A = (rbar - sigma**2 / (2 * kappa**2)) * (B - tau) - sigma**2 * B**2 / (4 * kappa)
    bond = np.exp(A - B * rates)                      # P(t, T) along each path
    assert deflated_martingale_test(bond, bank)["max_abs_t"] < 4
    assert deflated_martingale_test(bond, np.ones_like(bank))["max_abs_t"] > 20   # undiscounted: fails
    w = change_of_numeraire_weights(1.0, bond[0, 0], bank[:, -1], 1.0)
    assert abs(w.mean() - 1) < 0.002
