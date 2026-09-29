import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_escalation as fe  # noqa: E402


def test_severity_and_notify():
    assert [fe.severity(x, d) for x, d in ((0.03, 1), (0.1, 1), (0.03, 4), (0.25, 1), (0.03, 6))] == [1, 2, 2, 3, 3]
    assert fe.notify(3) == ("risk committee", 2) and fe.notify(1)[0] == "head of desk"


def test_register_classifies_each_resolution():
    expo = np.array([[90, 105, 95, 90, 90, 90, 90, 90],       # position cut on day 2
                     [90, 105, 105, 90, 90, 90, 90, 90],      # limit raised on day 2
                     [90, 105, 84, 90, 90, 90, 90, 90],       # model change on day 2
                     [90, 90, 90, 90, 90, 90, 105, 105]], float)  # still open
    hard = np.full((4, 8), 100.0)
    hard[1, 2:] = 110.0
    reg = fe.register(expo, hard, {(2, 2)})
    assert [b.resolution for b in reg] == ["position cut", "limit increase", "model change", "open"]
    assert reg[1].flags == ["limit raised during breach"] and reg[2].flags == ["model changed during breach"]
    assert reg[0].days == 1 and reg[1].days == 1 and abs(reg[0].peak_excess - 0.05) < 1e-12
    st = fe.stats(reg)
    assert st["n"] == 4 and st["share"]["open"] == 0.25 and st["flagged"] == 2


def test_repeated_increases_and_hard_path():
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "limitalloc"))
    import firm_limitalloc as la
    node = la.Node("desk", (la.Limit("var", 90.0, 100.0),))
    hard = fe.hard_path(node, "var", 30, increases=((10.0, 5, 9), (10.0, 20, 25)))
    assert hard[4] == 100 and hard[5] == 110 and hard[10] == 100 and hard[20] == 110
    expo = np.full((1, 30), 90.0)
    expo[0, 4], expo[0, 19] = 105.0, 104.0
    reg = fe.register(expo, hard[None, :])
    assert [b.resolution for b in reg] == ["limit increase", "limit increase"]
    assert "repeated increases" in reg[1].flags and "repeated increases" not in reg[0].flags


def test_backdated():
    ch = [(0, 10, 10, 110.0), (1, 3, 45, 4.0)]
    assert fe.backdated(ch) == [(1, 3, 45, 4.0)]
