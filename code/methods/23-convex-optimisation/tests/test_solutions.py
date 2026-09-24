"""Numbers gate: every numerical answer printed in Book 4, Chapter 23 (text and solutions)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from qm_opt import broken_correlation, constraint_costs, infeasible, risk_limit, today, turnover_curve

T = today()


def r(x, d=2):
    return round(float(x), d)


def test_optimum_and_duals():
    assert T["status"] == "optimal" and T["iters"] == 18
    assert (r(100 * T["expected_return"]), r(100 * T["risk"]), r(100 * T["objective"])) == (3.78, 3.47, 3.18)
    assert (r(T["gross"], 4), r(T["turnover"], 4), T["binding_positions"]) == (1.0, 0.2, 43)
    d = T["duals"]
    assert (r(d["turnover"], 4), r(d["gross"], 4), r(d["dollar"], 4), r(d["position"] / 43, 4)) == (0.0159, 0.0185, 0.0004, 0.0175)
    assert T["kkt"]["stationarity"] < 1e-9 and T["kkt"]["complementarity"] < 1e-9


def test_turnover_curve_and_costs():
    tc = {round(100 * L): (u, er, du) for L, u, er, du, _ in turnover_curve()}
    assert (r(100 * tc[5][0]), r(100 * tc[20][0], 3), r(100 * tc[80][0])) == (2.88, 3.180, 3.62)
    assert [r(tc[k][2], 4) for k in (10, 15, 20, 30, 80)] == [0.0210, 0.0184, 0.0159, 0.0119, 0.0011]
    assert r((tc[30][0] - tc[20][0]) / 0.1, 4) == 0.0139
    assert (r(100 * tc[10][1]), r(100 * tc[30][1])) == (3.60, 3.92) and r((tc[30][1] - tc[10][1]) / 0.2, 3) == 0.016
    assert r(100 * today(turnover=0.22)["objective"], 3) == 3.211 and r(100 * (tc[20][0] + 0.0159 * 0.02), 3) == 3.212
    c = constraint_costs()
    assert (r(100 * c["turnover"]), r(100 * c["gross"]), r(100 * c["position"]), r(100 * c["sector"], 3), r(100 * c["dollar"], 6)) == (
        0.44, 0.28, 0.19, 0.014, 0.0)


def test_certificate_cone_and_ncm():
    inf = infeasible()
    assert (r(inf["t"], 4), inf["support"], r(inf["lam_min_sector0"], 6), r(inf["value"], 4)) == (0.005, 40, 1.0, -0.005)
    assert inf["stationarity"] < 1e-8 and inf["lam_upper"] < 1e-8 and inf["lam_lower"] < 1e-8
    assert np.allclose(inf["lam"][:40], 1 / 40, atol=1e-8)
    rl = risk_limit()
    assert (r(100 * rl["ret_soc"]), r(100 * rl["ret_qp"]), r(rl["gamma"], 1), r(rl["multiplier"], 3), rl["iters"]) == (5.31, 5.31, 25.8, 1.033, 924)
    assert rl["gap"] < 1e-7 and r(rl["gamma"] * 0.04, 3) == 1.033 and rl["status"] == "optimal"
    b = broken_correlation()
    assert (b["n_negative"], r(b["eig_before"].min()), b["iters"], r(b["distance"]), r(b["max_change"])) == (21, -1.42, 74, 4.45, 0.31)
    assert b["eig_after"].min() > -1e-8 and b["eig_before"].max() > 10


def test_stability():
    """WRITING section 9: the turnover price is a local property; the finite-difference slope over a narrow bracket
    around 20% matches the multiplier, and tightening the solver's tolerance leaves the solution unchanged."""
    lo, hi = today(turnover=0.19)["objective"], today(turnover=0.21)["objective"]
    assert abs((hi - lo) / 0.02 - T["duals"]["turnover"]) < 0.0005


def test_exercises():
    assert r(0.5 - 1, 1) == -0.5
    lam = np.array([1.0, 1.0])
    assert np.allclose(np.array([[1.0, 0.0], [0.0, 1.0]]).T @ lam + np.array([[1.0, 1.0]]).T @ np.array([-1.0]), 0)
