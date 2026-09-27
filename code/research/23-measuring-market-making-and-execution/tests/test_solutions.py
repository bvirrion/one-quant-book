"""Numbers gate: every numerical answer printed in Book 7, chapter 23 (text and solutions)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from rs_markout import SEEDS, annual, curves, decomposition, execution, session, settle, tca_all


def r(x, d=2):
    return round(float(x), d)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_market_maker():
    for pull, exp in ((False, (8144, 18000, 45, 42, 0.43, -0.67, 0.19, -0.85)),
                      (True, (3309, 16391, 20, 40, 0.52, -0.53, 0.44, -0.81))):
        c = curves(pull)
        tot, lots, posted = decomposition(pull, 20.0)
        got = (lots, posted, r(100 * lots / posted, 0), r(100 * c["share_informed"], 0), r(c["all"][0][0]),
               r(c["all"][0][8]), r(c["all_micro"][0][0]), r(tot["total"] / lots))
        assert got == exp
        assert settle(pull) == 20.0
    c = curves(False)
    assert (r(c["informed"][0][8]), r(c["informed"][0][-1]), r(c["uninformed"][0][8]), r(c["uninformed"][0][-1])) == \
        (-1.85, -2.71, 0.18, 0.52)
    a, _, _ = decomposition(False, 20.0)
    b, _, _ = decomposition(True, 20.0)
    assert [r(a[k], 0) for k in ("spread", "adverse", "inventory", "fees", "total")] == [3519, -8977, -1060, -407, -6925]
    assert [r(b[k], 0) for k in ("spread", "adverse", "inventory", "fees", "total")] == [1734, -3483, -771, -165, -2685]
    y = annual(a)
    assert [r(y[k] / 1000, 0) for k in ("spread", "adverse", "inventory", "fees", "total")] == [480, -1225, -145, -56, -945]
    assert (r(100 * (1 - b["total"] / a["total"]), 0), r(100 * (1 - 3309 / 8144), 0)) == (61, 59)
    assert r(-8977 / 8144 / 100 * 100) == -1.10 and r(0.43 - 1.10) == -0.67
    assert (r(6.5 * 252), r(6.5 * 252 / 12, 1)) == (1638, 136.5) and r(-a["adverse"] / a["spread"]) == 2.55
    per = a["total"] / 8144
    assert (r(a["total"] - b["total"], 0), r(3309 * per, 0), r(a["total"] - 3309 * per, 0), r(3309 * per - b["total"], 0)) == \
        (-4240, -2814, -4111, -129)
    assert r(100 * (a["total"] - 3309 * per) / (a["total"] - b["total"]), 0) == 97


def test_exercises_by_hand():
    assert (r(100 * (100.00 - 99.99)), r(100 * (99.97 - 100.00)), r(100 * (100.02 - 99.97)), r(100 * (100.02 - 99.99))) == \
        (1.0, -3.0, 5.0, 3.0)
    assert (r(80 * 0.20), r(80 * (50.40 - 50.20)), r(20 * 1.0), r(80 * 0.01), r(16 + 16 + 20 + 0.8)) == (16.0, 16.0, 20.0, 0.8, 52.8)
    assert (r(100 * 1.0), r(80 * (51 - 50.40) - 0.8)) == (100.0, 47.2) and r(8144 / 18000 * 100, 0) == 45


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_tca():
    rows, m, se = tca_all()
    got = {k: (r(m[k]), r(se[k])) for k in ("delay", "execution", "opportunity", "total", "drift", "paid", "vwap", "impact",
                                            "move", "move_without", "delay_without")}
    assert got == {"delay": (2.83, 0.94), "execution": (-4.68, 2.09), "opportunity": (-0.2, 0.2), "total": (-2.0, 2.73),
                   "drift": (-4.78, 2.07), "paid": (0.1, 0.03), "vwap": (0.4, 0.61), "impact": (0.25, 0.24),
                   "move": (-9.71, 5.48), "move_without": (-9.96, 5.44), "delay_without": (2.92, 1.02)}
    assert (r(100 * m["passive"], 0), r(m["lots"], 0), r(m["fees"])) == (43, 289, 0.05)
    e = execution(61)
    q = e["sf"]["filled"]
    assert (q, r(e["sf"]["delay"] / q), r(e["sf"]["execution"] / q), r(e["sf"]["opportunity"] / q), r(e["sf"]["total"] / q),
            r(e["vwap"])) == (28700, 0.0, -7.83, -0.91, -8.69, -1.1)
    assert r(-7.83 - 0.91 + 0.05, 2) == -8.69


def test_small_runs():
    # One live session instead of twelve per arm: the market maker is filled, some fills meet informed orders, and
    # every fill has a reference mid just before it.
    s = session(SEEDS[0], False)
    assert len(s["t"]) > 0 and 0 < s["informed"].mean() < 1 and (s["mid_before"] > 0).all()
