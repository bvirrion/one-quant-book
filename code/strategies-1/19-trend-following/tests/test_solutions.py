"""Numbers gate: every numerical answer printed in Book 8, chapter 19 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import s1_trend  # noqa: E402
from firm_synthfut import FutConfig, simulate_futures  # noqa: E402
from s1_trend import crises, decades, lookbacks, market, smile, summary, table, wti  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_universe():
    F = market()
    assert [r(F["r"][:, F["cls"] == k].std() * math.sqrt(252), 3) for k in range(4)] == [0.173, 0.069, 0.094, 0.271]
    assert [(r(s / 252, 1), e - s) for s, e in F["crashes"]] == [(7.5, 100), (18.0, 100), (27.0, 100)]


def test_signal_table():
    t = table()
    got = [(r(a), r(b, 0), r(c)) for a, b, c in t.values()]
    assert got == [(-0.0, 49, 0.32), (0.26, 29, 0.46), (0.66, 15, 0.76),
                   (0.1, 33, 0.32), (0.43, 9, 0.48), (0.72, 5, 0.76),
                   (0.17, 18, 0.29), (0.34, 8, 0.39), (0.78, 3, 0.8)]


def test_blends_and_scaling():
    s = summary()
    assert (r(s["blend"]), r(s["all9"]), r(s["equal_notional"]), r(s["targeted"])) == (0.4, 0.55, 0.31, 0.34)
    assert (r(100 * s["vol_blend"], 1), r(100 * s["vol_targeted"], 1)) == (7.7, 10.2)
    assert (r(s["dd_blend"], 1), r(s["dd_targeted"], 1)) == (3.7, 3.8)


def test_crises_smile_decades():
    assert [(r(100 * a, 1), r(100 * b, 1)) for a, b in crises()] == [(-6.8, 2.3), (-24.3, 21.1), (-35.1, 39.0)]
    x, y, c = smile()
    assert (len(x), r(c[0]), r(c[1]), r(c[2])) == (115, 2.63, 0.03, -0.01)
    assert (r(100 * x.min(), 1), r(100 * y[x.argmin()], 1), r(np.corrcoef(x, y)[0, 1])) == (-36.2, 31.6, -0.09)
    assert [r(v) for v in decades()] == [0.56, 0.24, 0.34]


def test_lookbacks():
    assert [(m, r(v)) for m, v in lookbacks()] == [(1, -0.0), (2, 0.06), (3, 0.26), (6, 0.56), (9, 0.52), (12, 0.66),
                                                  (18, 0.51), (24, 0.53)]


def test_wti():
    w = wti()
    assert (r(w["sr"]), r(100 * w["ret"], 1), r(w["hold_sr"]), w["first"], w["last"], r(100 * w["long_share"], 0)) == \
        (0.22, 9.0, 0.04, 1986, 2024, 54)


def test_faster_trends_exercise():
    F = simulate_futures(FutConfig(trend_half_life=63.0))
    F["cost"] = np.array(s1_trend.COST_BP)[F["cls"]] / 1e4
    F["ewma"] = s1_trend.ewma_vol(F["r"])
    old = s1_trend.market
    try:
        s1_trend.market = lambda: F
        assert [(m, r(v)) for m, v in lookbacks((3, 6, 12))] == [(3, 0.13), (6, 0.39), (12, 0.42)]
    finally:
        s1_trend.market = old


def test_exercises():
    lam = 60 / 61
    assert (r(lam, 4), r(math.log(0.5) / math.log(lam), 0)) == (0.9836, 42)
    assert (r(0.4 / (40 * 0.25), 2), r(0.4 / (40 * 0.06), 3)) == (0.04, 0.167)
    assert r(2.63 * 0.09 + 0.03 * -0.30 - 0.01, 3) == 0.218
    assert r(math.sqrt(1 / 10), 2) == 0.32 and r(0.4 - 0.32, 2) == 0.08 and r(0.4 + 0.32, 2) == 0.72
    assert r(1 / math.sqrt(38), 2) == 0.16 and 2024 - 1986 == 38 and r(1 / math.sqrt(25), 2) == 0.2
