"""Numbers gate: every numerical answer printed in Book 9, chapter 25 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s2_crbook import Z99, by_desks, frontier, pick, pooling  # noqa: E402


def r(x, d=1):
    return round(float(x), d)


def test_pooling():
    p = pooling()
    assert (r(p["desks"], -3), r(p["pooled"], -3), r(100 * p["saving"]), r(100 * p["crossed"])) == (335000, 270000,
                                                                                                     19.5, 47.0)


def test_frontier():
    f, g = frontier(True), frontier(False)
    got = [(r(f[k]["cost"] / 1000), r(f[k]["sd"] / 1000, 0), r(g[k]["sd"] / 1000, 0))
           for k in (1.0, 0.5, 0.3, 0.2, 0.15, 0.1, 0.05)]
    assert got == [(269.7, 0, 0), (123.1, 128, 157), (78.4, 222, 268), (56.5, 304, 367), (45.3, 369, 448),
                   (33.4, 472, 579), (20.3, 684, 842)]
    assert 400 < f[0.15]["futures"] < 600
    assert r(1 - f[0.15]["sd"] / g[0.15]["sd"], 2) == 0.18


def test_pick():
    a, b = pick(), pick(5e5)
    assert (a["rate"], r(a["cost"], -2), r(a["var"], -3)) == (0.15, 45300, 859000)
    assert (b["rate"], r(b["cost"], -2), r(b["var"], -3)) == (0.35, 89300, 449000)
    assert r(100 * (1 - a["cost"] / pooling()["desks"])) == 86.5
    f = frontier(True)
    assert (r(100 * (1 - f[0.05]["cost"] / pooling()["desks"])), r(Z99 * f[0.05]["sd"], -4)) == (93.9, 1590000)
    assert r(1e6 / Z99 / 1000) == 429.9


def test_desks():
    d = by_desks()
    assert (r(100 * d[10][1]), r(100 * d[6][0]), r(100 * d[10][0])) == (48.0, 19.7, 17.1)


def test_exercises():
    assert r(1 - 1 / 5, 2) == 0.8                                                          # exercise 1
    assert r(Z99 * 369_000, -3) == 858000                                                  # exercise 2
    assert r(1e6 * (3e-4 + 0.7 * 0.02 * math.sqrt(1 / 50)), 0) == 2280                     # exercise 3
