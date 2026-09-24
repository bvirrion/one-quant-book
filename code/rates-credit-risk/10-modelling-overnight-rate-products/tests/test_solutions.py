"""Numbers gate: every numerical answer printed in Book 6, chapter 10 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_rfr as m
from firm_rfrcaplet import gfmm_effective_variance

T = m.cap_table()
TOT = m.cap_totals()


def test_text():
    assert round(TOT["backward"]) == 288_963 and round(TOT["forward"]) == 250_741 and round(TOT["gap"]) == 38_222
    assert [round(r[3]) for r in T] == [13_623, 28_643, 33_003, 36_614, 40_944, 39_743, 42_548, 53_846]
    assert round(TOT["gap"] - TOT["first"]) == 24_599
    assert [round(T[i][5], 1) for i in (0, 1, 4, 7)] == [100.0, 25.2, 7.9, 4.8]
    cf, mc, se = m.mc_check()
    assert round(cf * 1e8) == 40_944 and abs(mc - cf) < 0.2 * se
    w = [(1.25 - x) / 0.25 for x in m.meetings_in(1.0, 1.25)]
    assert [round(x * 100) for x in w] == [69, 23]
    assert (m.FOMC[-1] - m.FOMC[-1].replace(day=29)).days == -21 and len(m.MEETINGS) == 10


def test_exercises():
    assert round(gfmm_effective_variance(1.0, 2.0, 2.25) / 2.0, 3) == 1.042
    assert round((0.25 / 3) / (0.25 + 0.25 / 3) * 100) == 25


def test_problem():
    assert round(T[4][3]) == 40_944
    ext = (0.25 / 3) / 1.0
    assert round(ext * 100, 1) == 8.3
