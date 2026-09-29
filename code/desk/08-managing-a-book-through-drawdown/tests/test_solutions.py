"""Numbers gate: every numerical answer printed in Book 16, chapter 8 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import fm_drawdown as m  # noqa: E402

dd = m.dd


def r(x, d=1):
    return round(float(x), d)


def test_lorden():
    assert (r(m.lorden(10)), r(m.lorden(5)), r(m.lorden(10, -1.0)), r(m.lorden(10, -2.0))) == (15.7, 14.3, 3.9, 1.7)
    assert r(2 * math.log(2520)) == 15.7


def test_posterior_one_day():
    sd = 0.10 / math.sqrt(252)
    mu1, mu0 = 1.0 * 0.10 / 252, 0.0
    prior = 0.30 + 0.70 / 1260
    l1 = math.exp(-0.5 * ((mu0 - mu1) / sd) ** 2)
    post = prior / (prior + (1 - prior) * l1)
    assert r(prior, 4) == 0.3006 and r(post, 4) == 0.3010
    p = dd.posterior(np.array([[mu0]]), 1.0, 0.0, 0.10, 1 / 1260)
    assert r(p[0, 0], 5) == r(1 / 1260 / (1 / 1260 + (1 - 1 / 1260) * l1), 5)


@pytest.mark.reference
def test_table():
    t = m.table()
    want = {"stop-loss 10%": (9.79, 0.344, 0.72, 21.7, 15.0), "ladder 7.5 / 12.5%": (2.09, 0.600, 2.79, 39.5, 12.8),
            "time stop 18 months": (6.19, 0.802, 2.00, 54.6, 19.5), "posterior > 0.9": (2.84, 0.946, 2.68, 71.4, 18.2)}
    for k, (fs, cau, dly, va, vd) in want.items():
        v = t[k]
        assert (r(v["false_per_100y"], 2), r(v["share_caught"], 3), r(v["median_delay_days"] / 252, 2),
                r(100 * v["value_alive"]), r(100 * v["value_dead"])) == (fs, cau, dly, va, vd)
    u = t["stop-loss 10%"]
    assert (r(100 * u["value_alive_unmanaged"]), r(100 * u["value_dead_unmanaged"])) == (79.0, 11.1)
    assert r(100 * u["early_stops_dead"], 0) == 66
    assert r(50 * (t["posterior > 0.9"]["value_alive"] + t["posterior > 0.9"]["value_dead"])) == 44.8


@pytest.mark.reference
def test_drawdown_stats_and_examples():
    assert tuple(r(100 * x) for x in m.drawdown_quantiles()) == (16.8, 25.4)
    a = m.at_drawdown()
    assert (r(a["alive"][0], 2), r(a["broken"][0], 2), r(100 * a["broken"][1], 0)) == (0.24, 0.39, 13)
    ea, pa, eb, pb = m.examples()
    assert r(pa.max(), 2) == 0.80 and int(np.argmax(pa) / 252) == 3 and int(np.argmax(pb > 0.9) / 252) == 4


@pytest.mark.reference
def test_losing_break():
    old = m.SR_DEAD
    m.SR_DEAD = -1.0
    try:
        t = m.table()
    finally:
        m.SR_DEAD = old
    p = t["posterior > 0.9"]
    assert (r(p["median_delay_days"] / 252, 1), r(p["false_per_100y"], 2)) == (1.3, 2.24)
    mix = {k: 50 * (v["value_alive"] + v["value_dead"]) for k, v in t.items()}
    assert [r(x) for x in mix.values()] == [17.5, 23.2, 31.3, 39.3]
    u = t["stop-loss 10%"]
    assert r(50 * (u["value_alive_unmanaged"] + u["value_dead_unmanaged"])) == 10.1


def test_small_runs():
    t = m.table(n=150)
    assert t["posterior > 0.9"]["share_caught"] > t["stop-loss 10%"]["share_caught"]
    assert t["stop-loss 10%"]["false_per_100y"] > t["ladder 7.5 / 12.5%"]["false_per_100y"]
