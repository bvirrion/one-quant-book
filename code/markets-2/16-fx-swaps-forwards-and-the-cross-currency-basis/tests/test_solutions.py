"""Numbers gate: every numerical answer printed in Book 2, Chapter 16 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/fxfwd"))
from firm_fxfwd import forward, hedged_yield, points
from fxfwd_demo import JGB10, R_JPY, R_USD, SPOT, UST10, hedged_now, hedged_series, three_month, usdjpy_forward

T = three_month()
H = hedged_now()


def test_text():
    assert round((UST10 - JGB10) * 100, 2) == 1.81 and round((R_USD - R_JPY) * 100, 2) == 2.70
    assert round(H[0.0] * 100, 2) == 2.05
    assert (round(T["fwd0"], 4), round(T["pts0"], 1), round(T["fwd"], 4), round(T["pts"], 1)) == (
        155.8028, -106.7, 155.7059, -116.4)
    assert round(T["tn_pts"], 2) == -1.18
    assert round(10e6 * SPOT / 1e6, 2) == 1568.70 and round(10e6 * T["fwd"] / 1e6, 2) == 1557.06
    assert round((10e6 * SPOT - 10e6 * T["fwd"]) / 1e6, 2) == 11.64
    below = [d for d, _, h, g in hedged_series() if h < g]
    assert len(below) == 57 and below[0] == "2018-12-31" and "2022-11-30" in below and "2022-10-31" not in below


def test_exercises():
    f = forward(1.1464, 0.0368, 0.02, 90)
    assert round(f, 5) == 1.15119 and round(points(f, 1.1464, 0.0001), 1) == 47.9
    assert round(T["basis_back"] * 1e4) == -25
    assert round(-100e6 * (usdjpy_forward(1) - SPOT) / 1e6, 2) == 1.18


def test_problem():
    assert [round(H[b] * 100, 2) for b in (0.0, -0.0025, -0.0050)] == [2.05, 1.80, 1.55]
    assert [round((JGB10 - H[b]) * 100, 2) for b in (0.0, -0.0025, -0.0050)] == [0.89, 1.14, 1.39]
    assert round(hedged_yield(UST10, R_USD - 0.01, R_JPY, 0.0) * 100, 2) == 3.05
