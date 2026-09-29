"""Numbers gate: every numerical answer printed in Book 17, chapter 10 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import in_crypto as c  # noqa: E402

tc = c.tc


def r(x, d=1):
    return round(float(x), d)


def test_headcount():
    ch = {x["year"]: x for x in c.changes()}
    assert [r(100 * ch[y]["revenue"]) for y in (2022, 2023, 2024, 2025)] == [-59.3, -2.7, 111.2, 9.4]
    assert [r(100 * ch[y]["employees"]) for y in (2023, 2024, 2025)] == [-24.3, 10.4, 31.3]


def test_small_runs():
    s = tc.summary(tc.simulate(c.GRANT, 0.8, 0.0, 2000, np.random.default_rng(3)))
    assert s["median"] < s["cash"] < s["p90"] and 0.5 < s["p_any_tax_exceeds"] < 1


@pytest.mark.reference
def test_grant_printed():
    s = c.grant()
    assert [round(s[k]) for k in ("median", "p10", "p90", "mean")] == [106193, 17467, 537810, 235062]
    assert s["cash"] == 240000 and r(100 * s["p_below_cash"]) == 74.3 and r(100 * s["p_any_tax_exceeds"]) == 76.2
    s4 = c.grant(0.4)
    assert round(s4["median"]) == 194318 and r(100 * s4["p_any_tax_exceeds"]) == 2.4
    g = tc.Grant(400_000.0, 48, 12, 12, 0.4)
    s12 = tc.summary(tc.simulate(g, 0.8, 0.0, 20_000, np.random.default_rng(10)))
    assert round(s12["median"]) == 76275 and r(100 * s12["p_any_tax_exceeds"]) == 86.8


def test_arithmetic():
    assert (10_000 * 0.5 - 0.4 * 10_000) == 1000 and 60_000 - 17_150 == 42_850
    assert r(math.exp(-0.32), 3) == 0.726 and round(400_000 / 48) == 8333


def test_per_head():
    ph = c.per_head()
    assert {y: round(v, 2) for y, v in ph.items()} == {2022: 0.71, 2023: 0.91, 2024: 1.74, 2025: 1.45}
    assert round(ph[2024] / ph[2022], 1) == 2.5
