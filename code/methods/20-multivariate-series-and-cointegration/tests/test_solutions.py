"""Numbers gate: every numerical answer printed in Book 4, Chapter 20 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from qm_coint import ROOT, cointegration, eg_vs_df, load, rolling_weights, var_analysis

sys.path.insert(0, str(ROOT / "code" / "firm" / "tsa"))
from firm_tsa import adf

C = cointegration()
V = var_analysis()


def r(x, d=2):
    return round(float(x), d)


def test_series_and_var():
    Y = load()["Y"]
    assert Y.shape[0] == 12574
    assert [r(adf(Y[:, i], lags=0)["tau"]) for i in range(3)] == [-1.30, -1.33, -1.31]
    assert V["p"] == 10 and V["stable"]
    assert [r(v, 1) for v in V["sd"]] == [7.9, 7.6, 7.1]
    assert (r(V["corr"][0, 1]), r(V["corr"][0, 2]), r(V["corr"][1, 2])) == (0.90, 0.82, 0.94)
    assert [r(v, 1) for v in V["cum_2y_shock"]] == [10.1, 8.3, 6.7] and r(V["irf"][0, 0, 0], 1) == 7.9
    f = V["fevd10"][2]
    assert (round(100 * f[0]), round(100 * f[1]), round(100 * f[2])) == (67, 21, 12)
    g = V["granger"]
    assert (r(g["2y->10y"][0]), r(g["2y->10y"][3]), r(g["2y->5y"][0]), r(g["10y->2y"][0]), r(g["10y->2y"][3], 3)) == (1.88, 0.04, 7.16, 2.83, 0.002)
    assert g["2y->5y"][3] < 1e-6 and all(v[3] < 0.05 for v in g.values()) and g["2y->10y"][2] == 12532


def test_cointegration():
    assert (C["p"], C["rank"]) == (10, 1)
    assert [r(v) for v in C["trace"]] == [59.77, 14.93, 2.34]
    assert [c[1] for c in C["crit_trace"]] == [35.23, 20.36, 9.23]
    w = C["weights"]
    assert (r(w[0]), r(w[1]), r(w[2]), r(w[0] + w[2])) == (0.41, -1.0, 0.61, 1.02)
    assert (r(C["eg_beta"][1]), r(C["eg_beta"][2]), r(C["eg_tau"]), r(C["eg_crit"][1])) == (0.40, 0.62, -10.04, -3.74)
    assert (r(C["hl_johansen"][0], 4), round(C["hl_johansen"][1]), r(C["hl_121"][0], 4), round(C["hl_121"][1])) == (0.9841, 43, 0.9891, 63)
    assert (r(C["sd_fly_j"]), r(C["sd_fly_121"] / 2)) == (2.06, 2.15)
    rk = C["hl_johansen"][0] + (1 + 3 * C["hl_johansen"][0]) / C["n"]
    assert (r(rk, 4), round(math.log(0.5) / math.log(rk))) == (0.9844, 44)
    assert r(C["sd_fly_j"] / math.sqrt(1 - C["hl_johansen"][0] ** 2), 1) == 11.6


def test_rolling_and_simulation():
    rw = rolling_weights()
    ranks = np.array([x[3] for x in rw])
    assert (len(rw), int(np.sum(ranks == 0))) == (46, 20)
    w = np.array([(x[1], x[2]) for x in rw if x[3] == 1])
    assert (r(w[:, 0].min()), r(w[:, 0].max()), r(w[:, 1].min()), r(w[:, 1].max())) == (0.27, 0.63, 0.40, 0.97)
    assert sum(1 for x in rw if abs(x[1]) >= 1.5 or abs(x[2]) >= 1.5) == 4
    e = eg_vs_df()
    assert (r(e["df5"]), r(e["eg5"]), round(100 * e["df_reject_at_eg"])) == (-2.92, -3.75, 27)


def test_stability():
    """WRITING section 9: the rank and the weights survive dropping the first decade (the named result's sample
    sensitivity), and the Engle-Granger null distribution is stable across seeds."""
    c2 = cointegration("1986-01-01")
    assert c2["rank"] >= 1 and abs(c2["weights"][0] - C["weights"][0]) < 0.05 and abs(c2["weights"][2] - C["weights"][2]) < 0.05
    e2 = eg_vs_df(reps=2000, seed=5)
    assert abs(e2["eg5"] - (-3.75)) < 0.1


def test_exercises():
    assert sorted(np.round(np.linalg.eigvals([[0.5, 0.4], [0.4, 0.5]]), 6)) == [0.1, 0.9]
    assert sorted(np.round(np.linalg.eigvals([[0.6, 0.4], [0.4, 0.6]]), 6)) == [0.2, 1.0]
    assert r(-3.74066 - 8.5631 / 500 - 10.852 / 500**2 + 27.982 / 500**3, 3) == -3.758
    lam = [0.05, 0.01, 0.002]
    assert [r(-1000 * sum(math.log(1 - x) for x in lam[k:])) for k in range(3)] == [63.35, 12.05, 2.0]
    assert (r(0.9**2), r(1 - 0.9**2)) == (0.81, 0.19)
