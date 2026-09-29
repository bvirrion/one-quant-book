"""Numbers gate: every numerical answer printed in Book 16, chapter 7 (text and solutions)."""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import fm_limits as m  # noqa: E402

la = m.la


def r(x, d=1):
    return round(float(x), d)


@pytest.mark.reference
def test_allocation_table():
    a = m.allocation()
    assert (r(a["firm_es"]), r(a["firm_mu"]), r(a["standalone"].sum())) == (212.8, 59.1, 393.9)
    assert math.isclose(a["euler"].sum(), a["firm_es"], rel_tol=1e-9)
    assert [r(x) for x in a["standalone"]] == [65.5, 69.0, 76.9, 122.8, 47.9, 11.8]
    assert [r(x) for x in a["euler"]] == [48.0, -21.5, 64.0, 108.5, 13.9, -0.1]
    assert [r(x) for x in a["incremental"]] == [42.5, -31.2, 59.6, 93.6, 10.0, -0.7]
    assert [r(100 * x) for x in a["raroc_standalone"]] == [16.7, 17.4, 10.5, 9.8, 12.6, 84.9]
    assert [r(100 * a["raroc_euler"][i]) for i in (0, 2, 3, 4)] == [22.8, 12.6, 11.1, 43.3]
    assert [r(x) for x in a["mu"]] == [10.9, 12.0, 8.0, 12.1, 6.0, 10.0]
    va = m.value_added()
    assert [r(x, 2) for x in va["standalone"]] == [1.12, 1.66, -3.5, -6.34, -1.17, 8.24]
    assert [r(x, 2) for x in va["euler"]] == [3.74, 15.24, -1.55, -4.2, 3.93, 10.02]
    assert r(100 * (1 - a["firm_es"] / a["standalone"].sum())) == 46.0


@pytest.mark.reference
def test_scales():
    w, b, af = m.scaled()
    assert [r(x, 2) for x in w] == [2.0, 2.0, 1.57, 0.57, 2.0, 2.0] and (r(b), r(af)) == (27.2, 59.0)


@pytest.mark.reference
def test_no_crash():
    old = m.P_CRASH
    m.P_CRASH = 0.0
    try:
        a = m.allocation()
    finally:
        m.P_CRASH = old
    assert (r(a["euler"][1]), r(a["euler"][3])) == (24.7, 20.3)


def test_small_runs():
    a = m.allocation(n=20_000)
    assert math.isclose(a["euler"].sum(), a["firm_es"], rel_tol=1e-9) and a["euler"][1] < 0 < a["euler"][3]
    assert a["standalone"].sum() > a["firm_es"]
    w, b, af = m.scaled(n=3_000)
    assert af >= b - 1e-9 and w[3] < w[0]


def test_limits():
    rows = {(x[0], x[1]): x for x in la.check(m.framework(), m.daily_var_exposures(), 1)}
    assert rows[("vol selling", "var")][3] == "soft" and r(100 * rows[("firm", "var")][2], 0) == 72
    assert r(m.daily_var_exposures()["vol selling"]["var"]) == 6.4
    assert r(sum(v["var"] for v in m.daily_var_exposures().values())) == 21.5
    t, v, hard = m.var_path()
    assert r(v.max()) == 7.6 and r(100 * v.max() / 8, 0) == 95 and r(100 * v.max() / 12, 0) == 63
    assert r(6 * 0.7 * 8) == 33.6 and r(0.7 * 8 * math.sqrt(6 + 30 * 0.2)) == 19.4
