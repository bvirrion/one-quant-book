"""Variance swaps and volatility derivatives (Book 5, Chapter 14): the strip on chapter 9's surface, the
index-style discrete number, volatility-swap convexity and volatility-index futures under the Heston model
calibrated in chapter 10, gamma swaps, and the log-contract hedge on paths with and without jumps.
Zero rates and dividends; spot and forward 100."""
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for comp in ("bs", "svi", "heston", "fwdvar", "jumps", "varswap"):
    sys.path.insert(0, str(ROOT / f"code/firm/{comp}"))
sys.path.insert(0, str(ROOT / "code/derivatives/10-stochastic-volatility/python"))
from dv_heston import calibration  # noqa: E402
from firm_bs import black, implied_vol  # noqa: E402
from firm_fwdvar import log_strip_variance  # noqa: E402
from firm_jumps import Merton  # noqa: E402
from firm_svi import ssvi  # noqa: E402
from firm_varswap import (  # noqa: E402
    heston_mean_variance,
    heston_vix_future,
    heston_vol_swap,
    index_variance,
    jump_error,
    log_payoff_strip,
    strip_from_vols,
)

F = 100.0
MONTH = 30 / 365
# The Merton model fitted to the one-month smile in chapter 13 (rounded).
MERTON = Merton(0.098, 3.16, -0.058, 0.046)


def market_vol_k(k: float, t: float) -> float:
    """Chapter 9's market at log-moneyness k."""
    theta = (0.20 - 0.06 * math.exp(-t / 0.5)) ** 2 * t
    return math.sqrt(float(ssvi(k, theta, -0.6, 1.0, 0.45)) / t)


def fair_variance(t: float) -> float:
    return log_strip_variance(lambda k: market_vol_k(k, t), t)


# ---------------------------------------------------------------- the strip
def contributions(t: float = 1.0, strikes=None) -> tuple[np.ndarray, np.ndarray]:
    """Each strike's share of the index-style variance (one-year expiry, strikes every 5 from 30 to 250)."""
    strikes = np.arange(30.0, 250.01, 5.0) if strikes is None else strikes
    k, c, p = strip_from_vols(lambda x: market_vol_k(x, t), F, t, strikes)
    q = np.where(k < F, p, c)
    q[k == F] = 0.5 * (c[k == F] + p[k == F])
    dk = np.full_like(k, k[1] - k[0])
    w = 2 / t * dk / k ** 2 * q
    return k, w / w.sum()


SPACINGS = (0.5, 1.0, 2.5)


def index_errors(t: float = MONTH) -> dict:
    """Index-style variance against the continuous strip, by strike spacing and by how far the strip reaches."""
    exact = fair_variance(t)
    out = {"exact_vol": math.sqrt(exact), "rows": []}
    for lo in (70.0, 80.0, 85.0, 90.0, 95.0):
        row = {"lo": lo}
        for dk in SPACINGS:
            ks = np.arange(lo, 2 * F - lo + 0.01, dk)
            k, c, p = strip_from_vols(lambda x: market_vol_k(x, t), F, t, ks)
            row[dk] = 100 * (math.sqrt(index_variance(k, c, p, F, t)) - math.sqrt(exact))
        out["rows"].append(row)
    return out


