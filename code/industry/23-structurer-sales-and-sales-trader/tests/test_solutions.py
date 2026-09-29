"""Numbers gate: every numerical answer printed in Book 17, chapter 23 (text and solutions)."""
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import in_structurer as a  # noqa: E402

fr = a.fr


def r(x, d=2):
    return round(float(x), d)


@pytest.mark.reference
def test_margins():
    m = a.margins()
    order = ((0.01, 0.2), (0.04, 0.2), (0.01, 0.3), (0.04, 0.3))
    assert [r(m[k]["margin"]) for k in order] == [-1.65, 1.83, 6.91, 9.13]
    assert [r(m[k]["fair_coupon"]) for k in order] == [4.23, 5.91, 8.79, 10.22]
    assert [r(m[k]["zero_margin_coupon"]) for k in order] == [5.20, 6.97, 9.92, 11.41]
    assert [r(100 * m[k]["called_first"], 1) for k in order] == [44.0, 50.0, 42.7, 46.7]
    assert [r(100 * m[k]["ki"], 1) for k in order] == [15.8, 9.4, 25.1, 19.3]
    assert r(m[(0.04, 0.2)]["margin"] - m[(0.01, 0.2)]["margin"]) == 3.48
    ms = [100 - fr.note_value(a.sheet(6.0), 0.04, a.Q, 0.20, n=50_000, seed=s, steps=a.STEPS)[0] for s in range(1, 21)]
    assert (r(np.mean(ms)), r(np.std(ms, ddof=1)), r(min(ms)), r(max(ms))) == (1.84, 0.06, 1.74, 1.97)


def test_market_and_pay():
    sh = a.eusipa_shares()
    assert sum(a.EUSIPA_OUTSTANDING.values()) == a.EUSIPA_TOTAL == 486_635
    assert (r(100 * sh["Switzerland"], 1), r(100 * sh["Germany"], 1)) == (58.8, 20.5)
    assert r(100 * (sh["Switzerland"] + sh["Germany"]), 1) == 79.4
    assert a.revenue_per_structurer() == (2e6, 10e6)
    s = a.survey()
    assert [int(s["523000"][k]) for k in ("employment", "p10", "p50", "p90")] == [173_040, 55_130, 103_030, 309_440]
    assert (int(s["5220A1"]["employment"]), int(s["5220A1"]["p50"])) == (257_110, 61_440)


def test_small_runs():
    m = fr.structuring_margin(a.sheet, 6.0, 2.0, 0.04, a.Q, 0.2, n=2000, seed=1, steps=4)
    assert 0 < m["fair_coupon"] < m["zero_margin_coupon"] < 20
    assert fr.card("sales-trader").chapter == 23
