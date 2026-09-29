"""Numbers gate: every numerical answer printed in Book 17, chapter 22 (text and solutions)."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import in_pm as a  # noqa: E402

fr = a.fr


def r(x, d=2):
    return round(float(x), d)


@pytest.mark.reference
def test_curve_and_crossing():
    rows = {x["sr"]: x for x in a.curve()}
    assert [r(rows[s]["mean"] / 1e6) for s in (0.0, 0.5, 1.0, 2.0)] == [3.18, 6.04, 10.48, 23.36]
    assert r(rows[0.0]["p50"] / 1e6) == 1.50
    assert [r(100 * rows[s]["stopped"], 1) for s in (0.0, 0.5, 1.0, 2.0)] == [57.3, 32.5, 15.2, 1.9]
    assert r(100 * (1 - rows[0.0]["stopped"])) >= 42.5 and round(100 * (1 - rows[0.0]["stopped"])) == 43
    x, p = a.crossing(list(rows.values()))
    assert r(x) == 0.26 and round(100 * p) == 43
    xc, pc = a.crossing(list(rows.values()), "ce")
    assert r(xc) == 0.75 and round(100 * pc) == 23
    assert r(10.48 - 3.18) == 7.30 and r(57.3 - 15.2, 1) == 42.1 and r(3.18 / 4.5, 1) == 0.7
    s0, s1 = a.run(0.0, stop=0.10), a.run(1.0, stop=0.10)
    assert (r(s0["pay"].mean() / 1e6), r(100 * s0["stopped"].mean(), 1)) == (3.56, 26.8)
    assert (r(s1["pay"].mean() / 1e6), r(100 * s1["stopped"].mean(), 1)) == (10.76, 2.1)


def test_arithmetic_and_evidence():
    assert r(fr.years_to_significance(1.0, 252)) == 3.85 and r(math.sqrt(3)) == 1.73
    s = 2 / math.sqrt(252)
    assert r(2 * math.sqrt(3)) == 3.46 and r(s * math.sqrt(756) / math.sqrt(1 + s * s / 2)) == 3.45
    assert r(1.2 * math.sqrt(3)) == 2.08 and r(0.15 * 30 / math.sqrt(2 * math.pi)) == 1.80
    assert max(0.5, 0.15 * (40 - 10)) == 4.5 and 0.06 * 50e6 == 3e6
    sv = a.survey()
    fm, an = sv[("523000", "11-3031")], sv[("523000", "13-2051")]
    assert [int(fm[k]) for k in ("employment", "p10", "p50", "p90")] == [70_400, 128_260, 223_860, 383_590]
    assert [int(an[k]) for k in ("employment", "p50", "p90")] == [89_390, 124_370, 250_000]
    assert (int(sv[("525900", "11-3031")]["p50"]), int(sv[("525900", "13-2051")]["p50"])) == (215_690, 125_710)
    pm = a.pm_filings()
    assert sum(n for (fy, _), (n, _, _) in pm.items() if fy == 2025) == 14
    assert all(sup for (fy, _), (_, _, sup) in pm.items() if fy == 2025)


def test_small_runs():
    d = a.run(1.0, n=300)
    assert d["pay"].min() > 0 and 0 <= d["stopped"].mean() < 0.5
    assert fr.card("sub-portfolio manager").chapter == 22
