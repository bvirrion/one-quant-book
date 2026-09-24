"""SABR: Hagan's implied-volatility formula, calibration with a fixed beta, and three deltas
(build of Book 5, Chapter 11). Rates-style SABR on a forward F:

    dF = alpha F^beta dW1,  d alpha = nu alpha dW2,  d<W1, W2> = rho dt.

hagan_lognormal is Hagan, Kumar, Lesniewski and Woodward (2002), equations (2.17a-c); normal_vol converts
its Black price to a Bachelier implied volatility with Book 2's normal-volatility solver.
"""
import math
import pathlib
import sys

import numpy as np

FIRM = pathlib.Path(__file__).resolve().parents[1]
for comp in ("bs", "normalvol", "svi"):
    sys.path.insert(0, str(FIRM / comp))
from firm_bs import black, greeks  # noqa: E402
from firm_normalvol import implied as bachelier_implied  # noqa: E402
from firm_svi import nelder_mead  # noqa: E402


def hagan_lognormal(f: float, k: float, t: float, alpha: float, beta: float, rho: float, nu: float) -> float:
    """Black implied volatility of the SABR model (Hagan et al. 2002, 2.17)."""
    fk = f * k
    lfk = math.log(f / k)
    omb = 1.0 - beta
    pre = alpha / (fk ** (omb / 2) * (1 + omb ** 2 / 24 * lfk ** 2 + omb ** 4 / 1920 * lfk ** 4))
    z = nu / alpha * fk ** (omb / 2) * lfk
    if abs(z) < 1e-8:
        zx = 1.0 - 0.5 * rho * z
    else:
        x = math.log((math.sqrt(1 - 2 * rho * z + z * z) + z - rho) / (1 - rho))
        zx = z / x
    corr = 1 + (omb ** 2 / 24 * alpha ** 2 / fk ** omb + 0.25 * rho * beta * nu * alpha / fk ** (omb / 2)
                + (2 - 3 * rho * rho) / 24 * nu * nu) * t
    return pre * zx * corr


def alpha_from_atm(f: float, t: float, sigma_atm: float, beta: float, rho: float, nu: float) -> float:
    """The alpha that reproduces an at-the-money Black volatility: the smallest positive root of the cubic
    (2.18) in alpha."""
    omb = 1.0 - beta
    c3 = omb ** 2 * t / (24 * f ** (2 - 2 * beta))
    c2 = rho * beta * nu * t / (4 * f ** omb)
    c1 = 1 + (2 - 3 * rho * rho) / 24 * nu * nu * t
    c0 = -sigma_atm * f ** omb
    roots = np.roots([c3, c2, c1, c0]) if c3 > 0 else np.roots([c2, c1, c0])
    real = sorted(r.real for r in roots if abs(r.imag) < 1e-12 and r.real > 0)
    return real[0]


def calibrate(f: float, t: float, strikes, vols, beta: float,
              atm_vol: float) -> tuple[tuple[float, float, float], float]:
    """Fit (rho, nu) with alpha tied to the at-the-money volatility; returns (alpha, rho, nu) and the RMSE."""
    strikes, vols = np.asarray(strikes, float), np.asarray(vols, float)

    def params(z):
        rho, nu = math.tanh(z[0]), math.exp(z[1])
        return alpha_from_atm(f, t, atm_vol, beta, rho, nu), rho, nu

    def obj(z):
        a, r, n = params(z)
        return float(sum((hagan_lognormal(f, k, t, a, beta, r, n) - v) ** 2
                         for k, v in zip(strikes, vols, strict=True)))
    z, v = nelder_mead(obj, [-0.3, math.log(0.5)], [0.3, 0.3], tol=1e-14)
    return params(z), math.sqrt(v / len(strikes))


def normal_vol(f: float, k: float, t: float, alpha: float, beta: float, rho: float, nu: float) -> float:
    """Bachelier implied volatility of the SABR Black price (payer, unit annuity)."""
    p = black(f, k, t, 1.0, hagan_lognormal(f, k, t, alpha, beta, rho, nu), "C")
    return bachelier_implied(p, f, k, t)


def deltas(f: float, k: float, t: float, alpha: float, beta: float, rho: float, nu: float, h: float = 1e-6) -> dict:
    """Black delta (volatility frozen), Hagan's delta (volatility moves along the smile with F, alpha fixed)
    and Bartlett's delta (alpha also moves with its expected co-move rho nu / F^beta dF)."""
    def vol(ff: float, aa: float) -> float:
        return hagan_lognormal(ff, k, t, aa, beta, rho, nu)
    sig = vol(f, alpha)
    g = greeks(f, k, t, 0.0, 0.0, sig, "C")             # on the forward, zero rates
    dsig_df = (vol(f + h, alpha) - vol(f - h, alpha)) / (2 * h)
    ha = 1e-6 * alpha
    dsig_da = (vol(f, alpha + ha) - vol(f, alpha - ha)) / (2 * ha)
    black_d = g["delta"]
    hagan_d = black_d + g["vega"] * dsig_df
    bartlett_d = hagan_d + g["vega"] * dsig_da * rho * nu / f ** beta
    return {"black": black_d, "hagan": hagan_d, "bartlett": bartlett_d, "vega": g["vega"], "sigma": sig}


def one_day_hedge_errors(f0: float, k: float, t: float, alpha: float, beta: float, rho: float, nu: float,
                         n: int = 200_000, seed: int = 3, dt: float = 1 / 252) -> dict[str, float]:
    """Standard deviation of the one-day P&L of a call hedged with each delta, under SABR dynamics."""
    rng = np.random.default_rng(seed)
    z1 = rng.standard_normal(n)
    z2 = rho * z1 + math.sqrt(1 - rho * rho) * rng.standard_normal(n)
    f1 = f0 + alpha * f0 ** beta * math.sqrt(dt) * z1
    a1 = alpha * np.exp(nu * math.sqrt(dt) * z2 - 0.5 * nu * nu * dt)
    v0 = black(f0, k, t, 1.0, hagan_lognormal(f0, k, t, alpha, beta, rho, nu), "C")
    v1 = np.array([black(ff, k, t - dt, 1.0, hagan_lognormal(ff, k, t - dt, aa, beta, rho, nu), "C")
                   for ff, aa in zip(f1, a1, strict=True)])
    d = deltas(f0, k, t, alpha, beta, rho, nu)
    return {name: float(np.std(v1 - v0 - d[name] * (f1 - f0))) for name in ("black", "hagan", "bartlett")}
