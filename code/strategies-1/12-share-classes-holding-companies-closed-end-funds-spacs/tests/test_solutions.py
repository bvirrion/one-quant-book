"""Numbers gate: every numerical answer printed in Book 8, chapter 12 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s1_structrv import fund, holding, spac  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def f(x):
    return (r(100 * x["mean"], 1), r(100 * x["ann"], 2), r(x["median_years"], 2), r(100 * x["closed"], 0),
            r(100 * x["catalyst"], 0), r(100 * x["p5"], 1), r(100 * x["loss"], 0))


def test_funds():
    assert f(fund(0.0)) == (1.9, 0.87, 2.96, 50, 0, -14.7, 40)
    assert f(fund(0.1)) == (4.4, 2.23, 2.13, 63, 19, -13.3, 30)
    assert f(fund(0.3)) == (7.9, 5.04, 1.37, 79, 46, -10.4, 17)
    assert f(holding()) == (2.8, 0.94, 3.0, 2, 0, -13.9, 40)


def test_spac():
    s = spac()
    assert (r(100 * s["mean"], 1), r(100 * s["floor"], 1), r(100 * s["redeem"], 0), r(100 * s["hold_mean"], 1),
            r(100 * s["hold_median"], 1)) == (20.2, 6.2, 74, -13.9, -27.8)


def test_exercises():
    assert (r(100 * math.log(0.85), 1), r(100 * math.log(0.90), 1), r(100 * math.log(0.95), 1)) == (-16.3, -10.5, -5.1)
    assert r(100 * (math.log(0.95) - math.log(0.85) - 0.013), 1) == 9.8
    assert r(100 * (10 * math.exp(0.04) / 9.8 - 1), 1) == 6.2 and r(10 * math.exp(0.04), 2) == 10.41
    assert r(100 * 0.5 ** (1 / 2), 1) == 70.7 and r(100 * (math.log(0.95) - math.log(0.85)), 1) == 11.1
    assert r(100 * (fund(0.3)['ann'] - fund(0.0)['ann']), 1) == 4.2
