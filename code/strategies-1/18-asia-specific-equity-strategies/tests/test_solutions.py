"""Numbers gate: every numerical answer printed in Book 8, chapter 18 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import numpy as np  # noqa: E402
from s1_asia import band, flows, limit_ups, market, panel  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def pct(d, keys=("open", "fill", "filled", "week")):
    return tuple(r(100 * d[k], 2 if k != "fill" else 0) for k in keys)


def test_market():
    P, o = panel(), market()
    live = P.listed[1:] & P.listed[:-1]
    ret = np.expm1(o["close"][1:] - o["close"][:-1])[live]
    assert (r(100 * ret.std(), 1), r(100 * o["down"][P.listed].mean(), 2)) == (3.1, 0.83)


def test_limit_ups_by_width():
    u5, u10, u20 = limit_ups(0.05), limit_ups(0.10), limit_ups(0.20)
    assert [(r(100 * u["freq"], 2), u["n"], r(100 * u["share_pushed"], 0)) for u in (u5, u10, u20)] == \
        [(11.24, 282172, 38), (1.29, 32277, 33), (0.1, 2325, 22)]
    assert pct(u5["all"]) == (2.98, 63, 2.12, -1.76)
    assert pct(u10["all"]) == (4.51, 57, 2.64, -2.81)
    assert pct(u20["all"]) == (6.58, 45, 3.2, -5.27)
    assert pct(u10["real"]) == (5.9, 36, 3.96, -2.77)
    assert pct(u10["pushed"]) == (1.67, 100, 1.67, -2.88)
    assert r(100 * u10["all"]["se"], 2) == 0.02 and r(100 * u20["all"]["se"], 1) == 0.1


def test_controls():
    nomag, bare = limit_ups(0.10, push=0.0), limit_ups(0.10, attention=0.0, push=0.0)
    assert r(100 * nomag["freq"], 2) == 0.87 and pct(nomag["all"]) == (5.94, 36, 4.0, -2.8)
    assert r(100 * bare["freq"], 2) == 0.79 and pct(bare["all"]) == (3.42, 37, 1.21, -0.27)


def test_magnet_band():
    (w, at_w), (n, at_n) = band(0.5), band(0.0)
    assert (r(1e4 * at_w, 0), r(1e4 * at_n, 0)) == (129, 87)
    assert [r(1e4 * a, 1) for _, a in w[-4:]] == [16.0, 11.6, 9.6, 7.4]
    assert [r(1e4 * b, 1) for _, b in n[-4:]] == [29.3, 23.3, 19.0, 14.9]


def test_northbound():
    d, q = flows(1, 0), flows(63, 5)
    assert (r(d["ic"], 3), r(d["ic_se"], 3), r(d["sr"], 2)) == (0.021, 0.001, 2.04)
    assert (r(q["ic"], 3), r(q["ic_se"], 3), r(q["sr"], 2)) == (0.003, 0.001, 0.26)


def test_exercises():
    assert r(math.log1p(0.5) / math.log1p(0.2), 2) == 2.22 and r(math.log1p(0.5) / math.log1p(0.1), 2) == 4.25
    assert r(math.exp(-(math.log1p(0.15) - math.log1p(0.10)) / 0.02), 3) == 0.108
    assert r(0.03 * 0.6**4, 4) == 0.0039
    assert r(0.03 * (1 - 0.6**4), 4) == 0.0261
    assert r(2.64 - 0.15, 2) == 2.49 and r(1.29 * 1000 / 100, 1) == 12.9
