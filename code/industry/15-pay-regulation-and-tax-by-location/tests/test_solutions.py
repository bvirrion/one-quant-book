"""Numbers gate: every numerical answer printed in Book 17, chapter 15 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import in_tax as a  # noqa: E402

at, P = a.at, a.P
M = a.million()


def test_million_table():
    want = {"dubai": (1_000_000, 0.0, 0.0), "hong_kong": (844_104, 15.6, 16.0), "singapore": (791_283, 20.9, 24.0),
            "zurich": (599_515, 40.0, 44.4), "chicago": (597_361, 40.3, 44.3), "london": (545_545, 45.4, 47.0),
            "new_york": (540_584, 45.9, 50.1), "amsterdam": (516_376, 48.4, 49.5)}
    got = {k: (round(M[k]["net"]), round(100 * M[k]["avg"], 1), round(100 * M[k]["marginal"], 1)) for k in want}
    assert got == want
    ex = M["amsterdam expat"]
    assert round(ex["net"]) == 560_341 and round(100 * ex["avg"], 1) == 44.0 and round(100 * ex["marginal"], 1) == 49.5
    assert round(ex["net"] - M["amsterdam"]["net"]) == 43_964
    loc = {k: round(M[k]["local"]) for k in ("london", "amsterdam", "zurich", "singapore", "hong_kong")}
    assert loc == {"london": 758_235, "amsterdam": 884_969, "zurich": 829_243, "singapore": 1_305_833,
                   "hong_kong": 7_796_944}


def test_spread():
    s = a.spread()
    assert (s["hi"], s["lo"], round(s["ratio"], 2)) == ("dubai", "amsterdam", 1.94)
    five = [k for k in at.LOCATIONS if M[k]["avg"] >= 0.3995]
    assert sorted(five) == ["amsterdam", "chicago", "london", "new_york", "zurich"]
    assert round(100 * (max(M[k]["net"] for k in five) / min(M[k]["net"] for k in five) - 1)) == 16


def test_curve_statements():
    c = a.curve()
    g = list(a.GRID)
    assert c["new_york"][g.index(750e3)] < c["london"][g.index(750e3)]
    assert c["new_york"][g.index(1e6)] > c["london"][g.index(1e6)]
    assert round(100 * c["new_york"][g.index(1e6)], 1) == 45.9 and round(100 * c["new_york"][g.index(1.5e6)], 1) == 50.1
    mid = [c[k] for k in ("london", "new_york", "chicago", "amsterdam", "zurich")]
    assert 22 < 100 * min(min(v) for v in mid) < 23 and 51 < 100 * max(max(v) for v in mid) < 52
    assert 10 < 100 * min(c["singapore"]) and 100 * max(c["singapore"] + c["hong_kong"]) < 24
    assert round(100 * c["zurich"][-1], 1) == 41.7 and round(100 * c["chicago"][-1], 1) == 43.0


def test_exercises():
    r = at.net_local(P, "london", 100_000.0)
    assert (r["tax"], round(r["social"], 2), round(r["net"], 2)) == (27_432.0, 4_010.6, 68_557.4)
    assert at.progressive(2_132_500 - 145_000, P["hk", "brackets"]) == 319_875 == round(0.15 * 2_132_500)
    cross = next(g for g in range(150_000, 3_000_001, 1000)
                 if at.net_usd(P, "new_york", g)["net"] < at.net_usd(P, "london", g)["net"])
    assert cross == 839_000
    lo, hi = 1e6, 3e6
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if at.net_usd(P, "amsterdam", mid)["net"] < 1e6 else (lo, mid)
    assert round(hi / 1e6, 2) == 1.96
    assert 0.30 * 262_000 == 78_600


def test_small_runs():
    assert all(0 <= at.net_usd(P, k, 2e5)["avg_rate"] < 0.5 for k in at.LOCATIONS)


def test_marginal_curve_and_fx():
    mc = a.marginal_curve()
    g = list(a.MGRID)
    assert round(100 * mc["london"][0]) == 62 and round(100 * mc["amsterdam"][0]) == 56
    assert all(round(100 * x, 1) == 47.0 for x in mc["london"][g.index(200_000.0):])
    assert all(round(100 * x, 1) == 49.5 for x in mc["amsterdam"][g.index(200_000.0):])
    assert max(mc["singapore"]) <= 0.24 + 1e-9 and max(mc["hong_kong"]) <= 0.17 + 1e-9
    fx = a.P
    r24 = 1.08238046875 / 0.8466166015625
    r25 = fx["fx", "usd_per_eur"] / fx["fx", "gbp_per_eur"]
    assert (round(r24, 4), round(r25, 4), round(100 * (r25 / r24 - 1), 1)) == (1.2785, 1.3189, 3.2)
    assert round(1_000_000 / 3) == 333_333 and 1_000_000 / 2 == 500_000


def test_new_york_band_over_one():
    ti = [g for g in range(1_000_000, 1_300_000, 1000) if at.marginal(P, "new_york", float(g), 1000.0) > 1.0]
    assert ti and min(ti) - 8_000 > 1_077_550 and max(ti) - min(ti) <= 50_000
