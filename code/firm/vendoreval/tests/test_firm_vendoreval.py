import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_vendoreval import (
    backfill_share,
    breakeven,
    coverage,
    cusum_break,
    fit_by_group,
    incremental_ic,
    long_short,
    rank_ic,
    residualise,
    tone,
)


def test_coverage_backfill_fit():
    assert coverage([1, 1, 2, 3, 3, 3]) == {1: 2, 2: 1, 3: 3}
    assert backfill_share([10, 20, 30, 40], [15, 90, 35, 100], 30) == 0.5
    x = np.arange(10.0)
    f = fit_by_group(x, np.r_[2 * x[:5] + 1, -x[5:]], np.r_[[0] * 5, [1] * 5])
    assert np.allclose(f[0], (2.0, 1.0, 1.0)) and np.allclose(f[1], (-1.0, 0.0, -1.0))


def test_cusum_finds_shift():
    rng = np.random.default_rng(1)
    e = np.r_[rng.normal(0, 1, 300), rng.normal(0.8, 1, 200)]
    k, stat = cusum_break(e)
    assert 280 <= k <= 320 and stat > 3
    assert cusum_break(rng.normal(0, 1, 500))[1] < 1.36 * 1.5


def test_ic_and_incremental():
    rng = np.random.default_rng(2)
    n, g = 4000, np.repeat(np.arange(20), 200)
    s = rng.standard_normal(n)
    old = s + rng.standard_normal(n)                 # a signal already owned
    new = s + rng.standard_normal(n)                 # the vendor's, same information plus independent noise
    y = s + 3 * rng.standard_normal(n)
    assert math.isclose(rank_ic(y, y), 1.0) and math.isclose(rank_ic([1.0, np.nan, 3.0, 2.0], [1.0, 5.0, 3.0, 2.0]), 1.0)
    r = residualise(new, old, g)
    assert abs(np.corrcoef(r, old)[0, 1]) < 0.01
    full = rank_ic(new, y)
    inc, t, k = incremental_ic(new, old, y, g)
    assert k == 20 and 0.0 < inc < full and t > 2
    assert np.allclose(residualise(old, old, g), 0.0)          # nothing new in a copy
    assert long_short(np.arange(10.0), np.arange(10.0), np.zeros(10), 0.2) == 8.0


def test_breakeven_and_tone():
    assert math.isclose(breakeven(0.02, 1e8, 0.0, np.inf, 3), 2e6)
    assert breakeven(0.02, 1e8, 0.005, 2.0, 3) < breakeven(0.02, 1e8, 0.0, 2.0, 3) < 2e6
    counts = np.array([[2, 1, 1], [0, 0, 4]])
    assert np.allclose(tone(counts, ["loss", "gain", "the"], {"loss"}), [0.5, 0.0])
