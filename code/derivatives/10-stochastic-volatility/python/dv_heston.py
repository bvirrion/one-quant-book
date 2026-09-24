"""Stochastic volatility: the Heston model's smile, what each parameter does, calibration to a surface,
and the mixing formula (Book 5, Chapter 10). Zero rates and dividends: F = S = 100."""
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for comp in ("bs", "svi", "heston"):
    sys.path.insert(0, str(ROOT / f"code/firm/{comp}"))
from firm_heston import Heston, calibrate, call_prices, implied_vols  # noqa: E402
from firm_svi import ssvi  # noqa: E402

BASE = Heston(v0=0.04, kappa=1.5, vbar=0.04, eta=0.6, rho=-0.7)
STRIKES = np.arange(70.0, 130.01, 2.5)


def smile(m: Heston, t: float = 1.0, strikes=STRIKES) -> np.ndarray:
    return implied_vols(m, 100.0, strikes, t)


def skew_90_110(m: Heston, t: float = 1.0) -> float:
    v = implied_vols(m, 100.0, [90.0, 110.0], t)
    return float(v[0] - v[1])


def butterfly(m: Heston, t: float = 1.0) -> float:
    """Curvature measure: average of the 90 and 110 volatilities minus the at-the-money volatility."""
    v = implied_vols(m, 100.0, [90.0, 100.0, 110.0], t)
    return float(0.5 * (v[0] + v[2]) - v[1])


def eta_for_butterfly(target: float, base: Heston = BASE, t: float = 1.0) -> float:
    lo, hi = 0.05, 2.0
    for _ in range(50):
        mid = 0.5 * (lo + hi)
        m = Heston(base.v0, base.kappa, base.vbar, mid, base.rho)
        if butterfly(m, t) < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------- calibration to a market surface
MARKET_TENORS = (0.25, 0.5, 1.0, 2.0)
MARKET_STRIKES = np.array([80.0, 85, 90, 95, 100, 105, 110, 115, 120])


def market_vol(k: float, t: float) -> float:
    """The market of chapter 9: an SSVI surface (rho -0.6, eta 1.0, gamma 0.45)."""
    theta = (0.20 - 0.06 * math.exp(-t / 0.5)) ** 2 * t
    return math.sqrt(float(ssvi(math.log(k / 100.0), theta, -0.6, 1.0, 0.45)) / t)


def market_quotes():
    return [(t, MARKET_STRIKES, np.array([market_vol(k, t) for k in MARKET_STRIKES])) for t in MARKET_TENORS]


def calibration():
    q = market_quotes()
    m, rmse = calibrate(q, 100.0, BASE)
    per = []
    for t, ks, vols in q:
        err = implied_vols(m, 100.0, ks, t) - vols
        per.append((t, float(np.sqrt(np.mean(err ** 2))), float(np.max(np.abs(err)))))
    return m, rmse, per


# ---------------------------------------------------------------- the mixing formula
def mixing_check(n: int = 100_000, steps: int = 400, seed: int = 4, t: float = 1.0):
    """With rho = 0 the call is the Black-Scholes price at the realised root-mean variance, averaged over
    variance paths: simulate v, integrate it, average Black's formula; compare with the Fourier price."""
    m = Heston(0.04, 1.5, 0.04, 0.6, 0.0)
    rng = np.random.default_rng(seed)
    dt = t / steps
    v = np.full(n, m.v0)
    integ = np.zeros(n)
    for _ in range(steps):
        vp = np.maximum(v, 0.0)
        integ += vp * dt
        v += m.kappa * (m.vbar - vp) * dt + m.eta * np.sqrt(vp * dt) * rng.standard_normal(n)
    out = []
    sd = np.sqrt(integ)
    for k in (80.0, 100.0, 120.0):
        d1 = np.log(100.0 / k) / sd + 0.5 * sd
        calls = 100.0 * _ncdf(d1) - k * _ncdf(d1 - sd)
        mix, se = float(calls.mean()), float(calls.std(ddof=1) / math.sqrt(n))
        out.append((k, mix, se, float(call_prices(m, 100.0, [k], t)[0])))
    return out


def _ncdf(x: np.ndarray) -> np.ndarray:
    return 0.5 * np.vectorize(math.erfc)(-x / math.sqrt(2.0))


def atm_skew_term(m: Heston, tenors) -> list[tuple[float, float, float]]:
    """At-the-money skew d sigma / dk of the model and of the market, by central difference."""
    out = []
    for t in tenors:
        h = 0.01
        mv = implied_vols(m, 100.0, [100 * math.exp(-h), 100 * math.exp(h)], t)
        out.append((t, float((mv[1] - mv[0]) / (2 * h)),
                    (market_vol(100 * math.exp(h), t) - market_vol(100 * math.exp(-h), t)) / (2 * h)))
    return out
