"""Numbers gate: every numerical answer printed in Book 16, chapter 23 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import fm_deals as m  # noqa: E402

dt = m.dt


def r(x, d=0):
    return round(float(x), d)


def test_published_terms():
    assert (m.PROG.rebate, m.PROG.volume_share, m.PROG.symbols) == (0.000075, 0.0125, 2700)
    assert r(m.PROG.volume_share * m.TCV / 1e6) == 150 and r(m.PROG.rebate * 150e6) == 11250
    assert r(11250 * m.DAYS / 1e6, 2) == 2.83


def test_breakeven():
    assert r(100 * m.breakeven(), 2) == 1.16
    assert (m.SMALL.symbols, m.LARGE.symbols) == (1080, 5400)


def test_deals():
    s = m.deal(m.SMALL, m.R_SMALL)
    assert (r(s["value"]["rebate"]), r(s["value"]["padding"]), r(s["value"]["quoting"]), r(s["value"]["net"])) == (
        11250, 102000, 3240, -93990)
    assert (r(s["venue_gain"]), s["transfer"]) == (22500, None) and s["zopa"][0] > s["zopa"][1]
    t = m.deal(m.SMALL, m.R_SMALL, prog=m.tailored(m.SMALL))
    assert (r(t["venue_gain"]), r(t["transfer"]), round(t["rebate_per_share"], 7)) == (7200, 3600, 0.000075)
    b = m.deal(m.LARGE, m.R_LARGE)
    assert (r(b["venue_gain"]), [r(x) for x in b["zopa"]], r(b["transfer"]), r(b["published"])) == (
        36000, [10000, 36000], 23000, 18000)
    assert round(b["rebate_per_share"], 8) == 0.00009583 and r(m.deal(m.LARGE, 0.0)["transfer"]) == 18000
    assert r(100 * (0.00009583 / 0.000075 - 1)) == 28


def test_small_runs():
    assert dt.nash_transfer(10.0, 12.0, 0.0, 0.0) is None and dt.nash_transfer(10.0, 2.0, 2.0, 0.0) == 7.0


def test_exercises():
    b = m.deal(m.LARGE, m.R_LARGE, beta=0.3)
    assert r(b["transfer"]) == 17800 and round(b["rebate_per_share"], 8) == 0.00007417
