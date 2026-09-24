"""SABR and smile dynamics: backbones, a fit, the low-strike density problem, three deltas and the hedging
experiment (Book 5, Chapter 11)."""
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for comp in ("bs", "svi", "sabr"):
    sys.path.insert(0, str(ROOT / f"code/firm/{comp}"))
from firm_bs import black  # noqa: E402
from firm_sabr import alpha_from_atm, calibrate, deltas, hagan_lognormal, normal_vol, one_day_hedge_errors  # noqa: E402
from firm_svi import ssvi  # noqa: E402

# A rates-style example: a 3% forward, one-year expiry, 20% at-the-money Black volatility.
F0, T, BETA, RHO, NU = 0.03, 1.0, 0.5, -0.6, 0.5
ALPHA = alpha_from_atm(F0, T, 0.20, BETA, RHO, NU)


def backbone(beta: float, fs, t: float = T, rho: float = RHO, nu: float = NU) -> list[tuple[float, float]]:
    """At-the-money volatility as the forward moves, alpha fixed at the value that gives 20% at F0."""
    a = alpha_from_atm(F0, t, 0.20, beta, rho, nu)
    return [(f, hagan_lognormal(f, f, t, a, beta, rho, nu)) for f in fs]


def smiles_at_forwards(fs=(0.025, 0.03, 0.035), ks=None):
    ks = np.linspace(0.015, 0.05, 36) if ks is None else ks
    return {f: [(k, hagan_lognormal(f, k, T, ALPHA, BETA, RHO, NU)) for k in ks] for f in fs}


def equity_fit():
    """Fit SABR (beta = 1) to the one-year smile of chapter 9's market surface."""
    t = 1.0
    theta = (0.20 - 0.06 * math.exp(-t / 0.5)) ** 2 * t
    ks = np.arange(70.0, 130.01, 5.0)
    vols = np.array([math.sqrt(float(ssvi(math.log(k / 100), theta, -0.6, 1.0, 0.45)) / t) for k in ks])
    atm = float(np.sqrt(float(ssvi(0.0, theta, -0.6, 1.0, 0.45)) / t))
    (a, rho, nu), rmse = calibrate(100.0, t, ks, vols, 1.0, atm)
    fitted = np.array([hagan_lognormal(100.0, k, t, a, 1.0, rho, nu) for k in ks])
    return {"alpha": a, "rho": rho, "nu": nu, "rmse": rmse, "ks": ks, "market": vols, "fitted": fitted,
            "max_err": float(np.max(np.abs(fitted - vols)))}


def wing_density(t: float = 10.0, nu: float = 0.6, rho: float = -0.3, beta: float = 0.5):
    """Breeden-Litzenberger density of Hagan's prices at a long expiry: negative at low strikes."""
    a = alpha_from_atm(F0, t, 0.20, beta, rho, nu)
    ks = np.linspace(0.0010, 0.03, 300)
    c = np.array([black(F0, k, t, 1.0, hagan_lognormal(F0, k, t, a, beta, rho, nu), "C") for k in ks])
    h = ks[1] - ks[0]
    dens = (c[2:] - 2 * c[1:-1] + c[:-2]) / (h * h)
    return ks[1:-1], dens


def normal_smile(ks=None):
    ks = np.linspace(0.015, 0.05, 36) if ks is None else ks
    return [(k, normal_vol(F0, k, T, ALPHA, BETA, RHO, NU)) for k in ks]


def hedge_experiment(n: int = 200_000):
    d = deltas(F0, F0, T, ALPHA, BETA, RHO, NU)
    e = one_day_hedge_errors(F0, F0, T, ALPHA, BETA, RHO, NU, n=n)
    return {"deltas": d, "sd": e, "var_ratio": {k: (v / e["black"]) ** 2 for k, v in e.items()}}


def delta_curves(ks=None):
    ks = np.linspace(0.02, 0.045, 26) if ks is None else ks
    return [(k, deltas(F0, k, T, ALPHA, BETA, RHO, NU)) for k in ks]
