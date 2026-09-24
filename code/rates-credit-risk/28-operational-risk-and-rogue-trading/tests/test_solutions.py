"""Numbers gate: every numerical answer printed in Book 6, chapter 28 (text and solutions)."""
import math
import pathlib
import sys
from statistics import NormalDist

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import rc_tradecontrol as m

S = m.surveillance()


def pct(x, d=1):
    return round(100 * x, d)


def test_rules():
    one, two = S["one"], S["two"]
    assert S["n"] == 2060 and S["fraud"] == 60
    hits = [pct(v["hit"], 0) for k, v in one.items() if k != "combined"]
    falses = [pct(v["false"], 2) for k, v in one.items() if k != "combined"]
    assert (min(hits), max(hits)) == (23, 52) and (min(falses), max(falses)) == (0.25, 4.4)
    assert pct(one["combined"]["hit"]) == 88.3 and pct(one["combined"]["false"]) == 7.1
    assert round(one["combined"]["false"] * 2000) == 142
    assert pct(two["combined"]["hit"]) == 61.7 and pct(two["combined"]["false"], 2) == 0.05
    assert round(two["combined"]["false"] * 2000) == 1
    assert round(one["combined"]["hit"] * 60) == 53 and round(two["combined"]["hit"] * 60) == 37


def test_audit():
    assert m.audit_demo() == {"before": True, "after_edit": False}


def test_capital():
    a, b = m.op_capital(35, 0.5), m.op_capital(35, 0.25)
    assert round(a["bic"], 2) == 5.37 and a["lc"] == 7.5 and round(a["ilm"], 3) == 1.107
    assert round(a["capital"], 2) == 5.94 and round(b["ilm"], 3) == 0.904 and round(b["capital"], 2) == 4.85
    assert round(m.bic(10), 2) == 1.47 and m.ilm(1.0, 1.0) == 1.0


def test_unwind():
    assert round(100 * m.unwind(), 1) == 13.1 and round(6.4 / 0.05) == 128
    var = 49 * 0.25 / math.sqrt(250) * NormalDist().inv_cdf(0.99)
    assert round(var, 2) == 1.80
