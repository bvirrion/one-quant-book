"""Numbers gate: every numerical answer printed in Book 6, chapter 21 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_var as m
from firm_varmodel import ewma_cov, kupiec

MEAS = m.measures()
B = m.backtest()


def mn(x, d=2):
    return round(x / 1e6, d)


def test_text():
    assert MEAS["date"] == "2026-09-23"
    y2, y10, e, j = MEAS["levels"]
    assert (round(100 * y2, 2), round(100 * y10, 2), round(e, 4), round(j, 2)) == (4.85, 5.11, 1.1411, 157.92)
    vol = np.sqrt(np.diag(ewma_cov(m.today()[2], m.LAM)))
    assert (round(1e4 * vol[0], 1), round(1e4 * vol[1], 1), round(100 * vol[2], 2), round(100 * vol[3], 2)) == (
        6.4, 5.7, 0.28, 0.65)
    assert (mn(MEAS["hs"][0][0]), mn(MEAS["param_ewma"][0][0]), mn(MEAS["param_eq"][0][0]), mn(MEAS["mc"][0][0]),
            mn(MEAS["fhs"][0][0]), mn(MEAS["dg"][0][0]), mn(MEAS["delta_only"][0])) == (2.10, 1.58, 1.60, 1.66, 2.09, 2.10, 1.91)
    assert (mn(MEAS["param_ewma"][1][1]), mn(MEAS["hs"][1][1])) == (1.59, 2.34)
    p = 0.009
    assert round(100 * (1 - (1 - p) ** 2), 2) == 1.79 and round((p * p * 200 + (0.01 - p * p) * 100) / 0.01, 1) == 100.8
    assert B["rows"][0][0] == "2022-09-02" and B["rows"][-1][0] == "2026-09-23" and len(B["rows"]) == 1000
    h, e, f = B["hs"], B["ewma"], B["fhs"]
    assert (h["exceptions"], round(h["kupiec"][1], 2), h["last250"], h["zone"][0]) == (10, 1.00, 0, "green")
    assert (e["exceptions"], round(e["kupiec"][0], 1), e["last250"], e["zone"]) == (28, 22.0, 8, ("yellow", 0.75))
    assert f"{e['kupiec'][1]:.0e}" == "3e-06"
    assert (f["exceptions"], f["last250"], f["zone"][0]) == (8, 3, "green")
    assert all(x["christoffersen"][1] > 0.05 for x in (h, e, f))
    sh = MEAS["euler"] / MEAS["param_ewma"][0][0]
    assert [round(100 * x) for x in sh] == [-32, 114, 23, -5]


def test_exercises():
    assert math.ceil(0.01 * 500) == 5 and math.ceil(0.025 * 500) == 13
    assert mn(MEAS["param_ewma"][0][0] * math.sqrt(10)) == 5.01
    lr, pv = kupiec(1000, 28, 0.01)
    assert round(lr, 1) == 22.0


def test_problem():
    c = m.capital(0.75)
    assert (mn(c["var10"]), mn(c["base"]), mn(c["with_addon"])) == (5.01, 15.02, 18.78)
