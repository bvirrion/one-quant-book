"""Numbers gate: every numerical answer printed in Book 17, chapter 28 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import in_career as a  # noqa: E402

fc = a.fc


def r(x, d=1):
    return round(float(x), d)


def test_move():
    assert fc.unvested(a.JOB) == 280_000
    feb, mar = fc.forfeited(a.JOB, 2), fc.forfeited(a.JOB, 3)
    assert (round(feb["total"]), round(mar["total"]), round(mar["accrued"]), round(feb["accrued"])) == (
        659_167, 338_333, 58_333, 29_167)
    c = a.by_month()
    assert (round(c[1]["net"]), round(c[2]["net"]), c[1]["lost_award"]) == (694_167, 548_333, 350_000)
    s = a.surface()
    assert (r(100 * s[(2, 0.5)]), r(100 * s[(3, 0.5)]), r(100 * s[(2, 0.0)]), r(100 * s[(2, 1.0)])) == (
        38.6, 30.5, 56.1, 21.1)
    assert (r(100 * s[(12, 0.0)]), r(100 * s[(12, 1.0)]), r(100 * s[(12, 0.5)])) == (52.8, 37.3, 45.0)
    assert r(100 * min(s[(m, 0.5)] for m in a.MONTHS)) == 30.5 and r(100 * s[(3, 0.0)]) == 38.2
    feb_q1 = fc.move_cost(a.JOB, 2, q=1.0, **a.MOVE)
    assert (round(feb_q1["net"]), round(feb_q1["buyout"])) == (379_167, 630_000)
    unpaid = dict(a.MOVE, paid_noncompete=False)
    assert round(fc.move_cost(a.JOB, 2, q=0.5, **unpaid)["net"]) == 819_167
    assert r(100 * fc.breakeven_raise(a.JOB, 2, 3, q=0.5, **unpaid)) == 45.5
    assert round(a.employer_view(), 2) == 0.74 and a.spinouts() == []


def test_career():
    c = a.career()
    assert (r(100 * c["pm_by_10"]), r(100 * c["left_by_10"])) == (21.5, 36.7)
    p50, p90 = list(c["p50"]), list(c["p90"])
    assert p50.index(700_000) == 7 and p50[-1] == 200_000 and p90.index(1_500_000) == 6


def test_small_runs():
    assert fc.breakeven_raise(a.JOB, 3, 3, notice_m=0) > 0
