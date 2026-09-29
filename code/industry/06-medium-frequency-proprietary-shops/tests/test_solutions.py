"""Numbers gate: every numerical answer printed in Book 17, chapter 6 (text and solutions)."""
import math
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import in_firmsize as m  # noqa: E402


def r(x, d=1):
    return round(float(x), d)


def test_shares():
    s = m.shares()
    assert s["firms"] == 3249 and s["reps"] == 649241
    assert (r(100 * s["le10"]), r(100 * s["le50"]), r(100 * s["small_reps"]), r(100 * s["large_reps"])) == (46.8, 78.7, 9.4, 81.7)
    assert r(100 * 149 / 3249) == 4.6 and r(100 * 93 / 103) == 90.3


def test_fit():
    f = m.fit()
    assert (r(f["pareto"]["alpha"], 2), r(f["pareto"]["se"], 3)) == (0.60, 0.015) and f["pareto"]["n"] == 1727
    assert f["bins_used"] == 13 and (r(f["chi2_lognormal"]), r(f["chi2_pareto"])) == (5.1, 21.2)
    assert r(m.fit(2024, 51)["pareto"]["alpha"], 2) == 0.65
    a20 = m.fit(2020)["pareto"]
    assert r(a20["alpha"], 3) == 0.616 and abs(a20["alpha"] - f["pareto"]["alpha"]) < 2 * math.hypot(a20["se"], f["pareto"]["se"])
    assert r(((1000.5 / 10.5) ** -0.6) * 100) == 6.5
    tail = [b for b in m.bins() if b.lo >= 11]
    assert r(100 * 84 / sum(b.n for b in tail)) == 4.9


def test_flows():
    e = m.entry_exit()
    assert (r(100 * statistics.mean(x["exit_rate"] for x in e)), r(100 * statistics.mean(x["entry_rate"] for x in e))) == (5.6, 3.2)
    assert r(100 * (1 - 3249 / 4577), 0) == 29 and r(1 / 0.056, 0) == 18


def test_splits_and_iq():
    pay = lambda g: max(0.4 * (g - 150_000), 0)  # noqa: E731
    assert [pay(g) for g in (800_000, 200_000, 100_000, 500_000, 150_000)] == [260_000, 20_000, 0, 140_000, 0]
    assert 150_000 / 0.4 == 375_000 and 3 * 252 == 756
