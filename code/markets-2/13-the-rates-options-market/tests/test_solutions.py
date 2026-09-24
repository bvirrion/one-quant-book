"""Numbers gate: every numerical answer printed in Book 2, Chapter 13 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from swaption_demo import (
    annuity,
    bachelier,
    black_equivalents,
    bp_per_day,
    callable_swap,
    cap,
    load_negative_yields,
    no_black_below,
    normal_to_black,
    normal_vega,
    straddle_1y10y,
)

S = straddle_1y10y()
C = cap()
CB = callable_swap()
B = dict(black_equivalents())


def test_text():
    rows = load_negative_yields()
    de = [x for _, x, _ in rows if x < 0]
    jp = [x for _, _, x in rows if x < 0]
    assert (len(de), round(min(de), 2), len(jp), round(min(jp), 2)) == (38, -0.65, 24, -0.28)
    assert [round(x) for x in C["caplets"]] == [182_874, 310_339, 401_400, 470_709]
    assert round(C["cap"] / 1e6, 2) == 1.37 and round(C["cap"] / 1e8 * 1e4) == 137
    assert round(C["floor"]) == round(C["cap"])
    assert round(annuity(1, 11), 2) == 7.80
    assert round(bp_per_day(0.0095), 2) == 5.98
    assert (round(B[4.0], 1), round(B[1.0]), round(B[0.5])) == (22.5, 93, 215)
    assert round(no_black_below() * 100, 2) == 0.36
    assert round(S["premium_bp"] / 100, 2) == 5.91 and round(S["premium"] / 1e6, 2) == 5.91
    assert round(S["breakeven_bp"], 1) == 75.8


def test_exercises():
    assert round(7 * math.sqrt(252), 1) == 111.1
    assert round(bachelier(0.04, 0.04, 1, 0.0095, annuity(1, 11)) * 1e8 / 1e6, 2) == 2.96
    assert [round(B[f], 1) for f in (6.0, 2.0, 0.4)] == [15.0, 45.4, 326.7]
    assert round(0.009 / math.sqrt(2 * math.pi), 5) == 0.00359


def test_problem():
    assert round(CB["annuity"], 3) == 5.336
    assert round(CB["price"] / 1e6, 2) == 25.87 and round(CB["price_bp"]) == 517
    assert round(CB["vega"]) == 176_826 and round(CB["delta"]) == -163_698
    assert round(-CB["vol_down_2"]) == 353_651
    assert round(CB["straddle_vega_100m"]) == 73_740 and round(CB["straddles"] / 1e6, -1) == 240
    assert round(CB["running_bp"], 1) == 63.8 and round(annuity(0, 10), 2) == 8.11
    a = annuity(3, 10)
    assert round(bachelier(0.035, 0.045, 3, 0.01, a, payer=False) * 5e8 / 1e6, 2) == 34.76
    assert round(normal_vega(0.035, 0.045, 3, 0.01, a) * 5e8 * 1e-4) == 156_048
    assert round(normal_to_black(0.04, 0.04, 1, 0.009) * 100, 1) == 22.5
