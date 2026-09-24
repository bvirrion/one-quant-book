"""Numbers gate: every numerical answer printed in Book 2, Chapter 15 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/lastlook"))
from firm_lastlook import expected_transfer
from lastlook_demo import SIGMA, THRESHOLD, by_hold, no_last_look, window

W = window()


def test_text():
    assert round(no_last_look()["markout"], 4) == 0.3785
    assert round(W["sd_hold"], 2) == 0.1 and round(W["per_bp"], 4) == 0.0352 and round(W["per_bp_t0"], 4) == 0.0399
    assert round(W["daily"]) == 7_041 and round(W["yearly"] / 1e6, 2) == 1.76
    assert round(W["p_reject_sym"] * 100) == 62 and abs(W["sym_kept"]) < 0.001


def test_exercises():
    assert (round((1.1464 - 1.1463) * 1e6), round((1.1465 - 1.1463) * 1e6)) == (100, 200)
    assert round((1.1464 - 1.1465) / 1.1463 * 1e4, 2) == -0.87
    assert [round(SIGMA * math.sqrt(h), 2) for h in (25, 100, 400)] == [0.05, 0.1, 0.2]
    assert round(expected_transfer(SIGMA, 25, 0.0, "asymmetric"), 4) == 0.0199
    a = dict(by_hold("asymmetric", THRESHOLD))[100]
    s = dict(by_hold("symmetric", THRESHOLD))[100]
    got = [round(100 * x, 2) for x in (a["reject_informed"], a["reject_uninformed"], s["reject_informed"],
                                       s["reject_uninformed"])]
    assert got == [92.68, 30.79, 93.46, 61.76]
    assert (round(a["markout"], 4), round(s["markout"], 4)) == (0.4491, 0.3991)


def test_problem():
    assert (round(W["p_reject_asym"] * 100, 1), round(W["p_reject_sym"] * 100, 1)) == (30.9, 61.7)
    assert round(W["spread_cost_daily"]) == 80_000 and round(W["daily"] / W["spread_cost_daily"] * 100, 1) == 8.8
    assert round(expected_transfer(SIGMA, 25, 0.0, "asymmetric") * 1e-4 * 2e9) == 3_989
    assert abs(W["sim_per_bp"] - W["per_bp"]) < 0.001
