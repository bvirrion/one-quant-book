"""Numbers gate: every numerical answer printed in Book 10, chapter 4 (text and solutions)."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from mx_spread import gm_learning, gm_with_cost, kyle_check, pin_bias, roll_on_tape  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / "code" / "firm" / "spreadmodels"))
from firm_spreadmodels import gm_quotes, inventory_quotes, kyle_one_period  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_glosten_milgrom():
    g = gm_learning()
    assert [g[m]["median_trades"] for m in (0.1, 0.3, 0.5)] == [148.0, 19.0, 6.0]
    assert [r(g[m]["mean_spread"][50], 3) for m in (0.1, 0.3)] == [0.066, 0.014]
    assert [r(x, 2) for x in gm_quotes(0.5, 0.3)] == [0.35, 0.65]
    assert (r(gm_with_cost(0.1, 1, 0.05)["adverse_share"]), r(gm_with_cost(0.3, 1, 0.05)["adverse_share"])) == (0.5, 0.75)
    assert r(gm_with_cost(0.3, 1, 0.05)["spread"]) == 0.4


def test_kyle_and_roll():
    k = kyle_check()
    assert (k["lambda"], r(k["lambda_hat"], 3), r(k["posterior_hat"], 3), r(k["profit_hat"], 3)) == (0.25, 0.25, 0.498, 0.991)
    ro = roll_on_tape()
    assert (r(ro["roll"]), r(ro["quoted"]), r(ro["sign_autocorr"])) == (0.88, 1.08, 0.29)


# Printed digits that move with the CPU's floating-point kernels: skipped by CI (make test-fast).
@pytest.mark.reference
def test_pin():
    got = {(a, sd): r(pin_bias(sd, a)["mean"], 3) for a in (0.0, 0.4) for sd in (0.0, 0.25, 0.5, 0.75)}
    assert got == {(0.0, 0.0): 0.006, (0.0, 0.25): 0.085, (0.0, 0.5): 0.153, (0.0, 0.75): 0.207,
                   (0.4, 0.0): 0.107, (0.4, 0.25): 0.135, (0.4, 0.5): 0.164, (0.4, 0.75): 0.195}
    assert r(pin_bias(0.0, 0.4)["true"], 3) == 0.107


def test_exercises():
    # exercise 1: Roll with Cov = -0.0004 (dollars squared): s = 2 sqrt(0.0004) = 0.04
    assert r(2 * math.sqrt(0.0004), 2) == 0.04
    # exercise 2: GM with v in {99, 101}, mu = 0.2, delta = 0.5: bid 99.8, ask 100.2
    b, a = gm_quotes(0.5, 0.2, 99.0, 101.0)
    assert (r(b, 2), r(a, 2)) == (99.8, 100.2)
    # exercise 3: Kyle, sigma_v = 2, sigma_u = 8: lambda = 0.125, beta = 4, profit = 8
    k = kyle_one_period(2.0, 8.0)
    assert (k["lambda"], k["beta"], k["profit"], k["posterior_var"]) == (0.125, 4.0, 8.0, 2.0)
    # exercise 4: inventory quotes, v = 50, q = -3, size 1, gamma = 0.2, sigma = 1, T = 0.5
    b, a = inventory_quotes(50.0, -3.0, 1.0, 0.2, 1.0, 0.5)
    assert (r(b, 2), r(a, 2)) == (50.25, 50.35)
    # exercise 5: after one buy with mu = 0.2 from delta = 0.5: 0.6
    from firm_spreadmodels import gm_update
    assert r(gm_update(0.5, 1, 0.2), 2) == 0.6


def test_exercises_5_and_7():
    import numpy as np
    from firm_spreadmodels import pin_fit, simulate_days
    b, a = gm_quotes(0.6, 0.2, 99.0, 101.0)
    assert (r(b, 2), r(a, 2)) == (100.0, 100.38)
    bb, ss = simulate_days(250, (0.4, 0.5, 60.0, 100.0, 100.0), seed=41, activity_sd=0.5)
    tot = bb + ss
    bn = np.round(bb / tot * tot.mean()).astype(int)
    sn = np.round(ss / tot * tot.mean()).astype(int)
    assert (r(pin_fit(bb, ss)["pin"], 3), r(pin_fit(bn, sn)["pin"], 3)) == (0.149, 0.139)
    b0, s0 = simulate_days(250, (0.4, 0.5, 60.0, 100.0, 100.0), seed=41)
    assert r(pin_fit(b0, s0)["pin"], 3) == 0.098
