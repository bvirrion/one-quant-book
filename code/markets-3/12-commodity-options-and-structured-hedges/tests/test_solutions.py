"""Numbers gate: every numerical answer printed in Book 3, Chapter 12 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/hedgeprog"))
from firm_hedgeprog import Leg, black76, hedged_revenue, three_way
from m3_options import averages, producer_car, sovereign, vanilla_vs_average

V = vanilla_vs_average()
S = sovereign()
P = producer_car()


def test_text():
    assert round(V["vanilla"], 2) == 5.51 and round(V["apo"], 2) == 2.66
    assert round(P["collar_cost"], 2) == 0.07 and round(P["put_cost"], 2) == 2.66
    assert round(S["call_strike"], 2) == 70.24
    assert round(P["unhedged"], 2) == 8.43 and P["collar"] == 0.0 and P["put"] == 0.0


def test_exercises():
    assert hedged_revenue(np.array([55.0]), [Leg("swap", 62.0, -1)], 0.0)[0] == 62.0
    c = hedged_revenue(np.array([40.0, 60.0, 90.0]), [Leg("put", 50.0), Leg("call", 75.0, -1)], 0.0)
    assert list(c) == [50.0, 60.0, 75.0]
    tw = hedged_revenue(np.array([30.0, 50.0, 65.0, 90.0]), three_way(60.0, 45.0, 70.24), 0.0)
    assert [round(v, 2) for v in tw] == [45.0, 60.0, 65.0, 70.24]
    assert round(float(np.std(np.log(averages()), ddof=1)) * 100, 1) == 21.3
    assert round(0.35 / math.sqrt(3) * 100, 1) == 20.2 and round(0.35 * math.sqrt(13 * 25 / 864) * 100, 1) == 21.5
    call = black76(60, 55, 1, 0.35, 0.04, True)
    assert round(call, 2) == 10.31 and round(call - V["vanilla"], 2) == round(math.exp(-0.04) * 5, 2) == 4.80


def test_problem():
    assert round(S["premium"], 2) == 2.66 and round(S["cost_usd"] / 1e6) == 664 and round(S["share"] * 100, 1) == 4.4
    assert S["pay45"] == (2.5e9, 3.75e9) and S["pay30"] == (6.25e9, 3.75e9)
    assert round(-S["pay90"][1] / 1e9, 2) == 4.94 and S["revenue_usd"] == 15e9


def test_swing_example():
    from m3_options import swing_example
    assert swing_example() == 400.0
