"""Numbers gate: every numerical answer printed in Book 16, chapter 12 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import fm_risk as m  # noqa: E402

fe = m.fe


def r(x, d=1):
    return round(float(x), d)


def test_public_record_arithmetic():
    lim = dict(m.LEHMAN_LIMITS)
    assert r(100 * (lim["2007-12"] / lim["2006-11"] - 1), 0) == 74 and r(lim["2007-12"] - m.LEHMAN_OLD_METHOD_2008, 1) == 1.5
    assert r(100 * (lim["2006-12"] / lim["2006-11"] - 1), 0) == 43 and r(100 * (4.0 / 2.5 - 1), 0) == 60


def test_severity_rules():
    assert [fe.severity(x, d) for x, d in ((0.03, 1), (0.1, 1), (0.03, 4), (0.25, 1), (0.03, 6))] == [1, 2, 2, 3, 3]


def test_one_year():
    reg, st = m.run("desk")
    assert st["n"] == 33 and r(100 * st["share"]["limit increase"]) == 51.5 and st["flagged"] == 19
    reg, st = m.run("committee")
    assert st["n"] == 21 and r(100 * st["share"]["limit increase"]) == 19.0 and st["flagged"] == 6
    d, t, days, util, lim = m.model_change_window()
    assert (d, t) == (19, 78)
    reg, _ = m.run("desk")
    mine = [(x.opened - t, x.closed - t, x.resolution, x.flags) for x in reg if x.desk == d]
    assert mine == [(-51, -50, "position cut", []), (-27, -26, "limit increase", ["limit raised during breach"]),
                    (-9, -8, "position cut", []),
                    (-5, -4, "limit increase", ["limit raised during breach", "repeated increases"]),
                    (-2, 0, "model change", ["model changed during breach", "repeated increases"])]
    assert r(100 * [x for x in reg if x.desk == d][-1].peak_excess) == 7.7
    assert (r(util[list(days - t).index(-1)], 3), r(util[list(days - t).index(0)], 3)) == (1.185, 0.881)


def test_compare():
    c = m.compare()
    sh = {k: [r(100 * c[k]["share"][x]) for x in ("position cut", "limit increase", "model change", "open")] for k in m.REGIMES}
    assert sh == {"desk": [50.0, 45.3, 3.2, 1.4], "committee": [78.4, 14.4, 6.1, 1.1], "committee_cut": [87.4, 5.4, 6.5, 0.7]}
    assert [r(c[k]["n_per_year"]) for k in m.REGIMES] == [27.8, 26.4, 27.8]
    assert [r(c[k]["mean_days"], 2) for k in m.REGIMES] == [1.15, 1.64, 1.25]
    assert [c[k]["p90_days"] for k in m.REGIMES] == [2.0, 3.0, 2.0] and [c[k]["median_days"] for k in m.REGIMES] == [1.0] * 3
    assert [r(c[k]["breach_days"] / 10) for k in m.REGIMES] == [31.8, 43.5, 34.6]
    assert [r(100 * c[k]["over_base"], 2) for k in m.REGIMES] == [2.44, 1.33, 0.74]
    assert [r(100 * c[k]["flagged_share"]) for k in m.REGIMES] == [54.7, 23.1, 11.9]
    assert [c[k]["severity"][3] for k in m.REGIMES] == [0, 2, 0] and [c[k]["severity"][2] for k in m.REGIMES] == [32, 55, 25]
    assert [r(100 * c[k]["share"]["open"]) for k in m.REGIMES] == [1.4, 1.1, 0.7]


def test_wait():
    for mm in (5, 10):
        waits = [1 + (-(t + 1)) % mm for t in range(mm)]
        assert sorted(waits) == list(range(1, mm + 1)) and sum(waits) / mm == (mm + 1) / 2


def test_small_runs():
    for regime in m.REGIMES:
        expo, hard, models = m.simulate(regime, seed=1, n_desks=3, n_days=60)
        reg = fe.register(expo, hard, models)
        assert expo.shape == (3, 60) and all(b.closed > b.opened for b in reg)
