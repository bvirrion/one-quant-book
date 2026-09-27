"""Numbers gate: every numerical answer printed in Book 10, chapter 9 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from mx_dark import START, compare, run, zhu  # noqa: E402


def r(x, d=1):
    return round(float(x), d)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_strategies():
    c = compare()
    got = {s: (r(v["shortfall"][0]), r(v["shortfall"][1]), r(v["drift"][0]), r(v["drift"][1])) for s, v in c.items()}
    assert got == {"lit": (3.8, 1.4, 7.3, 2.3), "dark": (12.5, 0.5, 26.1, 2.2), "dark_min": (9.5, 1.6, 11.9, 1.6),
                   "block": (-2.9, 1.9, -1.7, 2.2)}
    assert (r(c["lit"]["own_impact"][0], 2), r(c["dark"]["leakage"][0]), r(c["dark"]["leakage"][1])) == (4.95, 10.9, 0.3)
    assert (r(c["dark"]["front_run"][0], -2), r(c["dark"]["fund_pings"][0], 0)) == (44000.0, 88.0)
    assert r(c["dark"]["done"][0] - START, -1) == 360.0
    assert (r(100 * c["dark_min"]["dark_share"][0], 0), r(c["dark_min"]["own_impact"][0])) == (46.0, 1.4)
    assert (r(100 * c["block"]["dark_share"][0], 0), r(c["block"]["leakage"][0]), r(c["block"]["leaks"][0], 2)) == \
        (79.0, 0.6, 0.75)
    assert r(c["block"]["done"][0] - START, -1) == 1240.0


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_zhu():
    z = zhu()
    assert (r(100 * z["fill_informed"]), r(100 * z["fill_uninformed"])) == (6.3, 17.5)
    assert (r(z["capture_lit"], 2), r(z["move_lit"], 2), r(z["capture_dark"], 2), r(z["move_dark"], 2)) == \
        (0.51, -0.13, 0.0, 0.11)


# Full-size run behind the book's printed numbers: make test-code / make reproduce; CI runs test_small_runs.
@pytest.mark.reference
def test_exercises():
    # 1: a midpoint cross between 20.00 and 20.02 saves a cent a share on each side
    assert (r(20.01 - 20.00, 2), r(10_000 * 0.01, 0)) == (0.01, 100.0)
    # 3: firm-up rate
    assert 28 / 40 == 0.7
    # 4: 500 shares bought ahead once 5,000 of 20,000 are filled, lambda 0.0005 tick a share, price 100.00
    lam, left = 0.0005, 15_000
    assert (r(lam * 500, 2), r(lam * 500 * left / 20_000, 4)) == (0.25, 0.1875)
    # 6: own impact of 100 equal children
    assert r(lam * 20_000 / 2 * (1 - 1 / 100), 2) == 4.95
    # 7: a minimum quantity of 200
    rs = [run(seed, "dark_min", fund_min=200) for seed in range(1, 17)]
    sf = np.array([x["shortfall"] for x in rs])
    assert (r(sf.mean()), r(sf.std(ddof=1) / 4), r(np.mean([x["leakage"] for x in rs]))) == (7.0, 0.9, 0.0)
    assert r(np.mean([x["done"] for x in rs]) - START, -1) == 1020.0
    assert r(np.mean([x["drift"] for x in rs])) == 13.6


def test_small_runs():
    # One seed instead of sixteen: the lit-only order trades nothing in the dark, the three dark strategies do, and
    # every strategy's shortfall is measured.
    c = compare(seeds=(1,))
    assert set(c) == {"lit", "dark", "dark_min", "block"} and c["lit"]["dark_share"][0] == 0
    assert all(c[s]["dark_share"][0] > 0 for s in ("dark", "dark_min", "block"))
    assert all(math.isfinite(v["shortfall"][0]) for v in c.values())
