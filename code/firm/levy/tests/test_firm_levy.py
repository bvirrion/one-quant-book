"""Acceptance tests of firm.levy."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_levy import (
    cumulants,
    exp_martingale_drift,
    merton_cumulants,
    psi_kou,
    psi_merton,
    psi_nig,
    psi_vg,
    simulate_merton,
    simulate_nig,
    simulate_vg,
)


def _emp_cf(x, u):
    return np.mean(np.exp(1j * u * x))


def test_merton_cumulants_and_charfn():
    args = (0.05, 0.2, 3.0, -0.05, 0.08)
    num = cumulants(lambda u: psi_merton(u, *args))
    assert all(abs(a - b) < 1e-6 for a, b in zip(num, merton_cumulants(*args), strict=True))
    x = simulate_merton(0.5, 1, 200_000, 1, *args)[:, 1]
    for u in (1.0, 3.0, 8.0):
        assert abs(_emp_cf(x, u) - np.exp(0.5 * psi_merton(u, *args))) < 0.01


def test_vg_and_nig_paths_match_their_exponents():
    x = simulate_vg(1.0, 4, 200_000, 2, -0.1, 0.2, 0.3)[:, -1]
    for u in (1.0, 5.0):
        assert abs(_emp_cf(x, u) - np.exp(psi_vg(u, -0.1, 0.2, 0.3))) < 0.01
    y = simulate_nig(1.0, 4, 200_000, 3, 15.0, -3.0, 0.5)[:, -1]
    for u in (1.0, 5.0):
        assert abs(_emp_cf(y, u) - np.exp(psi_nig(u, 15.0, -3.0, 0.5))) < 0.01


def test_kou_mean():
    c = cumulants(lambda u: psi_kou(u, 0.0, 0.1, 2.0, 0.4, 20.0, 10.0))
    assert abs(c[0] - 2.0 * (0.4 / 20.0 - 0.6 / 10.0)) < 1e-6


def test_exponential_martingale_drift():
    lev = (0.0, 0.2, 2.0, -0.1, 0.05)
    b = exp_martingale_drift(lambda u: psi_merton(u, *lev))
    x = simulate_merton(1.0, 1, 1_000_000, 4, b, *lev[1:])[:, 1]
    assert abs(np.mean(np.exp(x)) - 1) < 0.003
    assert abs(b - (-0.02 - 2.0 * (math.exp(-0.1 + 0.00125) - 1))) < 1e-9
