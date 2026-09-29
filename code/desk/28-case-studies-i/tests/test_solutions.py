"""Numbers gate: every numerical answer printed in Book 16, chapter 28 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import fm_cases1 as m  # noqa: E402

cb = m.cb


def r(x, d=2):
    return round(float(x), d)


def test_ltcm():
    lt = m.ltcm()
    assert {k: r(100 * v, 1) for k, v in lt["returns"].items()} == {"jan_jul": -12.1, "aug": -44.0, "sep": -82.6}
    assert [r(x) for x in lt["actual"]] == [4.67, 4.11, 2.3, 0.4] and [r(x) for x in lt["half"]] == [4.67, 4.39, 3.42, 2.01]
    assert r(100 * (1 - 0.4 / 4.67), 1) == 91.4 and r(3.6 / 0.9, 1) == 4.0 and r(4.67 * 28) == 130.76
    assert r(3.81 - 3.6, 2) == 0.21


def test_amaranth():
    a = m.amaranth()
    assert (r(a["days"], 1), r(a["days_10"], 1)) == (20.0, 40.0)


def test_august():
    u = m.august()
    assert r(u["overlap"], 2) == 0.94
    assert [r(100 * u["seller"][d], 1) for d in (0, 4, 19)] == [-5.4, -13.6, -9.7]
    assert [r(100 * u["holder"][d], 1) for d in (0, 4, 19)] == [-5.3, -15.1, -7.9]


def test_small_runs():
    assert cb.capital_path([-0.5], 10.0, 0.5) == [10.0, 7.5] and cb.days_to_liquidate(100, 50, 0.5) == 4.0


def test_exercises():
    lo = cb.quant_unwind(overlap=0.5)
    assert r(lo["overlap"]) == 0.52 and (r(100 * lo["seller"][19], 1), r(100 * lo["holder"][19], 1)) == (-9.8, -4.3)
    z = cb.quant_unwind(overlap=0.0)
    assert (r(100 * z["seller"][19], 1), r(100 * z["holder"][19], 1)) == (-9.7, 0.1)
    assert r(28 * 4.67, 0) == 131 and r(100 / 28, 1) == 3.6 and r(4.11 / 4.67, 2) == 0.88
