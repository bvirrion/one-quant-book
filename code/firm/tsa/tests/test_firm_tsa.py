"""Acceptance tests of firm.tsa."""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_tsa import (
    acf,
    adf,
    ar1,
    arma_css,
    frac_diff,
    hurst_gph,
    hurst_rs,
    mackinnon_crit,
    pacf,
    periodogram,
    yule_walker,
)


def _ar(phi, n, rng, ma=()):
    e = rng.standard_normal(n + 500)
    x = np.zeros(n + 500)
    for t in range(2, n + 500):
        x[t] = sum(p * x[t - 1 - i] for i, p in enumerate(phi)) + e[t] + sum(m * e[t - 1 - j] for j, m in enumerate(ma))
    return x[500:]


def test_acf_pacf_yule_walker():
    rng = np.random.default_rng(1)
    x = _ar([0.6], 20_000, rng)
    r = acf(x, 3)
    assert np.allclose(r[1:], [0.6, 0.36, 0.216], atol=0.02)
    p = pacf(x, 3)
    assert abs(p[1] - 0.6) < 0.02 and abs(p[2]) < 0.03 and abs(p[3]) < 0.03
    phi, s2 = yule_walker(_ar([0.5, -0.3], 20_000, rng), 2)
    assert np.allclose(phi, [0.5, -0.3], atol=0.02) and abs(s2 - 1) < 0.05


def test_arma_css():
    rng = np.random.default_rng(2)
    x = _ar([0.7], 8000, rng, ma=(0.4,))
    phi, theta, s2 = arma_css(x, 1, 1)
    assert abs(phi[0] - 0.7) < 0.03 and abs(theta[0] - 0.4) < 0.04 and abs(s2 - 1) < 0.05


def test_ar1_half_life_and_kendall():
    rng = np.random.default_rng(3)
    x = _ar([0.95], 50_000, rng)
    a = ar1(x)
    assert abs(a["rho"] - 0.95) < 0.005 and abs(a["half_life"] - math.log(0.5) / math.log(a["rho"])) < 1e-12
    assert abs(a["rho_kendall"] - (a["rho"] + (1 + 3 * a["rho"]) / x.size)) < 1e-15


def test_dickey_fuller():
    assert abs(mackinnon_crit("c", 100)[1] - (-2.86154 - 2.8903 / 100 - 4.234 / 1e4 - 40.040 / 1e6)) < 1e-12
    rng = np.random.default_rng(4)
    rej = sum(adf(np.cumsum(rng.standard_normal(300)), lags=1)["tau"] < mackinnon_crit("c", 298)[1] for _ in range(1000))
    assert abs(rej / 1000 - 0.05) < 0.02                                   # correct size under the unit root
    assert adf(_ar([0.9], 500, rng))["tau"] < mackinnon_crit("c", 500)[0]   # a stationary AR(1) is rejected


def test_spectral_and_memory():
    rng = np.random.default_rng(5)
    e = rng.standard_normal(4096)
    w, i = periodogram(e)
    assert abs(np.mean(i) - 1 / (2 * math.pi)) < 0.01                      # white noise: flat at sigma^2 / (2 pi)
    x = rng.standard_normal(1000)
    assert np.allclose(frac_diff(np.cumsum(x), 1.0, k=10), x[10:])          # d = 1 is the first difference
    z = rng.standard_normal(40_000)
    assert abs(hurst_rs(z) - 0.5) < 0.06 and abs(hurst_gph(z) - 0.5) < 0.1
    lm = frac_diff(rng.standard_normal(42_000), -0.3, k=2000)[-40_000:]
    assert abs(hurst_gph(lm) - 0.8) < 0.1
