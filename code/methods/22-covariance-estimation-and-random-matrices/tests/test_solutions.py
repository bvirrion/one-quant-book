"""Numbers gate: every numerical answer printed in Book 4, Chapter 22 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from qm_covest import SCALE, bias_vs_q, evaluate, mp_edges, spectrum, spike, truth

E = evaluate()


def r(x, d=2):
    return round(float(x), d)


def test_hook_and_evaluation():
    s = E["sample"]
    assert (r(100 * s["pred"]), r(100 * s["true"]), r(100 * s["real"]), r(100 * E["optimum"])) == (5.71, 9.58, 9.61, 7.44)
    assert (r(s["ratio"]), r(1 / (1 - E["q"]))) == (1.68, 1.67)
    ratios = [r(E[k]["ratio"]) for k in ("sample", "lw_identity", "lw_constcorr", "nonlinear", "clipped", "pca_factor")]
    assert ratios == [1.68, 1.51, 1.19, 1.12, 1.11, 1.17]
    assert [r(100 * E[k]["real"]) for k in ("lw_identity", "lw_constcorr", "nonlinear", "clipped", "pca_factor")] == [9.14, 9.14, 8.25, 8.05, 7.74]
    assert [r(100 * E[k]["pred"]) for k in ("lw_constcorr", "nonlinear", "clipped", "pca_factor")] == [7.64, 7.36, 7.27, 6.65]
    assert (r(E["intensity"]["lw_identity"], 3), r(E["intensity"]["lw_constcorr"], 3)) == (0.034, 0.178)


def test_truth_scale():
    spec = np.sqrt(np.diag(truth()))
    assert SCALE == 1.1 and round(100 * 1.1 * 0.01 * math.sqrt(252)) == 17 and round(100 * 1.1 * 0.025 * math.sqrt(252)) == 44
    assert spec.size == 200


def test_bias_curve():
    b = bias_vs_q()
    assert [r(v) for _, v, _ in b] == [1.11, 1.26, 1.43, 1.67, 2.05, 2.51, 3.38, 5.21, 10.05]
    assert [r(t) for _, _, t in b] == [1.11, 1.25, 1.43, 1.67, 2.0, 2.5, 3.33, 5.0, 10.09]
    assert (round(200 / b[0][0]), round(200 / b[-1][0])) == (2000, 222)


def test_spectrum_and_spike():
    s = spectrum()
    lo, hi = mp_edges(0.4)
    assert (r(lo, 3), r(hi, 3), r(s["noise"].min(), 3), r(s["noise"].max(), 3)) == (0.135, 2.665, 0.144, 2.565)
    top = np.sort(s["factor"])[::-1]
    assert (r(top[0], 1), r(top[4]), r(top[1])) == (51.4, 2.96, 3.68) and int(np.sum(s["factor"] > hi)) == 5
    pop = np.sort(s["population"])[::-1]
    assert (r(pop[0], 1), r(pop[4]), r(pop[1])) == (52.9, 2.83, 2.99)
    assert int(np.sum(s["factor"] > 3)) == 4
    sp = {e: (m, t) for e, m, t in spike()}
    assert r(1 + math.sqrt(0.4)) == 1.63 and all(abs(m - t) < 0.08 for m, t in sp.values())


def test_stability():
    """WRITING section 9: the named ratios are stable when the number of simulated histories is halved (a fresh
    seed), and the ablation of dimension (q = 0.1) brings the sample portfolio's ratio close to one."""
    e2 = evaluate(n_rep=25, seed=900)
    assert abs(e2["sample"]["ratio"] - 1.68) < 0.05 and abs(e2["nonlinear"]["ratio"] - 1.12) < 0.05
    b = bias_vs_q(Ts=(2000,), n_rep=10, seed=77)
    assert b[0][1] < 1.15


def test_exercises():
    assert (r((1 - math.sqrt(0.4)) ** 2, 3), r((1 + math.sqrt(0.4)) ** 2, 3)) == (0.135, 2.665)
    assert r(5 / (1 - 0.5)) == 10.0
    assert (r(1 + math.sqrt(0.25)), r(3 * (1 + 0.25 / 2), 3), r((1.5) ** 2)) == (1.5, 3.375, 2.25)
    assert (r(1 - 1 / 1.1, 3), round(200 / (1 - 1 / 1.1)), r(2200 / 252, 1)) == (0.091, 2200, 8.7)
