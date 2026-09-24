"""Numbers gate: every numerical answer printed in Book 4, Chapter 7 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from qm_hawkes import DAY, LAM_BAR, dispersion_theory, fit, problem, simulate_seasonal_poisson, simulate_thinning

P = problem()


def test_text_and_problem():
    assert P["events"] == 8006 and round(P["expected_events"]) == 7800 and round(LAM_BAR, 3) == 0.333
    assert (round(P["mu_hat"], 3), round(P["alpha_hat"], 3), round(P["beta_hat"], 3), round(P["n_hat"], 3)) == (0.103, 0.696, 0.995, 0.700)
    assert (round(P["n_mean"], 3), round(P["n_sd"], 3)) == (0.700, 0.011)
    assert (round(P["res_mean"], 3), round(P["res_var"], 2), round(P["poisson_res_var"], 2)) == (1.000, 0.98, 4.63)
    assert round(P["branch_share"], 3) == 0.699 and P["branch_events"] == 7498
    assert (round(P["disp_1s"], 2), round(P["disp_60s"], 1), round(P["disp_inf"], 1)) == (2.38, 10.5, 11.1)
    assert P["seasonal_events"] == 7730
    assert (round(P["n_spurious"], 2), round(P["beta_spurious"], 4)) == (0.87, 0.0076) and round(1 / P["beta_spurious"]) == 132
    assert (round(P["n_spurious_mean"], 2), round(P["n_flat_mean"], 2)) == (0.86, 0.04)
    assert round(P["cluster_size"], 2) == 3.33 and round(P["half_life_kernel"], 2) == 0.69


def test_exercises():
    gam, a_rel = 0.3, 0.7 * 1.3 * 1.0 / (2 * 0.3)
    assert round(a_rel, 3) == 1.517 and round(1 + 2 * a_rel * (1 / gam - (1 - math.exp(-gam)) / gam**2), 2) == 2.38
    assert (0.5 * 1 + 0.5 * 3, 2 + (0.5 * 1 + 0.5 * 9 - 4)) == (2.0, 3.0)


def test_time_step_and_ablation():
    """WRITING section 9. Thinning is exact (no time step); the dispersion law is checked against a
    simulation at bins four times finer than the text's; and each mechanism the text credits is
    ablated: no excitation (alpha = 0) gives a branching ratio near zero, and removing the
    seasonality from the no-excitation day removes the spurious branching (checked above: 0.04)."""
    t = simulate_thinning(0.1, 0.7, 1.0, DAY, seed=1)
    c = np.histogram(t, bins=np.arange(0, DAY + 1e-9, 15.0))[0]
    assert abs(c.var() / c.mean() - dispersion_theory(15.0)) < 0.8
    t0 = simulate_thinning(1 / 3, 0.0, 1.0, DAY, seed=5)
    assert fit(t0, DAY)["branching"] < 0.1
    s = simulate_seasonal_poisson(LAM_BAR, seed=6)
    assert fit(s, DAY)["branching"] > 0.6


def test_bivariate_example():
    G = np.array([[0.2, 0.4], [0.4, 0.2]])
    assert np.allclose(sorted(np.linalg.eigvals(G)), [-0.2, 0.6])
    assert np.allclose(np.linalg.solve(np.eye(2) - G, [0.1, 0.1]), [0.25, 0.25])
    lam = 0.25
    assert abs(0.4 * lam / (0.2 * lam + 0.4 * lam) - 2 / 3) < 1e-12        # cross share of triggered activity
