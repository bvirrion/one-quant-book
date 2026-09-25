import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_capacity import (
    avg_pairwise_corr,
    capacity_curve,
    comomentum,
    overlap,
    profit_maximising,
    size_at_fraction,
    unwind,
)


def test_capacity_curve_analytic():
    sizes = np.exp(np.linspace(math.log(1e7), math.log(1e11), 400))
    g, k = 0.10, 0.10 / math.sqrt(1e10)                                 # net return g - k sqrt(A): zero at 1e10
    c = capacity_curve(sizes, g - k * np.sqrt(sizes), np.full(400, 0.10))
    assert abs(profit_maximising(c) / (2 * g / (3 * k)) ** 2 - 1) < 0.03   # A* = (2g / 3k)^2
    half = size_at_fraction(c, 0.5)
    target = 0.5 * (g - k * math.sqrt(1e7))                                # half the best, at the smallest size
    assert abs(half / ((g - target) / k) ** 2 - 1) < 0.01
    assert size_at_fraction(capacity_curve([1, 2], [1, 1], [1, 1])) is None


def test_crowding_monitors():
    rng = np.random.default_rng(0)
    common = rng.standard_normal((500, 1))
    R = 0.5 * common + rng.standard_normal((500, 20))
    assert abs(avg_pairwise_corr(R) - 0.2) < 0.03                        # 0.25 / 1.25
    assert abs(comomentum(R, rng.standard_normal((500, 20))) - 0.1) < 0.03
    assert abs(overlap([1, 0, -1], [1, 0, -1]) - 1) < 1e-12 and abs(overlap([1, 0], [0, 1])) < 1e-12


def test_unwind():
    n = 50
    books = np.array([np.r_[np.full(25, 0.04), np.full(25, -0.04)]] * 3)
    books[2] = np.r_[np.full(25, -0.04), np.full(25, 0.04)]                 # the opposite book
    out = unwind(books, [1e9, 1e9, 1e9], seller=0, fraction=1.0, days=2, adv=np.full(n, 1e8),
                 sigma=np.full(n, 0.02), permanent=0.0, half_life=1.0, horizon=12)
    cum = out["cum"]
    assert cum[1, 1] < 0 and cum[1, 2] > 0 and abs(cum[1, 1] + cum[1, 2]) < 1e-12   # same book loses, opposite gains
    assert abs(cum[-1, 1]) < 0.01 * abs(cum[:, 1].min())                  # temporary impact: it all comes back
    assert abs(out["price"][-1]).max() < 0.02 * abs(out["price"][2]).max()
    perm = unwind(books, [1e9, 1e9, 1e9], 0, 1.0, 2, np.full(n, 1e8), np.full(n, 0.02), permanent=1.0, horizon=12)
    assert np.allclose(perm["price"][-1], perm["price"][2]) and perm["cum"][-1, 1] < 0     # nothing comes back
