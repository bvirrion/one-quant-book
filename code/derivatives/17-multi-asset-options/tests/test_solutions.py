"""Numbers gate: every numerical answer printed in Book 5, Chapter 17 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_multiasset import (
    INDEX_STRIKES,
    MEMBER_VOLS,
    WEIGHTS,
    calibrate_local_correlation,
    correlation_by_strike,
    dispersion,
    dispersion_vol_shift,
    index_vol,
    quanto_call,
    quanto_example,
    three_share_prices,
    variance_implied_correlation,
    worst_digital_local_corr,
)
from firm_multiasset import composite_vol, implied_correlation

TS = {r["rho"]: r for r in three_share_prices()}
LC = calibrate_local_correlation()


def test_three_shares():
    assert (round(TS[0.0]["worst_digital"], 3), round(TS[0.95]["worst_digital"], 3)) == (0.616, 0.787)
    assert round(100 * TS[0.0]["worst_digital"]) == 62 and round(100 * TS[0.95]["worst_digital"]) == 79
    assert (round(TS[0.4]["worst_digital"], 3), round(TS[0.6]["worst_digital"], 3)) == (0.673, 0.707)
    assert (round(TS[0.0]["worst_put"], 3), round(TS[0.95]["worst_put"], 3)) == (0.250, 0.152)
    assert (round(TS[0.0]["best_call"], 3), round(TS[0.95]["best_call"], 3)) == (0.284, 0.160)
    assert (round(TS[0.0]["basket_call"], 3), round(TS[0.95]["basket_call"], 3)) == (0.071, 0.118)
    assert max(abs(r["basket_call"] - r["basket_mm"]) for r in TS.values()) < 0.0005
    slope = (TS[0.6]["worst_digital"] - TS[0.4]["worst_digital"]) / 0.2 * 0.05
    assert 0.007 < slope < 0.011


def test_index():
    assert [round(100 * index_vol(k), 1) for k in INDEX_STRIKES] == [21.9, 19.2, 17.0]
    rc = correlation_by_strike()
    assert [round(rc[k], 3) for k in INDEX_STRIKES] == [0.549, 0.408, 0.308]
    iv = variance_implied_correlation()
    assert (round(100 * iv["index_vs"], 1), round(iv["rho"], 3)) == (22.1, 0.559)
    assert (round(iv["own"], 5), round(iv["cross"], 4), round(1e4 * iv["cross"])) == (0.0043, 0.0798, 798)
    assert [round(100 * v, 1) for v in LC["constant"][[0, 2]]] == [19.3, 19.3]
    assert (round(LC["a"], 3), round(LC["b"], 2), round(LC["c"], 1)) == (0.384, 3.62, 16.3)
    assert [round(100 * v, 2) for v in LC["fitted"]] == [21.93, 19.19, 16.99]
    assert [round(100 * v, 2) for v in LC["target"]] == [21.93, 19.19, 16.98]
    rho = lambda x: LC["a"] - LC["b"] * x + LC["c"] * x * x  # noqa: E731
    assert (round(rho(-0.1), 2), round(rho(0.1), 2)) == (0.91, 0.19) and rho(-0.15) > 1
    assert round(math.sqrt(iv["own"]), 3) == 0.066 and round(float(WEIGHTS @ MEMBER_VOLS), 3) == 0.290


def test_dispersion():
    d = dispersion()
    assert (round(d["k_idx"], 2), round(d["n_var"]), round(d["rho_realised"], 3)) == (22.12, 2261, 0.409)
    assert round(d["theory"], -2) == 270_600 and round(2261 * 0.15 * 798, -2) == 270_600
    p = d["pnl"]
    assert (round(p.mean(), -3), round(p.std(), -3)) == (271_000, 34_000)
    assert (round(np.percentile(p, 5), -3), round(np.percentile(p, 95), -3)) == (215_000, 326_000)
    assert abs(d["corr"].mean() - d["rho_realised"]) < 0.005
    assert round(dispersion_vol_shift()) == 28
    assert round(d["n_var"] * (1 - d["rho_implied"]) * 798, -5) == 800_000


def test_quanto():
    q = {r["rho"]: r for r in quanto_example()}
    assert [round(q[r]["analytic"], 2) for r in (-0.6, -0.3, 0.3, 0.6)] == [101.21, 100.60, 99.40, 98.81]
    assert max(abs(r["analytic"] - r["mc"]) for r in q.values()) < 0.006
    c = quanto_call()
    assert (round(c["quanto"], 2), round(c["plain"], 2)) == (8.29, 7.97)
    assert round(100 * composite_vol(0.2, 0.1, -0.3), 1) == 19.5


def test_exercises():
    w, v = np.array([0.5, 0.5]), np.array([0.2, 0.3])
    assert round(100 * math.sqrt(0.25 * 0.04 + 0.25 * 0.09 + 2 * 0.25 * 0.5 * 0.06), 1) == 21.8
    assert round(implied_correlation(0.24, w, np.array([0.25, 0.35])), 2) == 0.26
    assert round(worst_digital_local_corr((LC["a"], LC["b"], LC["c"])), 3) == 0.736
    assert v.sum() > 0
