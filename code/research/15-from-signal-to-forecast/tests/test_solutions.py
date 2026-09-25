"""Numbers gate: every numerical answer printed in Book 7, chapter 15 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "forecast"))
from firm_forecast import effective_breadth, isotonic, law_ir
from rs_forecast import IC0, calibration, concentrated, data, law, tracking_error_grid


def r(x, d=2):
    return round(float(x), d)


def test_calibration():
    eps, vol, s, _, _ = data()
    assert s.shape == (120, 704) and r(np.median(vol), 3) == 0.077
    assert r(IC0 * np.median(vol) * 2 * 100, 2) == 0.77
    c = calibration()
    assert r(c["ic_hat"], 3) == 0.055
    assert (r(c["scaled"][1]), r(100 * c["scaled"][2], 2), r(c["raw"][1], 4)) == (0.92, 0.24, 0.0039)
    assert 60 * 704 // 10 == 4224


def test_law():
    lw = law()
    assert (r(lw["law"]), r(lw["ir_gauss"]), r(lw["qian_hua"]), r(lw["ir_market"])) == (4.60, 4.92, 4.13, 4.26)
    assert (r(lw["ic_mean"], 4), r(lw["ic_sd"], 4), r(lw["ic_sd_gauss"], 4)) == (0.0505, 0.0424, 0.0331)
    assert round(lw["breadth_eff"]) == 569
    assert (r(lw["tc"], 3), round(100 * lw["clipped"]), r(lw["steps"][2]), r(lw["ir_long"])) == (0.857, 47, 3.54, 3.00)
    assert r(0.857 * 4.13) == 3.54 and round(100 * lw["ir_long"] / lw["law"]) == 65
    sr = lw["ir_gauss"] / math.sqrt(12)
    assert r(math.sqrt((1 + sr * sr / 2) / 120) * math.sqrt(12)) == 0.45
    assert [round(100 * (1 - b / a)) for a, b in zip(lw["steps"][:-1], lw["steps"][1:], strict=True)] == [10, 14, 15]


def test_tracking_error():
    g = tracking_error_grid()
    assert [round(100 * g[t]["clipped"]) for t in g] == [13, 28, 38, 44, 47]
    assert [r(g[t]["tc"]) for t in g] == [0.98, 0.93, 0.89, 0.87, 0.86]
    assert [r(g[t]["ir"]) for t in g] == [3.91, 3.54, 3.25, 3.09, 3.00]
    c = concentrated()
    assert (r(c["tc"]), r(c["ir"])) == (0.59, 2.18)


def test_exercises():
    assert (r(0.04 * 10 * -1.5, 1), r(0.04 * 5 * 2, 1)) == (-0.6, 0.4)
    assert (r(law_ir(0.03, 12 * 500)), r(law_ir(0.03, 52 * 50))) == (2.32, 1.53)
    assert [r(x, 3) for x in isotonic(np.arange(6), [2.0, 1.0, 3.0, 3.0, 2.0, 4.0])] == [1.5, 1.5, 2.667, 2.667, 2.667, 4.0]
    assert r(effective_breadth(100, 0.05), 1) == 16.8
    assert r((100 / 8.4 - 1) / 99, 3) == 0.110
    assert (r(0.04 / 0.05 * math.sqrt(12)), r(law_ir(0.04, 12 * 704)), r(1 / math.sqrt(704), 3)) == (2.77, 3.68, 0.038)
    assert (r(0.02 * 2, 2), r((0.02 + 0.01) * 2, 2)) == (0.04, 0.06)
    assert round(law_ir(0.03, 252 * 3000)) == 26
