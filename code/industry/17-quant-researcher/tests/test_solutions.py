"""Numbers gate: every numerical answer printed in Book 17, chapter 17 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import in_researcher as a  # noqa: E402

fr = a.fr


def r(x, d=2):
    return round(float(x), d)


def test_named_and_curve():
    n = a.named()
    assert [r(n[h][1]) for h in ("day", "week", "month")] == [0.97, 3.88, 15.53]
    assert [round(n[h][2]) for h in ("day", "week", "month")] == [244, 202, 186]
    c = {h: (sr, y, p) for h, _, sr, y, p in a.law_curve()}
    assert all(round(v[2]) == 194 for v in c.values())
    assert r(c["minute"][1] * 365.25, 1) == 0.7 and round(c["hour"][1] * 365.25) == 43
    assert [r(c[h][1]) for h in ("day", "week")] == [0.77, 3.73] and r(c["month"][1], 1) == 16.2
    assert r(c["quarter"][1], 1) == 48.5 and round(3.84 / 4, 2) == 0.96


def test_pay():
    p = a.pay()
    want = {"systematic fund": (220_000, 120, 5), "multi-manager platform": (190_000, 45, 3),
            "market maker": (175_000, 131, 9), "bank": (158_100, 825, 9), "exchange": (107_100, 35, 4)}
    assert {k: (p["all"][k]["p50"], p["all"][k]["n"], p["all"][k]["employers"]) for k in want} == want
    assert [p[lv]["bank"]["p50"] for lv in ("I", "II", "III", "IV")] == [88_300, 145_300, 179_335, 200_000]
    assert [p[lv]["market maker"]["p50"] for lv in ("I", "II", "III", "IV")] == [150_000, 200_000, 150_000, 225_000]
    t = a.titles()
    assert (t["13-2099.01"], t["15-2041"], t["15-2031"]) == (1018, 156, 52)


def test_exercises():
    assert r(fr.years_to_significance(1.5, 252)) == 1.72 and r(3.84 / 2.25) == 1.71
    assert r(fr.fundamental_law_sr(0.02, 50, 52)) == 1.02
    assert 220_000 - 158_100 == 61_900 and r(100 * (220_000 / 158_100 - 1), 1) == 39.2
    s = 0.8 / math.sqrt(12)
    assert r(0.8 * math.sqrt(3) / math.sqrt(1 + s * s / 2)) == 1.37 and r(fr.years_to_significance(0.8, 12), 1) == 6.2
    assert r(fr.years_to_significance(1.0, 52) * 1.2 / 0.8) == 5.82
    assert r(fr.years_to_significance(1.2, 12)) == 2.83 and round(fr.years_to_significance(0.6, 12)) == 11
    assert r(0.1 * math.sqrt(252)) == 1.59 and r(math.sqrt(1.005 / 400), 2) == 0.05
    assert r(math.sqrt(1.005 / 400) * math.sqrt(252), 1) == 0.8


def test_small_runs():
    assert fr.card("quant researcher").chapter == 17
    assert fr.periods_to_significance(1.0, 12) > fr.periods_to_significance(2.0, 12)
