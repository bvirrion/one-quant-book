"""Numbers gate: every number printed in Book 14, chapter 4 (text and solutions)."""
import functools
import math
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE / "python"))
import nw_clock as c  # noqa: E402

cs = c.cs


@functools.lru_cache
def summ(name):
    return c.summary(name)


def test_by_hand():
    assert round(100 / 15, 1) == 6.7 and round(50_000 / 15) == 3333 and round(3333 / 60) == 56
    t1, t2, t3, t4 = 0, 5300, 6300, 8900
    assert ((t2 - t1) - (t4 - t3)) / 2 == 1350 and (t4 - t1) - (t3 - t2) == 7900
    asym = 40 * 1.462 / 299_792_458 * 1e9
    assert round(asym, 1) == 195.1 and round(asym / 2, 1) == 97.5
    assert round(c.holdover(100_000, 1.0, 1e-5)) == 73_205 and round(73_205 / 3600, 1) == 20.3


def test_budget_and_holdover_problem():
    parts = dict(sat=30, cable=20, gm=40, bc1=50, bc2=50, asym=100, card=20, host=500, sw=1500)
    b = c.budget(parts)
    assert b["worst_ns"] == 2310 and round(b["rss_ns"]) == 1587 and round(100 * 2000 / 2310) == 87
    card = {k: v for k, v in parts.items() if k not in ("host", "sw")}
    b2 = c.budget(card)
    assert b2["worst_ns"] == 310 and round(b2["rss_ns"]) == 135
    margin = 100_000 - 2310
    assert margin == 97_690
    h1, h2 = c.holdover(margin, 1.0, 1e-5), c.holdover(margin, 50.0, 1e-3)
    assert round(h1, -1) == 71_870 and round(h1 / 3600, 1) == 20.0
    assert round(h2) == 1917 and round(h2 / 60) == 32 and h1 < 60 * 3600
    assert 50e6 / 2310 > 20_000


@pytest.mark.reference
def test_simulation_numbers():
    assert round(summ("software")["max_abs_ns"] / 1000, 1) == 26.3
    assert round(summ("hardware")["max_abs_ns"] / 1000, 1) == 25.9
    assert round(summ("hardware, min-delay filter")["max_abs_ns"] / 1000, 1) == 11.1
    assert round(summ("hardware, transparent clocks")["max_abs_ns"]) == 25
    mean, want = c.asymmetry_bias(2000)
    assert want == -1000 and abs(mean - want) < 5
    free, disc = c.adev()
    f, d = dict(free), dict(disc)
    assert d[2.0] > f[2.0] and d[8.0] < f[8.0]                         # crossing near 8 s
    for kw in ({}, {"min_filter": 8}):                                   # exercise 7
        r = cs.simulate(path=cs.Path(queue_ns=50_000, stamp_ns=8.0), **kw)
        o = abs(r["offset_ns"][r["t_s"] > 360]).max()
        assert o > 100_000
    r = cs.simulate(path=cs.Path(queue_ns=50_000, stamp_ns=8.0), transparent=True)
    assert round(abs(r["offset_ns"][r["t_s"] > 360]).max()) == 25


def test_small_runs():
    """Properties at reduced size: stability when the step is divided by four, and the ablation of transparent
    clocks."""
    small = dict(hours=0.15)
    tc = cs.simulate(transparent=True, path=cs.Path(stamp_ns=8.0), **small)
    tc4 = cs.simulate(transparent=True, interval_s=0.125 / 4, path=cs.Path(stamp_ns=8.0), **small)
    hw = cs.simulate(path=cs.Path(stamp_ns=8.0), **small)
    tail = lambda r: abs(r["offset_ns"][r["t_s"] > 200]).max()  # noqa: E731
    assert tail(tc) < 100 and tail(tc4) < 100 and tail(hw) > 1000
    assert math.isclose(c.asymmetry_bias(0)[1], 0.0, abs_tol=0.0)
