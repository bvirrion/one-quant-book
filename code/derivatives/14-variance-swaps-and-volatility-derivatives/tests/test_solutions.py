"""Numbers gate: every numerical answer printed in Book 5, Chapter 14 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_varswap import (
    MERTON,
    MONTH,
    F,
    calibration,
    contributions,
    fair_variance,
    gamma_swap_strike,
    hedge_pnl,
    heston_terms,
    index_errors,
    market_vol_k,
    strip_bias_merton,
    vix_curve,
    vix_options,
)
from firm_varswap import (
    heston_mean_variance,
    heston_vol_swap,
    index_variance,
    jump_error,
    mark_to_market,
    strip_from_vols,
    variance_notional,
    vol_swap_approx,
)

HT = {round(r["t"], 4): r for r in heston_terms()}
VC = {round(12 * r["t"]): r for r in vix_curve()}


def test_strip_and_notionals():
    assert round(100 * math.sqrt(fair_variance(1.0)), 1) == 22.1 and round(100 * market_vol_k(0.0, 1.0), 1) == 19.2
    k, w = contributions()
    assert round(100 * (w[k < 100].sum() + 0.5 * w[k == 100].sum())) == 72
    assert round(100 * w[k < 80].sum()) == 24 and round(100 * w[k > 120].sum(), 1) == 1.5
    n = variance_notional(100_000, 22.1)
    assert round(n) == 2262
    assert round(n * (30 ** 2 - 22.1 ** 2), -3) == 931_000 and round(n * (15 ** 2 - 22.1 ** 2), -3) == -596_000
    assert round(100_000 * (30 - 22.1), -3) == 790_000 and round(100_000 * (15 - 22.1), -3) == -710_000
    mtm = mark_to_market(n, 22.1, 25 ** 2, 0.5, 20.1 ** 2, 0.5)
    assert round(0.5 * 625 + 0.5 * 20.1 ** 2, 1) == 514.5 and round(22.1 ** 2, 1) == 488.4
    assert round(mtm, -3) == 59_000
    assert round(100 * gamma_swap_strike(1.0), 1) == 20.8


def test_index_errors():
    e = index_errors()
    assert round(100 * e["exact_vol"], 2) == 16.30
    rows = {r["lo"]: r for r in e["rows"]}
    table = {70: (0.01, 0.06, 0.38), 80: (-0.02, 0.03, 0.36), 85: (-0.13, -0.07, 0.28), 90: (-0.48, -0.40, 0.01),
             95: (-1.78, -1.61, -0.92)}
    for lo, vals in table.items():
        assert tuple(round(rows[lo][dk], 2) for dk in (0.5, 1.0, 2.5)) == vals
    ks = np.arange(80.0, 120.01, 1.0)
    k, c, p = strip_from_vols(lambda x: market_vol_k(x, MONTH), F, MONTH, ks)
    full = math.sqrt(index_variance(k, c, p, F, MONTH))
    q = np.where(k < F, p, c)
    keep = q >= 0.05
    cut = math.sqrt(index_variance(k[keep], c[keep], p[keep], F, MONTH))
    assert (round(100 * full, 2), round(100 * cut, 2), k[keep].min(), k[keep].max()) == (16.32, 16.10, 87.0, 106.0)
    assert round(100 * (full - cut), 2) == 0.22


def test_heston():
    r1 = HT[1.0]
    assert (round(100 * r1["var"], 1), round(100 * r1["vol"], 1), round(100 * r1["adj"], 2)) == (21.4, 19.8, 1.62)
    adj = [round(100 * HT[round(t, 4)]["adj"], 2) for t in (1 / 12, 0.25, 0.5, 2.0, 3.0)]
    assert adj == [0.72, 1.34, 1.61, 1.35, 1.10]
    assert round(100 * (r1["market_var"] - r1["var"]), 1) == 0.7
    m = calibration()[0]
    base = math.sqrt(heston_mean_variance(m.v0, m.kappa, m.vbar, 1.0))
    lo, hi = (base - heston_vol_swap(m.v0, m.kappa, m.vbar, m.eta + d, 1.0) for d in (-0.1, 0.1))
    assert (round(100 * lo, 2), round(100 * hi, 2)) == (1.24, 2.01)
    assert round(math.log(2) / m.kappa * 12) == 4


def test_index_futures_and_options():
    assert round(100 * VC[0]["future"], 1) == 17.1
    assert (round(100 * VC[3]["future"], 1), round(100 * VC[3]["fwd"], 1)) == (18.1, 20.4)
    assert (round(100 * VC[6]["future"], 1), round(100 * VC[6]["fwd"], 1)) == (19.3, 22.2)
    assert (round(100 * VC[12]["future"], 1), round(100 * VC[12]["fwd"], 1)) == (20.5, 23.7)
    gaps = [100 * (r["fwd"] - r["future"]) for r in VC.values() if r["t"] > 0]
    assert 1 < min(gaps) and max(gaps) < 3.3
    v = vix_options()["vols"]
    assert (round(100 * v[0]), round(100 * v[-1])) == (110, 94) and all(np.diff(v) < 0)


def test_jumps():
    assert round(0.04 - 2 * (math.exp(-0.2) - 1 + 0.2), 4) == 0.0025 and round(2 * (math.exp(-0.2) - 0.8), 4) == 0.0375
    b = strip_bias_merton()
    assert (round(b["per_jump"], 6), round(b["cubic"], 6)) == (-0.000182, -0.000188)
    assert round(b["gap_var"], 5) == 0.00058 and round(b["gap_vol_pts"], 2) == 0.18
    h = hedge_pnl()
    assert round(float(-h["jumps"].mean()), 2) == 0.17
    assert (round(float(h["jumps"].std()), 2), round(float(np.percentile(h["jumps"], 1)), 1)) == (0.40, -1.9)
    assert round(float(h["diffusion"].std()), 3) == 0.014 and h["diffusion"].min() > -0.1
    assert MERTON.lam == 3.16 and jump_error(-0.2) < 0


def test_exercises():
    assert variance_notional(50_000, 20) == 1250 and 1250 * (25 ** 2 - 20 ** 2) == 281_250
    assert 0.75 * 18 ** 2 + 0.25 * 16 ** 2 - 22 ** 2 == -177
    assert round(100 * vol_swap_approx(0.04, 0.02 ** 2), 1) == 19.4 and round(0.0004 / (8 * 0.04 ** 1.5), 5) == 0.00625
