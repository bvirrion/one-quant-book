import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_simlive import as_fills, calibrate, fill_pnl, implementation_shortfall, match_fills, parity, waterfall


def test_matching_and_parity():
    live = as_fills([(1.0, 1, 100, 100), (5.0, -1, 101, 100), (9.0, 1, 99, 100)])
    sim = as_fills([(1.4, 1, 100, 100), (5.2, -1, 101, 50), (6.0, -1, 101, 100), (20.0, 1, 99, 100)])
    pairs, live_left, sim_left = match_fills(live, sim, 1.0)
    assert [(i, j, q) for i, j, q in pairs] == [(0, 0, 100), (1, 1, 50), (1, 2, 50)]
    assert (live_left, sim_left) == (100, 150)
    assert parity(live, sim, 1.0) == (200 / 300, 200 / 350)
    assert parity(live, live, 0.0) == (1.0, 1.0)


def test_pnl_waterfall_calibrate():
    f = as_fills([(0, 1, 100, 100), (1, -1, 102, 100), (2, 1, 101, 100)])
    assert np.allclose(fill_pnl(f, 103.0), [300, -100, 200]) and fill_pnl(f, 103.0).sum() == 400
    w = waterfall([("sim", 100.0), ("latency", 70.0), ("live", 40.0)])
    assert w == [("sim", 100.0, 0.0), ("latency", 70.0, -30.0), ("live", 40.0, -30.0)]
    assert calibrate([0.0, 0.1, 0.2, 0.5], lambda p: 500 - 1000 * p, 390.0) == (0.1, 400.0)


def test_implementation_shortfall():
    fills = as_fills([(0, 1, 100.2, 600), (1, 1, 100.5, 200)])
    s = implementation_shortfall(1, 1000, 100.0, fills, 101.0, fee_per_unit=0.01)
    assert np.isclose(s["execution"], 600 * 0.2 + 200 * 0.5) and np.isclose(s["opportunity"], 200 * 1.0)
    assert np.isclose(s["fees"], 8.0) and np.isclose(s["total"], 220 + 200 + 8)
    sell = implementation_shortfall(-1, 100, 50.0, as_fills([(0, -1, 49.9, 100)]), 49.0)
    assert np.isclose(sell["execution"], 10.0) and sell["opportunity"] == 0.0
