"""Numbers gate: every numerical answer printed in Book 11, chapter 3 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import hf_inventory as h  # noqa: E402

inv = h.inv


def r(x, d=2):
    return round(float(x), d)


def test_as_table():
    t = h.as_table()
    got = {g: (r(v["spread"]), r(v["inventory"]["profit"]), r(v["inventory"]["sd"]), r(v["inventory"]["q"]),
               r(v["inventory"]["sd_q"]), r(v["symmetric"]["profit"]), r(v["symmetric"]["sd"]), r(v["symmetric"]["q"]),
               r(v["symmetric"]["sd_q"])) for g, v in t.items()}
    assert got == {0.01: (1.35, 68.45, 9.06, -0.05, 5.24, 68.5, 13.91, -0.05, 8.99),
                   0.1: (1.49, 64.83, 6.49, 0.09, 2.97, 68.15, 14.0, -0.21, 8.66),
                   1.0: (3.03, 31.44, 4.83, 0.05, 1.66, 43.3, 10.34, -0.14, 5.39)}
    assert (r(t[0.1]["inventory"]["fills"], 1), r(t[0.1]["symmetric"]["fills"], 1)) == (97.0, 91.7)
    assert r(100 * (1 - 64.83 / 68.15), 0) == 5 and r(100 * (1 - 31.44 / 43.3), 0) == 27


def test_frontier_and_depths():
    f = h.frontier()
    assert (r(f["cj"][0.5]["profit"], 1), r(f["cj"][0.5]["sd"], 1)) == (66.7, 6.9)
    assert (r(f["symmetric"][0.67]["profit"], 1), r(f["symmetric"][0.67]["sd"], 1)) == (68.5, 13.9)
    assert r(100 * f["cj"][0.5]["profit"] / f["symmetric"][0.67]["profit"], 0) == 97
    sol = inv.CJSolution(140, 1.5, 5.0, 1.0, 30, 1.0, 200)
    assert [r(x, 3) for x in sol.depths(0.0, 0)] == [0.804, 0.804]
    assert [r(x, 3) for x in sol.depths(0.0, 3)] == [1.55, 0.011] and r(sol.depths(0.0, 4)[1], 3) == -0.217


def test_by_hand():
    rp, half, b, a = inv.as_quotes(100, 3, 0.5, 0.1, 2, 1.5)
    assert (r(rp), r(2 * half, 3), r(b), r(a)) == (99.4, 1.491, 98.65, 100.15)
    w = 0.1 * 4 + 20 * math.log(1 + 0.1 / 1.5)
    assert (r(w), r(w - 0.4)) == (1.69, 1.29)
    k = 2 * math.log(40 / 18)
    assert (r(k), r(0.04 * math.exp(0.5 * k), 4)) == (1.6, 0.0889)


def test_calibration_on_the_tape():
    c = h.calibration()
    assert [round(float(x)) for x in c["time"]] == [1639, 1640, 1812, 1825] and list(c["fills"]) == [8, 0, 0, 0]
    tc = h.touch_calibration()
    assert (tc["n"], r(tc["lam"], 3), r(tc["c"], 3)) == (241, 0.033, 0.139)


def test_tape_compare():
    a, b = h.tape_compare(3e-4), h.tape_compare(1e-3)
    s = a["symmetric"]
    assert (r(s["pnl"]), r(s["sd_pnl"]), r(s["volume"], 0), r(s["abs_q"]), r(s["max_q"])) == (-65.17, 97.87, 15783, 2.51, 5.0)
    t = a["touch"]
    assert (r(t["pnl"]), r(t["sd_pnl"]), r(t["volume"], 0), r(t["abs_q"]), r(t["max_q"])) == (-0.75, 29.53, 14317, 1.12, 3.67)
    t = b["touch"]
    assert (r(t["pnl"]), r(t["sd_pnl"]), r(t["volume"], 0), r(t["abs_q"]), r(t["max_q"])) == (11.0, 8.41, 11433, 0.57, 2.33)
    assert r(s["sd_pnl"] / math.sqrt(6), 0) == 40
