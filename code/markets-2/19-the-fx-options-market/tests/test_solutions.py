"""Numbers gate: every numerical answer printed in Book 2, Chapter 19 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from fxopt_demo import EURUSD, USDJPY, barrier, smile, smile_vols

E = smile(EURUSD, "spot", False)
J, JP, JF = smile(USDJPY, "spot", False), smile(USDJPY, "spot_pa", True), smile(USDJPY, "forward", False)
B = barrier()


def test_text():
    assert round(0.60 - 73_669 / 1e6, 4) == 0.5263 and round(600_000 - 73_669) == 526_331
    assert (round(E["fwd"], 5), round(E["k_atm"], 5)) == (1.15119, 1.15190)
    assert (round(J["fwd"], 4), round(J["k_atm"], 4), round(JP["k_atm"], 4)) == (155.8196, 155.9955, 155.6439)
    assert round((J["k_atm"] - JP["k_atm"]) * 100) == 35
    assert (round(J["vol_c"] * 100, 1), round(J["vol_p"] * 100, 1)) == (9.2, 10.4)
    assert (round(J["k_c"], 2), round(J["k_p"], 2), round(JP["k_c"], 2), round(JP["k_p"], 2)) == (
        160.85, 150.71, 160.68, 150.52)
    assert round((J["k_p"] - JP["k_p"]) * 100) == 19


def test_exercises():
    c, p = smile_vols(0.07, -0.005, 0.002)
    assert (round(c * 100, 2), round(p * 100, 2)) == (6.95, 7.45)
    ef = smile(EURUSD, "forward", False)
    assert (round(E["k_c"], 5), round(E["k_p"], 5), round(ef["k_c"], 5), round(ef["k_p"], 5)) == (
        1.17904, 1.12357, 1.17920, 1.12341)
    assert (round(JF["k_c"], 2), round(JF["k_p"], 2)) == (160.90, 150.65)


def test_problem():
    assert (round(B["vanilla"] * 1e4, 1), round(B["ko"] * 1e4, 1)) == (183.8, 165.2)
    assert round((B["vanilla"] - B["ko"]) * 1e4, 1) == 18.6 and round((B["vanilla"] - B["ko"]) * 5e8, -4) == 930_000
    assert round(B["delta_now"], 3) == 0.657 and round(B["delta_now"] * 5e8 / 1e6, 1) == 328.7
    assert (round(B["delta_near"], 3), round(B["vanilla_delta_near"], 3)) == (0.631, 0.298)
    assert round(B["sell_at_barrier"] / 1e6, 1) == 315.5
