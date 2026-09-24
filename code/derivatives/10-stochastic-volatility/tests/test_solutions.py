"""Numbers gate: every numerical answer printed in Book 5, Chapter 10 (text and solutions)."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from dv_heston import (
    BASE,
    Heston,
    atm_skew_term,
    butterfly,
    calibration,
    eta_for_butterfly,
    implied_vols,
    mixing_check,
    skew_90_110,
    smile,
)
from firm_heston import black_limit_vol, call_prices, simulate

M, RMSE, PER = calibration()


def test_text():
    s = smile(BASE, strikes=[80.0, 90, 100, 110, 120])
    assert [round(100 * x, 1) for x in s] == [23.4, 20.1, 16.9, 14.4, 13.3]
    st = simulate(BASE, 100, 1.0, 500, 200_000, 1)
    for k in (80.0, 100.0, 120.0):
        pay = np.maximum(st - k, 0)
        assert abs(pay.mean() - call_prices(BASE, 100, [k], 1.0)[0]) < 3 * pay.std() / math.sqrt(len(pay))
    assert (round(M.v0, 4), round(M.kappa, 2), round(M.vbar, 3), round(M.eta, 2), round(M.rho, 2)) == (0.0267, 2.05, 0.060, 0.66, -0.70)
    assert (round(100 * math.sqrt(M.v0), 1), round(100 * math.sqrt(M.vbar), 1), round(100 * RMSE, 2)) == (16.3, 24.5, 0.37)
    assert round(100 * max(p[2] for p in PER), 1) == 0.7 and round(M.feller(), 2) == -0.19
    sk = atm_skew_term(M, [1 / 52, 0.25, 0.5, 1.0])
    assert round(sk[0][1] / sk[0][2], 1) == 0.5 and round(-sk[0][1], 1) == 0.7
    assert (round(skew_90_110(BASE) * 100, 2), round(skew_90_110(Heston(0.04, 1.5, 0.04, 0.6, -0.5)) * 100, 2)) == (5.71, 3.94)
    assert (round(100 * butterfly(BASE), 2), round(eta_for_butterfly(0.005), 2)) == (0.30, 0.77)
    mix = {k: (m, se, f) for k, m, se, f in mixing_check()}
    assert (round(mix[100.0][0], 3), round(mix[100.0][2], 3), round(mix[100.0][1], 3)) == (7.136, 7.137, 0.011)
    assert all(abs(m - f) < 2 * se for m, se, f in mix.values())
    term = [implied_vols(BASE, 100.0, [100.0], t)[0] for t in (0.05, 1.0)]
    assert (round(100 * term[0], 1), round(100 * term[1], 1)) == (19.6, 16.9)


def test_exercises():
    assert (round(BASE.feller(), 2), round(M.feller(), 2)) == (-0.24, -0.19)
    v = lambda t: 0.04 + 0.04 * math.exp(-1.5 * t)  # noqa: E731
    assert (round(v(0.5), 4), round(v(1.0), 4)) == (0.0589, 0.0489)
    m = Heston(0.08, 1.5, 0.04, 0.6, -0.7)
    assert round(black_limit_vol(m, 1.0) ** 2, 4) == 0.0607 and round(100 * black_limit_vol(m, 1.0), 1) == 24.6
    e = eta_for_butterfly(0.005)
    assert round(100 * skew_90_110(Heston(0.04, 1.5, 0.04, e, -0.7)), 2) == 6.45
    assert abs(BASE.cf(np.array([-1j]), 1.0)[0] - 1) < 1e-12


def test_problem():
    assert round(100 * implied_vols(BASE, 100.0, [100.0], 5.0)[0], 1) == 17.4
    assert round(100 * (skew_90_110(Heston(0.04, 1.5, 0.04, 0.6, -0.5)) - skew_90_110(BASE)), 2) == -1.77
    e = eta_for_butterfly(0.005)
    assert round(2 * 1.5 * 0.04 - e * e, 2) == -0.47
    assert round(0.5 * 0.6 * 0.7 * 0.05, 4) == 0.0105
