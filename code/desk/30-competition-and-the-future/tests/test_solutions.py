"""Numbers gate: every numerical answer printed in Book 16, chapter 30 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import fm_competition as m  # noqa: E402

fm = m.fm


def r(x, d=2):
    return round(float(x), d)


def test_public_bounds():
    lo, hi = m.public_bounds()
    assert (r(lo, 0), r(hi, 0)) == (2467, 3668)
    assert r(fm.hhi([1 / 6] * 6), 0) == 1667 and r(fm.hhi([0.33, 0.33, 0.085, 0.085, 0.085, 0.085]), 0) == 2467


def test_entry():
    e = m.entry()
    assert (e["n"], r(e["hhi"], 0), e["planner"], r(e["profit"], 1)) == (6, 1667, 3, 11.2)
    assert (r(e["w_free"], 0), r(e["w_plan"], 0)) == (1169, 1256)
    h, d = m.entry(25.0), m.entry(100.0)
    assert (h["n"], r(h["hhi"], 0), h["planner"]) == (9, 1111, 4) and (d["n"], r(d["hhi"], 0), d["planner"]) == (4, 2500, 2)
    assert r(fm.welfare(m.S, m.F, 6) / fm.welfare(m.S, m.F, 3), 3) == 0.931


def test_merger():
    x = m.merger()
    assert (r(x["pre"]["price"], 3), r(x["post"]["price"], 3), r(x["pre"]["hhi"], 0), r(x["post"]["hhi"], 0)) == (4.857, 5.0, 1667, 2000)
    assert (r(x["net_pre"], 1), r(x["net_post"], 1), r(100 * (5.0 / x["pre"]["price"] - 1), 1)) == (22.4, 33.3, 2.9)
    assert (r(x["pre"]["cs"], 0), r(x["post"]["cs"], 0)) == (1102, 1042)
    assert (r(x["needed"], 3), r(100 * x["needed"] / m.C, 1)) == (0.857, 21.4)
    y = m.merger(x["needed"])
    assert (r(y["post"]["price"], 3), r(y["post"]["hhi"], 0), r(100 * y["post"]["shares"][-1], 1)) == (4.857, 2222, 33.3)


def test_small_runs():
    assert fm.free_entry(100, 4) == 4 and fm.cr([0.5, 0.3, 0.2], 2) == 0.8 and r(fm.hhi([0.5, 0.5]), 0) == 5000


def test_interview_and_shortfall():
    assert r(fm.hhi([0.5, 0.25, 0.25]), 0) == 3750 and r(fm.hhi([0.5, 0.25, 0.25]) - fm.hhi([0.25] * 4), 0) == 1250
    e = m.entry()
    assert r(e["w_plan"] - e["w_free"], 0) == 87 and r(100 * (0.66 - 0.085), 1) == 57.5
    assert (r(2 * 33 ** 2, 0), r(4 * 8.5 ** 2, 0)) == (2178, 289)
