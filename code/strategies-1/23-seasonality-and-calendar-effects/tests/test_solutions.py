"""Numbers gate: every numerical answer printed in Book 8, chapter 23 (text and solutions)."""
import math
import pathlib
import sys
from statistics import NormalDist

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from s1_seasonal import calendar_test, gas_profile, same_month_test, wti_months  # noqa: E402


def r(x, d=2):
    return round(float(x), d)


def test_calendar_rules():
    c = calendar_test()
    assert c["n_rules"] == 100 and {k: int((c["family"] == k).sum()) for k in ("tom", "pre", "none")} == \
        {"tom": 23, "pre": 2, "none": 75}
    got = {k: (c[k]["tom"], c[k]["pre"], c[k]["none"]) for k in ("none", "Bonferroni", "Holm", "Benjamini-Hochberg",
                                                                    "Benjamini-Yekutieli")}
    assert got == {"none": (19, 0, 8), "Bonferroni": (6, 0, 0), "Holm": (6, 0, 0), "Benjamini-Hochberg": (11, 0, 3),
                   "Benjamini-Yekutieli": (6, 0, 0)}
    assert c["Benjamini-Hochberg"]["false"] == ["weekday 1", "weekday 2", "week 3 of month"]
    n = c["names"]
    assert (r(c["t"][n.index("turn of month -1..+3")], 1), r(c["t"][n.index("pre-holiday")], 1)) == (4.4, 1.5)


def test_same_month():
    s = same_month_test()
    assert (r(s["ic"], 3), r(s["ic_t"], 1), r(100 * s["ls_month"], 2), r(s["ls_sr"], 2), s["months"]) == \
        (0.031, 3.8, 0.5, 0.72, 108)


def test_real_data():
    w, bonf, bh = wti_months()
    assert [(m, r(100 * a, 1), r(t, 2)) for m, a, t, _ in w if m in (10, 11)] == [(10, -2.8, -1.71), (11, -4.2, -2.17)]
    assert r(w[10][3], 3) == 0.03 and r(min(bonf), 2) == 0.36 and r(min(bh), 2) == 0.36
    g = gas_profile()
    assert [r(100 * v, 1) for v in g["dev"]] == [8.8, 1.0, -5.3, -4.2, -1.0, 1.0, -1.6, -1.8, -2.7, 0.8, 1.3, 7.3]
    assert (g["start"], g["end"], g["n"]) == ("2000-01", "2026-07", 319)


def test_exercises():
    z = NormalDist().inv_cdf
    assert r(100 * 0.05, 0) == 5 and r(75 * 0.05, 2) == 3.75 and r(z(1 - 0.05 / 200), 2) == 3.48
    d = 0.147 / math.sqrt(252)
    se_tom = d * math.sqrt(1 / 1440 + 1 / 6120)
    se_pre = d * math.sqrt(1 / 270 + 1 / 7290)
    assert (r(1e4 * se_tom, 2), r(8e-4 / se_tom, 2), r(1e4 * se_pre, 2), r(15e-4 / se_pre, 2)) == (2.71, 2.95, 5.74, 2.61)
    assert r(30 * (3.48 / 2.61) ** 2, 0) == 53


def test_other_seed():
    c = calendar_test(8)
    assert (c["none"]["tom"], c["none"]["pre"], c["none"]["none"]) == (8, 1, 4)
    assert all(c[k]["tom"] + c[k]["pre"] + c[k]["none"] == 0 for k in ("Bonferroni", "Holm", "Benjamini-Hochberg",
                                                                      "Benjamini-Yekutieli"))
    n = c["names"]
    assert (r(c["t"][n.index("turn of month -1..+3")]), r(c["t"][n.index("pre-holiday")])) == (2.25, 2.99)
    assert r(0.147 / math.sqrt(252) * 100, 2) == 0.93
