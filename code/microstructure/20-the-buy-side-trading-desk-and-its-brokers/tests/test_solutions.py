"""Numbers gate: every numerical answer printed in Book 10, chapter 20 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from mx_wheel import card, power_study, routing_study, stratified_study, thompson_study  # noqa: E402


def r(x, d=1):
    return round(float(x), d)


def test_power_named_result():
    p = power_study()
    assert (p["months_adj"], p["months_raw"], r(p["formula_adj"]), r(p["formula_raw"]), r(p["sd_raw"])) == (
        16, 24, 15.7, 26.6, 39.1)
    s = stratified_study()
    assert (r(s["random"][1], 2), r(s["stratified"][1], 2)) == (1.59, 1.51)


def test_thompson_and_routing():
    t = thompson_study()
    th, un = t["thompson"], t["uniform"]
    assert (r(100 * th["best"]), r(100 * th["by_month"][-1]), r(th["excess"], 2), r(100 * th["power"], 0)) == (
        87.2, 97.5, 0.54, 88)
    assert (r(un["excess"], 2), r(100 * un["best"]), r(100 * un["power"], 0), r(100 * th["second"])) == (
        4.33, 16.7, 100, 5.4)
    assert r(un["excess"] - th["excess"]) == 3.8
    g = routing_study()
    assert list(g["raw_rank"]) == [6, 1, 2, 4, 3, 5] and r(g["raw"][0]) == 35.1
    assert r(min(g["adj"][1:])) == 3.8 and g["adj"].argmin() == 0


def test_scorecard():
    c = card()
    assert [x[1] for x in c] == [1175, 1246, 1171, 1169, 1207, 1232]
    assert [(r(x[2]), r(x[3]), r(x[4])) for x in c] == [(15.4, 15.1, 0.9), (16.7, 17.7, 0.9), (18.6, 18.7, 0.9),
                                                          (21.9, 21.0, 0.9), (20.5, 20.6, 0.8), (22.9, 22.7, 0.8)]
    assert [x[5] for x in c] == [1, 2, 3, 5, 4, 6]


def test_exercises():
    z = 1.959964 + 0.841621
    each = 2 * 30**2 * z**2 / 3**2
    assert round(each, -1) == 1570 and r(each * 3 / 600) == 7.8
    assert r(sum((0, 3, 4, 5, 6, 8)) / 6, 2) == 4.33
    assert (r(2 * 15**2 * z**2 / 9 * 6 / 600), r(math.sqrt(15**2 + 25**2)), r(2 * 850 * z**2 / 9 * 6 / 600)) == (3.9, 29.2, 14.8)
    assert r(30 * math.sqrt(2 / 300)) == 2.4
