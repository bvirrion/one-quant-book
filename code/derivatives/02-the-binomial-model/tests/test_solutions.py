"""Numbers gate: every numerical answer printed in Book 5, Chapter 2 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_binomial import bs_put, error, one_period, params, price, whiteboard

W = whiteboard()


def test_text_and_problem_part_1_2():
    assert round(W["p"], 4) == 0.6 and round(W["call"], 4) == 10.3603
    assert [round(x, 1) for x in W["shares"][3]] == [72.9, 89.1, 108.9, 133.1]
    assert (round(W["delta0"], 4), round(W["bond0"], 2)) == (0.6240, -52.04)
    assert round(W["put"], 4) == 4.5925 and round(W["parity"], 4) == round(W["parity_rhs"], 4) == 5.7678
    assert (round(W["am_put"], 4), round(W["premium"], 4)) == (4.9076, 0.3151)
    assert round(W["put_nodes"][1][0], 3) == 9.196 and round(W["put_nodes"][2][0], 3) == 17.039
    assert W["am_put_nodes"][1][0] == 10.0 and round(W["am_put_nodes"][2][0], 6) == 19.0
    assert round(one_period(50, 60, 40, 1.0, 10, 0)["price"], 6) == 5.0


def test_convergence():
    assert round(bs_put(), 4) == 5.5735
    assert (round(error(100, "crr"), 4), round(error(101, "crr"), 4)) == (-0.0200, 0.0174)
    assert round(error(101, "lr"), 5) == -0.00003 and abs(error(11, "lr")) < 0.003
    assert abs(error(101, "lr")) < 1e-4


def test_steps_within_one_cent():
    bad = [n for n in range(1, 1001) if abs(error(n, "crr")) >= 0.01]
    assert max(bad) + 1 == 199
    bad_lr = [n for n in range(1, 400, 2) if abs(error(n, "lr")) >= 0.01]
    assert max(bad_lr) + 2 == 7


def test_american_real_tree():
    am = price(100, 100, 1, 0.05, 0.2, 2001, "P", american=True, method="lr")
    assert (round(am, 4), round(am - bs_put(), 4)) == (6.0902, 0.5167)
    b = 100 - price(81.0, 100, 1, 0.05, 0.2, 1001, "P", american=True, method="lr")
    assert abs(b - 81.0) < 1e-9                        # at 81 the put is exercised
    assert price(81.2, 100, 1, 0.05, 0.2, 1001, "P", american=True, method="lr") > 100 - 81.2 + 1e-4


def test_exercises():
    u, d, p = params("crr", 100, 100, 1 / 12, 0.03, 0, 0.2, 1)
    assert (round(u, 4), round(d, 4), round(p, 4)) == (1.0594, 0.9439, 0.5072)
    assert round(W["digital"], 4) == 0.6106
    u, d, p = params("jr", 100, 100, 0.1, 0.05, 0, 0.2, 1)
    assert (round(u, 4), round(d, 4), round(p, 4)) == (1.0685, 0.9415, 0.5000)
    u, d, p = params("crr", 100, 100, 0.1, 0.05, 0, 0.2, 1)
    assert (round(u, 4), round(d, 4), round(p, 4)) == (1.0653, 0.9387, 0.5238)
    assert round(bs_put() + error(101, "crr"), 4) == 5.5909 and round(bs_put() + error(101, "lr"), 4) == 5.5735
    assert round((1.06 - 0.97) / (1.05 - 0.97), 3) == 1.125


def test_interview():
    r = one_period(100, 120, 80, 1.0, 20, 0)
    assert (r["delta"], round(r["bond"], 6), round(r["price"], 6)) == (0.5, -40.0, 10.0)
