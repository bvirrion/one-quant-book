"""Numbers gate: every numerical answer printed in Book 5, Chapter 3 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_blackscholes import bs, ncdf, problem, replicate_path

P = problem()


def test_text():
    assert (round(P["d1"], 2), round(P["d2"], 2), round(P["nd1"], 4), round(P["nd2"], 4)) == (0.35, 0.15, 0.6368, 0.5596)
    assert (round(P["formula"], 4), round(P["put"], 4)) == (10.4506, 5.5735)
    assert round(P["p_real"], 2) == 0.69 and round(P["hedge_error"], 2) == 0.39 and round(P["final_spot"], 2) == 115.46
    assert (round(P["tree"], 4), round(P["tree_err"], 4)) == (10.4486, -0.0020)
    t, s, opt, port = replicate_path()
    assert len(t) == 253 and abs(opt[0] - port[0]) < 1e-12


def test_exercises():
    assert (round(bs(100, 100, 0.5, 0.03, 0, 0.25, "C"), 4), round(bs(100, 100, 0.5, 0.03, 0, 0.25, "P"), 4)) == (7.7603, 6.2715)
    assert round(P["black_fut"], 4) == 3.5572
    assert round(ncdf(0.5), 4) == 0.6915 and round(P["digital"], 4) == 0.5323
    assert round(100 * P["iv_10"], 2) == 18.80
    assert (round(P["mc_10k"], 2), round(P["mc_10k_se"], 3)) == (10.64, 0.148)
    assert round(P["mc_10k"] - P["formula"], 2) == 0.19 and round((P["mc_10k"] - P["formula"]) / P["mc_10k_se"], 1) == 1.3


def test_problem():
    assert (round(P["delta"], 4), round(P["gamma"], 4), round(P["theta"], 3)) == (0.6368, 0.0188, -6.414)
    assert abs(P["pde"]) < 1e-12
    assert round(P["formula"] - P["put"], 4) == round(100 - 100 * math.exp(-0.05), 4) == 4.8771
    assert round(P["atm_approx"], 2) == 8.00
    fwd = 100 * math.exp(0.05)
    assert round(fwd, 2) == 105.13 and round(math.exp(-0.05) * fwd * (2 * ncdf(0.1) - 1), 2) == 7.97
    assert (round(P["mc"], 4), round(P["mc_se"], 4), round(P["mc_err"], 4)) == (10.4479, 0.0147, -0.0026)
    assert round(1e6 * (0.0147 / 0.0020) ** 2 / 1e6) == 54
    t, s, opt, port = replicate_path()
    assert (round(port[-1], 2), round(opt[-1], 2)) == (15.85, 15.46)
    assert round(bs(100, 100, 1, 0.05, 0.02, 0.2, "C"), 4) == 9.2270


def test_interview():
    assert round(0.4 * 200 * 0.30, 2) == 24.0
