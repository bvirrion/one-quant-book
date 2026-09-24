import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_energymodel as f

M = f.TwoFactor(1.5, 0.6, 0.2, 0.3)


def test_forwards_are_martingales_with_the_model_variance():
    chi, xi = M.simulate([0.5], 200_000, seed=1)
    F = M.forward(3.0, 0.5, 0.75, chi[:, 0], xi[:, 0])
    assert abs(F.mean() - 3.0) < 3e-3
    assert abs(np.log(F).var() - M.var(0.5, 0.75)) < 2e-3


def test_calibration_recovers_the_parameters():
    quotes = [(t - 0.04, t, M.implied_vol(t - 0.04, t)) for t in np.linspace(0.1, 1.0, 10)]
    fit = f.calibrate(quotes, 0.3)
    assert abs(fit.kappa - 1.5) < 1e-4 and abs(fit.sigma_s - 0.6) < 1e-5 and abs(fit.sigma_l - 0.2) < 1e-5


def test_kirk_reduces_to_margrabe_and_is_close_to_monte_carlo():
    assert abs(f.kirk(3.4, 2.7, 0.0, 0.3, 0.4, 0.5, 0.6) - f.margrabe(3.4, 2.7, 0.3, 0.4, 0.5, 0.6)) < 1e-14
    mc, se = f.spread_mc(3.4, 2.7, 0.3, 0.3, 0.4, 0.5, 0.6)
    assert abs(f.kirk(3.4, 2.7, 0.3, 0.3, 0.4, 0.5, 0.6) - mc) < 0.01 * mc


def test_storage_intrinsic_flat_curve_and_zero_volatility():
    fac = f.Facility(4, 1, 2, 0.01, 0.01)
    assert f.intrinsic(fac, [3.0] * 6, [1.0] * 6)[0] == 0.0
    prices = [2.0, 2.1, 2.2, 3.0, 3.2, 2.9]
    iv, plan = f.intrinsic(fac, prices, [1.0] * 6)
    flat = np.tile(np.array(prices), (50, 1))
    assert abs(f.lsm(fac, flat, [1.0] * 6) - iv) < 1e-9 and sum(plan) == 0


def test_rolling_intrinsic_and_lsm_exceed_intrinsic():
    F0 = [2.6, 2.7, 2.8, 3.4, 3.5, 3.0]
    T = [k / 12 + 1 / 24 for k in range(6)]
    fac = f.Facility(4, 1, 2, 0.02, 0.02)
    iv = f.intrinsic(fac, F0, [1.0] * 6)[0]
    assert f.rolling_intrinsic(fac, M, F0, T, [1.0] * 6, 1000) > iv
    assert f.lsm(fac, f.spot_paths(M, F0, T, 2000), [1.0] * 6) > iv


def test_swing_without_volatility_is_its_intrinsic():
    fac = f.swing_facility(3, 1, 3.0)
    prices = [2.8, 3.3, 3.1, 3.4, 2.9]
    iv, _ = f.intrinsic(fac, prices, [1.0] * 5)
    assert math.isclose(iv, 0.3 + 0.1 + 0.4)
    assert abs(f.lsm(fac, np.tile(np.array(prices), (20, 1)), [1.0] * 5) - iv) < 1e-9
