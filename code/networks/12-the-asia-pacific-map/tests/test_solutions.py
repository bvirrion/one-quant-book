"""Numbers gate: every number printed in Book 14, chapter 12 (text and solutions)."""
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import nw_asia as a  # noqa: E402

fd, gm = a.fd, a.gm


def test_pairs_table():
    rows = {(p["a"], p["b"]): p for p in a.pair_rows()}
    expect = {("tokyo", "tko"): (2880.3, 9.61, 14.05), ("tko", "singapore"): (2577.1, 8.60, 12.57),
              ("tokyo", "singapore"): (5311.0, 17.72, 25.90), ("singapore", "alc"): (6296.4, 21.00, 30.71),
              ("tokyo", "alc"): (7784.2, 25.97, 37.96), ("singapore", "bkc"): (3903.3, 13.02, 19.04),
              ("tko", "bkc"): (4317.3, 14.40, 21.05), ("tokyo", "bkc"): (6743.1, 22.49, 32.88)}
    for k, (km, vac, fib) in expect.items():
        p = rows[k]
        assert (round(p["km"], 1), round(p["vacuum_us"] / 1e3, 2), round(p["fibre_us"] / 1e3, 2)) == (km, vac, fib), k


def test_model_by_hand():
    kw = {k: v for k, v in a.PARAMS.items() if k != "jitter"}
    t = fd.unicast_us(a.TOPOLOGY, jitter=0, **kw)
    M = fd.Member
    assert (t[M("server 1", 0, 0)], t[M("server 1", 0, 9)]) == (15, 105)
    assert (t[M("server 1", 0, 4)], t[M("server 1", 0, 5)]) == (55, 65)
    assert (t[M("server 4", 0, 0)], t[M("server 4", 0, 9)]) == (30, 120)
    assert (t[M("secondary", 0, 0)], t[M("secondary", 0, 1)]) == (35, 45)
    f = fd.fairness(t)
    assert (f["first"], f["last"]) == (15, 120)
    assert len(fd.members(a.TOPOLOGY)) == 126 and sum(1 for m in fd.members(a.TOPOLOGY) if m.server == "secondary") == 6


@pytest.mark.reference
def test_designs_table():
    s = a.scenarios()
    u, r, n, m = s["unicast"], s["unicast, randomised"], s["unicast, randomised, no secondary"], s["multicast"]
    assert (round(u["first"], 1), round(u["median"], 1), round(u["spread"], 1), round(u["stability"], 2)) == (16.0, 65.6, 107.7, 1.00)
    assert round(100 * u["win_first"]) == 100 and round(u["median"]) == 66 and round(u["first"]) == 16
    assert (round(r["first"], 1), round(r["median"], 1), round(r["spread"], 1), round(r["stability"], 2)) == (15.1, 70.7, 110.2, 0.07)
    assert round(100 * r["win_first"]) == 88 and round(r["spread"]) == 110
    assert (round(n["first"], 1), round(n["median"], 1), round(n["spread"], 1), round(n["stability"], 2)) == (15.2, 69.0, 106.9, 0.01)
    assert round(100 * n["win_first"]) == 51
    assert (round(m["first"], 1), round(m["median"], 1), round(m["spread"], 1), round(100 * m["win_first"])) == (10.0, 10.7, 8.4, 50)
    assert round(m["first_vs_median"], 1) == 0.7 and round(u["spread"]) == 108


@pytest.mark.reference
def test_first_vs_median():
    assert [round(a.first_vs_median(m), 1) for m in (2, 5, 10, 20)] == [15.5, 28.5, 50.4, 100.5]


def test_small_runs():
    rc = a.rank_curve(ticks=5)
    assert rc[("server 1", 0)] < rc[("server 2", 0)] < rc[("server 1", 9)]
    assert a.first_vs_median(10, ticks=5) == pytest.approx(50, abs=5)
    assert len(a.map_points()) == 5
