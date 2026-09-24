"""Acceptance tests of the Book 6, chapter 11 build (Jarrow-Yildirim with deterministic nominal rates)."""
import math
import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_inflopt import JYDet, LogLinearCurve, real_curve

YRS = [1, 2, 5, 10, 20]
NOM = LogLinearCurve(YRS, [math.exp(-0.035 * t) for t in YRS])
REAL = real_curve(NOM, YRS, [0.03, 0.03, 0.031, 0.032, 0.032])


def jy(**kw):
    p = {"kappa": 0.05, "sigma_r": 0.008, "sigma_i": 0.015, "rho": 0.2}
    p.update(kw)
    return JYDet(NOM, REAL, **p)


def test_zero_coupon_consistency_and_first_year():
    m = jy()
    assert m.zc_swap_rate(10.0) == pytest.approx(0.032, abs=1e-12)
    assert m.convexity(0.0, 1.0) == 0.0
    assert abs(jy(sigma_r=1e-9).convexity(5.0, 6.0)) < 1e-10 < abs(jy().convexity(5.0, 6.0))


def test_yoy_expectation_matches_simulation():
    m = jy()
    r = m.simulate_ratios(8, 40000)[:, 7]
    assert abs(r.mean() - m.yoy_ratio(7.0, 8.0)) < 3 * r.std(ddof=1) / math.sqrt(len(r))


def test_caplet_parity_and_uncapped_lpi():
    m = jy()
    cap, flo = m.yoy_caplet(4, 5, 0.03), m.yoy_caplet(4, 5, 0.03, floor=True)
    assert cap - flo == pytest.approx(NOM.df_t(5) * (m.yoy_ratio(4, 5) - 1.03), abs=1e-14)
    out = m.lpi_leg(5, cap=10.0, floor=-10.0, paths=20000)
    assert out["lpi"] == pytest.approx(out["uncapped"], rel=1e-12)
    assert abs(out["uncapped"] - out["uncapped_exact"]) < 4 * out["lpi_se"]
    assert np.isfinite(m.yoy_log_variance(3, 4)) and m.yoy_log_variance(3, 4) > 0
