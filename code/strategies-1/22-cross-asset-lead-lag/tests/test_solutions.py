"""Numbers gate: every numerical answer printed in Book 8, chapter 22 (text and solutions)."""
import math
import pathlib
import sys
from statistics import NormalDist

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s1_xasset import daily, intraday  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_daily():
    d = daily()
    assert d["lag_hits"] == [(4, 0, 0)] and (r(d["lag_thr"]), r(d["window_thr"])) == (4.06, 3.48)
    assert [r(v, 1) for v in d["window_t"]] == [3.2, 4.1, 4.1] and d["found"] == [(1, 3), (2, 7)]
    assert [r(v, 1) for v in d["lag_t_max"]] == [4.7, 2.7, 3.5]
    assert (r(d["gross"]), r(d["net"])) == (2.09, 1.73)


def test_intraday():
    i = intraday()
    assert set(i["leads"]) == {2.0} and len(i["leads"]) == 20
    assert [r(v) for v in i["ccf"]] == [0.0, 0.01, 0.02, 0.04, 0.09, 0.2, 0.41, 0.74, 1.0, 0.74, 0.41, 0.2, 0.09]
    got = [(r(i[k]["n"], 0), r(i[k]["bp"]), r(100 * i[k]["hit"], 1), i[k]["days_up"]) for k in range(4)]
    assert got == [(2343, 0.73, 69.6, 20), (2193, 0.35, 57.2, 20), (2025, -0.51, 32.0, 0), (1862, -0.81, 25.0, 0)]


def test_exercises():
    z = NormalDist().inv_cdf
    assert (r(z(1 - 0.05 / 2000)), r(z(1 - 0.05 / 200))) == (4.06, 3.48)
    per_lag = 0.08 * 25 / 8 / 5
    window = 0.08 * 25 / 8 / math.sqrt(5)
    assert (r(per_lag, 3), r(per_lag * math.sqrt(1260), 2), r(window, 3), r(window * math.sqrt(1255), 2)) == \
        (0.05, 1.77, 0.112, 3.96)
    assert r(0.73 + 1.0, 2) == 1.73 and r(-0.51 + 1.0, 2) == 0.49


def test_stronger_diffusion_exercise():
    from s1_xasset import panels, window_t
    d = daily(0.12)
    assert d["lag_hits"] == [(0, 2, 7), (4, 0, 0)] and d["found"] == [(0, 0), (1, 3), (2, 7), (9, 3)]
    assert [r(v, 1) for v in d["window_t"]] == [5.3, 6.1, 6.2] and r(d["net"]) == 2.56
    com, fol = panels(0.12)
    wt = window_t(com, fol, len(fol) // 2)
    assert r(wt[9, 3], 1) == 3.7 and r(np.corrcoef(com[: len(fol) // 2, 9], com[: len(fol) // 2, 1])[0, 1]) == 0.21
