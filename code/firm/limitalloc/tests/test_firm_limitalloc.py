import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_limitalloc as la  # noqa: E402


def _tree(temp=()):
    a = la.Node("a", (la.Limit("var", 8, 10),), temp=temp)
    b = la.Node("b", (la.Limit("var", 8, 10),))
    return la.Node("desk", (la.Limit("var", 15, 18),), (a, b))


def test_check_statuses_and_temporary_increase():
    t = _tree()
    rows = {(n, m): (u, s) for n, m, u, s in la.check(t, {"a": {"var": 9.0}, "b": {"var": 11.0}}, day=1)}
    assert rows[("a", "var")][1] == "soft" and rows[("b", "var")][1] == "hard"
    assert rows[("desk", "var")][1] == "hard" and math.isclose(rows[("desk", "var")][0], 20 / 18)
    t2 = _tree(temp=(("var", 5.0, 10),))
    assert la.check(t2, {"a": {"var": 12.0}, "b": {"var": 1.0}}, day=5)[1][3] == "soft"
    assert la.check(t2, {"a": {"var": 12.0}, "b": {"var": 1.0}}, day=11)[1][3] == "hard"


def test_euler_adds_up_and_incremental():
    rng = np.random.default_rng(2)
    s = rng.standard_normal((50_000, 3)) @ np.array([[1, 0.5, 0], [0, 1, 0], [0, 0, 1]])
    a = la.allocate_capital(s, 0.99)
    assert math.isclose(a["euler"].sum(), a["firm"], rel_tol=1e-9)
    assert a["standalone"].sum() > a["firm"]
    assert (a["incremental"] <= a["standalone"] + 1e-9).all()


def test_best_scales_prefers_high_return_low_tail():
    rng = np.random.default_rng(3)
    good = rng.normal(1.0, 1.0, 20_000)
    bad = rng.normal(0.1, 1.0, 20_000)
    w = la.best_scales(np.c_[good, bad], 0.99, 0.2)
    assert w[0] > w[1]


def test_to_riskctl():
    n = la.Node("firm", (), (la.Node("s1", (la.Limit("loss", 1, 2), la.Limit("position", 5, 6))),))
    assert la.to_riskctl(n) == {"s1": {"loss": 2, "position": 6}}