def replication_payoff(strikes=None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """-2 ln(S_T / F) against the payoff of a strip with strikes every 10 from 60 to 140."""
    strikes = np.arange(60.0, 140.01, 10.0) if strikes is None else strikes
    s = np.linspace(40.0, 170.0, 131)
    return s, -2 * np.log(s / F), log_payoff_strip(s, F, strikes)


def gamma_swap_strike(t: float = 1.0, n: int = 4001) -> float:
    """Fair gamma-swap strike (volatility units): (2 / (T S0)) int OTM(K) / K dK, spot 100."""
    width = max(1.0, 10.0 * market_vol_k(0.0, t) * math.sqrt(t))
    ks = np.linspace(-width, width, n)
    otm = np.array([black(1.0, math.exp(k), t, 1.0, market_vol_k(k, t), "P" if k < 0 else "C") for k in ks])
    f = otm                                    # OTM(K)/K dK = OTM(k) dk per unit forward
    return math.sqrt(2 / t * float(np.sum(0.5 * (f[1:] + f[:-1]) * np.diff(ks))))


# ---------------------------------------------------------------- Heston: volatility swaps and index futures
def heston_terms(tenors=(1 / 12, 0.25, 0.5, 1.0, 2.0, 3.0)) -> list[dict]:
    m = calibration()[0]
    rows = []
    for t in tenors:
        var_k = math.sqrt(heston_mean_variance(m.v0, m.kappa, m.vbar, t))
        vol_k = heston_vol_swap(m.v0, m.kappa, m.vbar, m.eta, t)
        rows.append({"t": t, "var": var_k, "vol": vol_k, "adj": var_k - vol_k,
                     "market_var": math.sqrt(fair_variance(t))})
    return rows


def vix_curve(months=range(0, 13)) -> list[dict]:
    m = calibration()[0]
    rows = []
    for mo in months:
        t = max(mo / 12, 1e-6)
        fut, fwd = heston_vix_future(m.v0, m.kappa, m.vbar, m.eta, t)
        rows.append({"t": mo / 12, "future": fut, "fwd": fwd})
    return rows


def vix_options(t: float = 0.25, rel=(0.8, 0.9, 1.0, 1.1, 1.25, 1.5, 1.75), n: int = 400_000,
                seed: int = 14) -> dict:
    """VIX options at T under Heston by exact simulation of v_T (a scaled non-central chi-square)."""
    m = calibration()[0]
    rng = np.random.default_rng(seed)
    c = m.eta ** 2 * (1 - math.exp(-m.kappa * t)) / (4 * m.kappa)
    d = 4 * m.kappa * m.vbar / m.eta ** 2
    lam = m.v0 * math.exp(-m.kappa * t) / c
    v_t = c * rng.noncentral_chisquare(d, lam, n)
    b = (1 - math.exp(-m.kappa * MONTH)) / (m.kappa * MONTH)
    vix = np.sqrt(m.vbar * (1 - b) + b * v_t)
    fut = float(vix.mean())
    vols = [implied_vol(float(np.maximum(vix - r * fut, 0).mean()), fut, r * fut, t, 1.0, "C") for r in rel]
    return {"future": fut, "rel": np.array(rel), "vols": np.array(vols)}


# ---------------------------------------------------------------- the hedge with and without jumps
def hedge_pnl(t: float = 0.25, days: int = 63, n: int = 100_000, seed: int = 14) -> dict:
    """Short a variance swap struck at the strip's variance and hold the replicating hedge (the static strip for
    -2 ln(S_T / F) and 2 / S_t shares rebalanced daily). Per path the P&L is the sum over days of
    jump_error(r) = 2 (e^r - 1 - r) - r^2, in variance units; reported in volatility points (divide by 2K)."""
    rng = np.random.default_rng(seed)
    dt = t / days
    kbar = math.exp(MERTON.mu + 0.5 * MERTON.delta ** 2) - 1
    total_var = MERTON.cumulants(1.0)[0]
    out = {}
    z = rng.standard_normal((n, days))
    nj = rng.poisson(MERTON.lam * dt, (n, days))
    jumps = nj * MERTON.mu + np.sqrt(nj) * MERTON.delta * rng.standard_normal((n, days))
    r_jump = (-0.5 * MERTON.sigma ** 2 - MERTON.lam * kbar) * dt + MERTON.sigma * math.sqrt(dt) * z + jumps
    vol = math.sqrt(total_var)
    r_diff = -0.5 * total_var * dt + vol * math.sqrt(dt) * z
    for name, r in (("diffusion", r_diff), ("jumps", r_jump)):
        var_pnl = np.sum(jump_error(r), axis=1) / t         # annualised variance units
        out[name] = 100 * var_pnl / (2 * vol)                # volatility points
        out[name + "_rv"] = np.sum(r * r, axis=1) / t
    out["vol"] = vol
    return out


def strip_bias_merton() -> dict:
    """Continuous-time gap between the variance swap's fair strike and the strip under Merton:
    E[RV] - strip = -lam E[jump_error(J)], by Gauss-Hermite quadrature over J."""
    z, w = np.polynomial.hermite_e.hermegauss(60)
    ej = float(np.sum(w * jump_error(MERTON.mu + MERTON.delta * z)) / math.sqrt(2 * math.pi))
    gap = -MERTON.lam * ej
    vol = math.sqrt(MERTON.cumulants(1.0)[0])
    return {"per_jump": ej, "gap_var": gap, "gap_vol_pts": 100 * gap / (2 * vol), "vol": vol,
            "cubic": (MERTON.mu ** 3 + 3 * MERTON.mu * MERTON.delta ** 2) / 3}
