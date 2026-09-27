"""Numbers gate: every numerical answer printed in Book 7, chapter 17 (text and solutions)."""
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rs_evbt as ev
from rs_evbt import at_close, level1, run


def mean(rows, k):
    return float(np.mean([d[k] for d in rows]))


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_no_latency():
    t, p, c = run("touch"), run("penetration"), run("capped")
    assert [round(mean(x, "filled_lots")) for x in (t, p, c)] == [523, 290, 388]
    assert [round(100 * mean(x, "filled_lots") / mean(x, "orders")) for x in (t, p, c)] == [70, 41, 55]
    assert [round(mean(x, "pnl")) for x in (t, p, c)] == [17, -584, 20]
    assert [round(mean(x, "markout"), 2) for x in (t, p, c)] == [-0.16, -2.0, -0.18]
    assert round(100 * mean(p, "filled_lots") / mean(t, "filled_lots")) == 55
    assert [round(d["pnl"]) for d in t] == [-333, 206, 12, 184] and all(d["pnl"] < 0 for d in p)
    assert round(float(np.mean(level1()))) == -215


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_latency():
    for m in ("touch", "penetration", "capped"):
        assert mean(run(m, 5.0, "conservative"), "filled_lots") == 0.0
    t, p, c = run("touch", 5.0, "optimistic"), run("penetration", 5.0, "optimistic"), run("capped", 5.0, "optimistic")
    assert [round(mean(x, "filled_lots")) for x in (t, p, c)] == [585, 372, 440]
    assert [round(mean(x, "pnl")) for x in (t, p, c)] == [-41, -776, -190]
    assert round(mean(c, "markout"), 2) == -0.87


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_exercises():
    ft, fp = at_close("touch"), at_close("penetration")
    assert (round(100 * ft[0]), round(ft[1], 2), round(ft[2])) == (95, -0.17, -188)
    assert (round(100 * fp[0]), round(fp[1], 2), round(fp[2])) == (70, -1.16, -506)
    assert [round(0.025 * v) for v in (40_000, 10_000, 60_000)] == [1000, 250, 1500]
    assert 5000 - (1000 + 250 + 1500) == 2250


def test_small_runs():
    # Half an hour of one day instead of four full days: the quoter trades under the optimistic touch model, and the
    # stricter penetration model never fills more.
    _, bars = ev.day(17, seconds=1800.0)
    n = {m: len(ev.Engine(bars, ev.Quoter(), ev.MODELS[m](), capital=1e6).run()[2]) for m in ("touch", "penetration")}
    assert n["touch"] > 0 and n["penetration"] <= n["touch"]
