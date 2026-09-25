"""Numbers gate: every numerical answer printed in Book 8, chapter 24 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s1_posisig import corn, extremes, lag_table  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_lags():
    t = lag_table()
    got = {lag: (r(v["hedge"][0], 3), r(v["hedge"][1], 1), r(v["spec"][0], 3)) for lag, v in t.items()}
    assert got == {0: (0.044, 5.1, 0.043), 3: (0.038, 4.4, 0.039), 10: (0.029, 3.4, 0.031), 21: (0.017, 2.0, 0.024)}
    assert r(1 - t[3]["hedge"][0] / t[0]["hedge"][0], 2) == 0.14 and r(t[21]["hedge"][0] / t[0]["hedge"][0], 2) == 0.38


def test_extremes():
    e = extremes()
    assert {k: (r(v[0], 3), v[1]) for k, v in e.items()} == {"high": (0.045, 6603), "low": (-0.093, 7055),
                                                             "middle": (-0.034, 58752)}


def test_corn():
    c = corn()
    assert (c["n"], r(c["corr"], 3), r(c["t"], 2), r(c["mm_pm_corr"], 2)) == (113, 0.098, 1.04, -0.97)
    assert {k: (r(100 * v[0], 1), v[1]) for k, v in c["groups"].items()} == {"high": (4.6, 28), "low": (0.2, 24),
                                                                             "middle": (-0.9, 59)}
    assert [r(100 * x, 1) for x in c["mm_range"]] == [-22.8, 24.4]
    assert (str(c["dates"][0]), str(c["dates"][-1])) == ("2016-01-05", "2026-09-15")


def test_exercises():
    phi = math.exp(-math.log(2) / 20)
    assert (r(phi**3, 3), r(phi**21, 3), r(phi**10, 3)) == (0.901, 0.483, 0.707)
    assert r(1.96 / math.sqrt(113), 3) == 0.184


def test_short_half_life():
    t = lag_table(5.0)
    assert (r(t[0]["hedge"][0], 3), r(t[3]["hedge"][0], 3), r(1 - t[3]["hedge"][0] / t[0]["hedge"][0], 2)) == \
        (0.032, 0.019, 0.42)
    t20 = lag_table()
    assert [r(t20[k]["hedge"][0] / t20[0]["hedge"][0], 2) for k in (3, 10, 21)] == [0.86, 0.66, 0.38]
