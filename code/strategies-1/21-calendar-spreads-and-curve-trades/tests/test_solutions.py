"""Numbers gate: every numerical answer printed in Book 8, chapter 21 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s1_curve import book, persistence, synthetic, wti  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def row(b):
    return (r(b["gross"]), r(b["net"]), r(100 * b["ret"], 1), r(100 * b["vol"], 1), r(100 * b["active"], 0),
            r(100 * b["y2020"], 1), r(100 * b["mar"], 1), r(100 * b["apr"], 1))


def test_persistence():
    phi, hl = persistence()
    assert (r(phi, 3), r(hl, 1)) == (0.949, 13.3)


def test_books():
    assert row(book(None)) == (0.3, 0.05, 0.5, 9.9, 47, -42.7, -58.3, 22.9)
    assert row(book(-0.8)) == (0.33, 0.08, 0.7, 9.7, 47, -28.1, -20.8, 0.0)
    assert row(book(-0.4)) == (0.31, 0.05, 0.4, 9.3, 45, -17.8, -10.5, 0.0)
    assert row(book(-0.2)) == (0.39, 0.14, 1.2, 9.0, 41, -8.8, -1.5, 0.0)


def test_2020_path():
    w, p = wti(), book(None)["pos"]
    yr = np.array([d.year for d in w["dates"]])
    pre = (yr >= 1986) & (yr <= 2019)
    assert (r(100 * np.mean(w["carry"][pre] < -0.2), 1), r(100 * np.mean(w["carry"][pre] < -0.4), 1)) == (13.1, 3.5)
    at = {str(d): i for i, d in enumerate(w["dates"])}
    assert [r(100 * w["carry"][at[k]], 1) for k in ("2020-03-31", "2020-04-20", "2020-04-21")] == [-215.6, -302.2, -575.5]
    longs = [str(w["dates"][i]) for i in range(len(p)) if w["dates"][i].year == 2020 and w["dates"][i].month <= 6
             and p[i] > 0]
    assert (longs[0], longs[-1], len(longs)) == ("2020-01-10", "2020-04-23", 54)


def test_synthetic():
    d, m = synthetic(252, False), synthetic(252, True)
    assert (r(d["gross"]), r(d["net"]), r(m["gross"]), r(m["net"]), r(m["corr_dc"])) == (1.0, -0.29, 1.05, 0.76, 1.0)


def test_exercises():
    assert r(math.log(0.5) / math.log(0.949), 1) == 13.2
    assert r(-0.01 * 252 / 21, 2) == -0.12 and r(-5.755 * 21 / 252, 2) == -0.48 and r(math.exp(-0.48), 2) == 0.62
    assert r(0.30 * 10 - 0.05 * 9.9, 1) == 2.5


def test_rounded_mentions():
    w = wti()
    at = {str(d): i for i, d in enumerate(w["dates"])}
    assert [r(100 * w["carry"][at[k]], 0) for k in ("2020-03-31", "2020-04-20", "2020-04-21")] == [-216, -302, -575]
    assert r(100 * w["carry"][at["2020-01-02"]], 1) == 4.5 and 2024 - 1985 == 39


def test_subperiods():
    w, x = wti(), book(None)["net_series"]
    yr = np.array([d.year for d in w["dates"]])
    out = []
    for a, b in ((1986, 2004), (2005, 2019)):
        m = (yr >= a) & (yr <= b)
        out.append(r(x[m].mean() / x[m].std(ddof=1) * math.sqrt(252)))
    assert out == [0.47, -0.32]
