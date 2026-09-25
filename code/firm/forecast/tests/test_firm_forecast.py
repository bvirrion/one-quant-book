import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_forecast import (
    binned,
    ding_martin_ir,
    effective_breadth,
    information_ratio,
    isotonic,
    law_ir,
    mincer_zarnowitz,
    qian_hua_ir,
    scale_rule,
    transfer_coefficient,
)


def test_scale_and_bins():
    assert np.allclose(scale_rule([1.0, -2.0], 0.05, [0.10, 0.20]), [0.005, -0.02])
    s = np.arange(100.0)
    k, ms, mr = binned(s, 2 * s, 4)
    assert list(k) == [0, 1, 2, 3] and np.allclose(mr, 2 * ms)


def test_isotonic():
    y = np.array([1.0, 3.0, 2.0, 4.0, 3.0, 5.0])
    f = isotonic(np.arange(6), y)
    assert np.allclose(f, [1.0, 2.5, 2.5, 3.5, 3.5, 5.0])
    assert np.allclose(isotonic([3, 1, 2], [5.0, 1.0, 0.0]), [5.0, 0.5, 0.5])        # unsorted x
    rng = np.random.default_rng(0)
    x = rng.uniform(0, 1, 2000)
    g = isotonic(x, x + rng.normal(0, 0.3, 2000))
    assert np.all(np.diff(g[np.argsort(x)]) >= -1e-12) and np.mean(np.abs(g - x)) < 0.08


def test_mz_and_law():
    rng = np.random.default_rng(1)
    f = rng.standard_normal(5000)
    a, b, r2 = mincer_zarnowitz(f, 0.5 * f + rng.standard_normal(5000))
    assert abs(a) < 0.05 and abs(b - 0.5) < 0.05 and 0.15 < r2 < 0.25
    assert effective_breadth(100, 0.0) == 100 and math.isclose(effective_breadth(100, 1.0), 1.0)
    assert math.isclose(effective_breadth(101, 0.01), 50.5)
    assert math.isclose(law_ir(0.05, 400), 1.0) and math.isclose(law_ir(0.05, 400, 0.5), 0.5)
    assert math.isclose(qian_hua_ir(0.03, 0.1), 0.3)
    assert math.isclose(ding_martin_ir(0.03, 0.0, 900), 0.03 / math.sqrt((1 - 0.0009) / 900))
    assert ding_martin_ir(0.03, 0.1, 10_000) < qian_hua_ir(0.03, 0.1)


def test_transfer_and_ir():
    rng = np.random.default_rng(2)
    alpha, vol = rng.standard_normal(500), rng.uniform(0.1, 0.4, 500)
    w = alpha / vol ** 2
    assert math.isclose(transfer_coefficient(w, alpha, vol), 1.0)
    assert transfer_coefficient(np.maximum(w, 0), alpha, vol) < 0.95
    p = np.tile([1.0, 3.0], 6)
    assert math.isclose(information_ratio(p, 12), 2.0 / p.std(ddof=1) * math.sqrt(12))
