"""Numbers gate: every numerical answer printed in Book 17, chapter 18 (text and solutions)."""
import itertools
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import in_bankquant as a  # noqa: E402

fr, mv = a.fr, a.mv


def r(x, d=1):
    return round(float(x), d)


def test_pay():
    c = a.lca()
    qr = [c[(2025, "quant researcher", lv)]["p50"] for lv in a.LEVELS]
    assert qr == [88_300, 145_300, 179_335, 200_000]
    assert [c[(2021, "quant researcher", lv)]["p50"] for lv in a.LEVELS] == [94_500, 125_000, 150_000, 160_430]
    q21, q25 = c[(2021, "quant researcher", "all")], c[(2025, "quant researcher", "all")]
    assert (q21["p50"], q21["n"], q25["p50"], q25["n"], q25["employers"]) == (128_300, 895, 158_100, 825, 9)
    rk = c[(2025, "risk", "all")]
    assert (rk["p50"], rk["n"], rk["employers"]) == (136_776, 380, 5)
    assert [c[(2025, "risk", lv)]["p50"] for lv in a.LEVELS] == [74_800, 115_700, 155_000, 170_373]
    assert c[(2021, "risk", "I")]["suppressed"]
    o = a.oews()
    b, s = o[("5220A1", "13-2054")], o[("523000", "13-2054")]
    assert [int(b[k]) for k in ("employment", "p10", "p50", "p90")] == [17_810, 62_620, 108_170, 187_490]
    assert [int(s[k]) for k in ("employment", "p10", "p50", "p90")] == [9_840, 83_230, 133_070, 219_990]
    nominal, real = a.growth()
    assert (r(100 * (nominal - 1)), r(100 * (real - 1))) == (23.2, 3.7) and round(135.8312 / 114.325, 3) == 1.188


def test_inventory_and_headcount():
    assert all(mv.ModelRecord("m", "m", "o", "u", *s).tier == (1 if 2 * s[0] + s[1] + s[2] >= 10 else
                                                              2 if 2 * s[0] + s[1] + s[2] >= 7 else 3)
               for s in itertools.product((1, 2, 3), repeat=3))
    assert a.intervals() == {1: 1, 2: 2, 3: 3}
    inv = a.inventory()
    assert inv == {1: 102, 2: 403, 3: 495}
    h = a.by_tier(inv)
    assert [round(h[t]) for t in (1, 2, 3)] == [44_880, 41_912, 15_510] and round(sum(h.values())) == 102_302
    tot = sum(h.values())
    assert [r(100 * h[t] / tot) for t in (1, 2, 3)] == [43.9, 41.0, 15.2]
    assert r(a.headcount(inv)) == 63.9
    cv = dict(a.curve())
    assert (r(cv[0.05]), r(cv[0.40])) == (50.7, 140.1)
    slope = (cv[0.40] - cv[0.05]) / 35
    assert r(slope) == 2.6
    one = fr.validation_hours({1: 1}, a.FULL, a.REVIEW, a.intervals(), a.CHANGE)
    three = fr.validation_hours({3: 1}, a.FULL, a.REVIEW, a.intervals(), a.CHANGE)
    assert (round(one), r(three), round(one - three), r((one - three) / 1600, 2)) == (440, 31.3, 409, 0.26)


def test_exercises():
    inv = a.inventory()
    assert r(a.headcount(inv, interval={1: 1, 2: 1, 3: 3})) == 82.1
    assert r(a.headcount(inv, interval={1: 1, 2: 1, 3: 3}) - a.headcount(inv)) == 18.1
    assert 160 / 2 + 16 * 0.5 + 16 == 104 and 160 + 16 == 176
    ch = a.CHANGE * sum(inv[t] * a.FULL[t] for t in inv)
    assert (round(ch), round(2 * ch)) == (13_498, 26_996) and r(a.headcount(inv, change=0.2)) == 72.4
    assert [g for _, _, g in a.org_cases()] == ["a", "b", "c", "fail"]
    boss = dict(a.BOSS, **{"validation team": "head of quantitative analytics"})
    assert fr.independence(boss, a.SENIOR, "validation team", "library developer",
                           "head of quantitative analytics") == "fail"
    assert r(100 * mv.binomial_tail(250, 7, 0.01)) == 1.4 and 250 * 0.01 == 2.5


@pytest.mark.reference
def test_sampled():
    hs = a.sampled_headcount()
    assert r(hs.mean()) == 64.0 and [r(x) for x in np.percentile(hs, [5, 95])] == [60.1, 67.9]


def test_small_runs():
    hs = a.sampled_headcount(draws=20)
    assert 55 < hs.mean() < 73
    assert fr.card("model validator").chapter == 18
