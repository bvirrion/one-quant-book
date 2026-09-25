import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_markout import (
    curve,
    fill_rate,
    hit_ratio,
    markouts,
    microprice,
    mm_decompose,
    ref_at,
    settle_horizon,
    shortfall,
    tca_report,
    vwap_slippage,
)


def test_reference_and_markouts_by_hand():
    rt, rp = np.array([0.0, 1.0, 2.0, 5.0]), np.array([100.0, 101.0, 99.0, 102.0])
    assert list(ref_at(rt, rp, [0.5, 1.0, 4.9, 9.0])) == [100.0, 101.0, 99.0, 102.0]
    M = markouts([0.5, 0.5], [1, -1], [99.5, 100.5], rt, rp, [0, 1, 5])
    assert M.tolist() == [[0.5, 1.5, 2.5], [0.5, -0.5, -1.5]]
    c = curve(M, [1, 3])
    assert np.allclose(c[0][0], [0.5, 0.0, -0.5])
    assert microprice(99, 1, 101, 3) == 99.5                              # more size on the ask: nearer the bid
    assert settle_horizon([0.5, -0.4, -0.52, -0.5], [0, 1, 5, 10], 0.05) == 5


def test_mm_decomposition_adds_up():
    rng = np.random.default_rng(0)
    rt = np.sort(rng.uniform(0, 100, 500))
    rp = 1000 + np.cumsum(rng.choice([-1, 0, 1], 500))
    n = 60
    t = np.sort(rng.uniform(0, 99, n))
    side = rng.choice([-1, 1], n)
    px = ref_at(rt, rp, t) - side * 0.5
    qty = rng.integers(1, 5, n)
    d = mm_decompose(t, side, px, qty, rt, rp, H=2.0, fee=0.1)
    pos = np.cumsum(side * qty)[-1]
    pnl = float(-(side * qty) @ px + pos * rp[-1]) - 0.1 * qty.sum()
    assert abs(d["total"] - pnl) < 1e-9 and abs(d["spread"] - 0.5 * qty.sum()) < 1e-9


def test_shortfall_by_hand():
    sf = shortfall(1, 100, 50.0, 50.2, [(50.3, 40), (50.5, 40)], 51.0, fee=0.01)
    assert abs(sf["delay"] - 80 * 0.2) < 1e-12 and abs(sf["execution"] - (40 * 0.1 + 40 * 0.3)) < 1e-12
    assert abs(sf["opportunity"] - 20 * 1.0) < 1e-12 and abs(sf["fees"] - 0.8) < 1e-12
    paper = 100 * (51.0 - 50.0)                                          # the paper portfolio's gain
    real = 40 * (51.0 - 50.3) + 40 * (51.0 - 50.5) - 0.8
    assert abs(sf["total"] - (paper - real)) < 1e-9                       # shortfall = paper - real
    assert abs(vwap_slippage(1, [(50.3, 40), (50.5, 40)], [50.0, 51.0], [1, 1]) + 0.1) < 1e-12
    assert fill_rate([2, 2, 2], [2, 0, 1]) == 0.5 and hit_ratio(40, 10) == 0.25
    assert "opportunity" in tca_report("x", sf, 0.1)
