"""Numbers gate: every numerical answer printed in Book 16, chapter 15 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import fm_finance as m  # noqa: E402

so = m.so


def r(x, d=0):
    return round(float(x), d)


def test_the_day():
    w = m.the_walk()
    assert [r(w[k]) for k in ("flash", "market moves after the flash", "late trades", "fees", "valuation adjustments",
                             "final", "unexplained")] == [475100, 63910, 1580, -11670, -149787, 379133, 0]
    assert m.late_count() == 6 and r(w["final"] - w["flash"]) == -95967 and r(100 * (w["final"] / w["flash"] - 1), 1) == -20.2
    assert [(k, r(v)) for k, v in m.day_exceptions()] == [("valuation adjustments", -149787)]
    status, trail = m.day_signoff()
    assert status == "escalated" and len(trail) == 2
    d = m.day()
    assert r(sum(abs(q) * d["sod_px"][s] for s, q in d["sod"].items()) / m.U / 1e6, 1) == 66.5
    assert [(d["close"][s], d["final"][s]) for s in m.ILLIQUID] == [(1234900, 1226274), (1069000, 1063345), (425500, 419327)]
    assert (d["consensus"]["S7"], d["tolerance"]["S7"], d["sod"]["S7"]) == (1220100, 6174, 73000)


def test_tax():
    t = m.tax_table()
    assert [[r(100 * x, 2) for x in t[s].values()] for s in m.STRATEGIES] == [
        [11.85, -8.0, 3.85], [8.77, 6.0, 7.58], [6.48, 6.6, 6.31]]
    assert m.half_turnovers() == {0.001: 40.0, 0.002: 20.0, 0.005: 8.0}
    assert r(100 * so.blended(0.37, 0.20), 1) == 26.8 and r(100 * 40 * 0.005) == 20 and r(100 * 6 * 0.005) == 3


def test_other_seed():
    w = m.the_walk(17)
    assert (r(w["flash"]), r(w["final"])) == (529950, 463393)
    assert [k for k, _ in so.exceptions(w, m.ABS_TOL, m.REL_TOL, m.CAT_TOL)] == ["valuation adjustments"]


def test_exercise_numbers():
    w = m.the_walk(17)
    assert r(w["final"] - w["flash"]) == -66557 and r(100 * so.tax_drag(0.06, 25, 0.002), 2) == 1.0
    assert r(100 * 0.035 * 0.15, 2) == 0.53 and r(100 * 0.8 * 0.005, 2) == 0.4
    assert r(1234900 / 1220100 * 100 - 100, 1) == 1.2
