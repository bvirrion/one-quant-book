"""Numbers gate: every numerical answer printed in Book 11, chapter 24 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import hf_crypto as h  # noqa: E402


def r(x, d=0):
    return round(float(x), d)


def test_week():
    b = h.base()
    assert [r(b[k]) for k in ("spread", "adverse", "hedge", "fees", "funding", "cascade", "total")] == [
        574912, 0, -464310, 143728, 274, 20842, 275445]
    assert r(100 * b["uptime"]) == 90


def test_budget_and_absorption():
    g = h.budget()
    assert [r(g[x]["total"], -2) for x in (1.0, 0.5, 0.25, 0.1)] == [275400, 270800, 173000, -265900]
    assert [r(g[x]["adverse"], -2) for x in (0.5, 0.25, 0.1)] == [-6400, -134600, -675200]
    assert r(g[1.0]["total"] - g[0.25]["total"], -2) == 102400 and r(g[0.2]["total"], -3) == 101000
    a = h.absorption()
    assert [r(a[k]["cascade"], -2) for k in ("pull", 0.0, 40.0, 60.0)] == [600, 5200, 20800, 17800]
    assert r(h.early_small()["cascade"], -2) == -600
    gb = h.governor_budget()
    assert (round(gb[1], 2), round(gb[5], 2)) == (1.16, 0.23) and round(gb[1] * 2, 2) == 2.31
