"""Numbers gate: every numerical answer printed in Book 7, chapter 28 (text and solutions)."""
import math
import pathlib
import sys

import pandas as pd
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from rs_capacity import FRACTIONS, OVERLAPS, curve, summary, unwind

DATA = pathlib.Path(__file__).resolve().parents[4] / "data" / "research" / "ff_aug2007.csv"


def r(x, d=2):
    return round(float(x), d)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_capacity():
    fx, op = curve("fixed"), curve("optimised")
    assert [r(x) for x in fx["sr"]] == [1.79, 1.74, 1.64, 1.48, 1.18, 0.9, 0.68, 0.34, -0.28, -1.85]
    assert [r(x) for x in op["sr"]] == [1.68, 1.76, 2.03, 2.34, 2.43, 2.31, 2.18, 1.96, 1.66, 1.36]
    s = summary()
    assert (r(s["fixed_half"] / 1e9), s["fixed_max"], r(fx["profit"].max() / 1e6, 0)) == (2.02, 3e9, 146)
    assert (s["opt_max"], s["opt_half"], r(op["profit"][-1] / 1e6, 0), r(op["profit"][4] / 1e6, 0)) == (3e10, None, 806, 125)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_unwind():
    grid = [[r(100 * unwind(t, f)["peak"]) for t in OVERLAPS] for f in FRACTIONS]
    assert grid == [[-0.03, -0.18, -0.42, -0.97], [-0.05, -0.28, -0.66, -1.54], [-0.08, -0.4, -0.93, -2.17],
                    [-0.11, -0.56, -1.32, -3.07]]
    assert [r(unwind(t, 1.0)["overlap"]) for t in OVERLAPS] == [0.04, 0.18, 0.43, 1.0]
    assert {unwind(t, f)["day"] for t in OVERLAPS for f in FRACTIONS} == {3}
    assert [r(100 * unwind(1.0, f)["end"]) for f in FRACTIONS] == [-0.41, -0.65, -0.92, -1.3]
    assert r(100 * unwind(1.0, 1.0)["seller"]) == -2.0
    assert r(unwind(1.0, 0.25)["peak"] / unwind(1.0, 1.0)["peak"]) == 0.5 == r(math.sqrt(0.25))


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_august_2007():
    d = pd.read_csv(DATA).set_index("factor")
    got = {f: (r(100 * d.loc[f, "cum_6_9"]), r(d.loc[f, "cum_6_9_sd"], 1), r(100 * d.loc[f, "aug10"]), r(d.loc[f, "aug10_sd"], 1))
           for f in d.index}
    assert got == {"Mkt-RF": (1.39, 2.0, 0.04, 0.1), "SMB": (2.04, 5.0, -0.03, -0.1), "HML": (-2.28, -10.6, 1.42, 6.6),
                   "Mom": (-3.43, -12.5, 1.15, 4.2)}


def test_exercises():
    g, k = 0.10, 0.10 / math.sqrt(1e10)
    assert r((2 * g / (3 * k)) ** 2 / 1e9, 2) == 4.44 and r(g / 3, 3) == 0.033
    assert r(0.7 * 0.02 * math.sqrt(2e9 * 0.02 / 3 / 2e8) * 100, 2) == 0.36 and r(2e9 * 0.02 / 3 / 1e6, 1) == 13.3
    assert (r(1.30 / 3.07), r(0.41 / 0.97), r(0.34 / 1.79, 2)) == (0.42, 0.42, 0.19)


def test_small_runs():
    # The crowding model alone (no capacity curves): funds that rank on a more common score hold more of the same
    # names, and a forced sale pushes prices down.
    lo, hi = unwind(0.2, 0.3), unwind(0.8, 0.3)
    assert 0 < lo["overlap"] < hi["overlap"] < 1 and hi["peak"] < 0 and hi["seller"] < 0
