"""Rough volatility and forward variance (Book 5, Chapter 12): the roughness of volatility paths, the
forward-variance curve of chapter 9's surface, Bergomi's exponential kernel against the rough power law, the
at-the-money skew term structure, the VIX in rough Bergomi, and a path-dependent volatility.
Zero rates and dividends throughout; forward 1 (or 100 for chapter 9's surface)."""
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for comp in ("bs", "svi", "heston", "fwdvar"):
    sys.path.insert(0, str(ROOT / f"code/firm/{comp}"))
sys.path.insert(0, str(ROOT / "code/derivatives/10-stochastic-volatility/python"))
from dv_heston import calibration  # noqa: E402
from firm_bs import implied_vol  # noqa: E402
from firm_fwdvar import (  # noqa: E402
    ForwardVarianceCurve,
    _chol,
    _g_ratio,
    atm_skew,
    fbm,
    log_strip_variance,
    power_law_fit,
    rbergomi_smile,
    rbergomi_vix,
    roughness,
    structure_function,
)
from firm_heston import implied_vols  # noqa: E402
from firm_svi import ssvi  # noqa: E402

# Illustrative rough Bergomi parameters (not a calibration): H, eta, rho and a flat forward variance.
H, ETA, RHO, XI0 = 0.10, 1.9, -0.9, 0.04
TENORS = (1 / 52, 2 / 52, 1 / 12, 2 / 12, 0.25, 0.5, 1.0, 2.0)
LAGS = range(1, 31)
NOISE = 0.5 * math.sqrt(2 / 78)

# Published estimates of H (zeta_2 / 2), Gatheral, Jaisson and Rosenbaum (2014), Table B.1, Oxford-Man
# realised-variance library.
PUBLISHED_H = {"SPX": 0.124, "FTSE": 0.131, "N225": 0.132, "DAX": 0.136, "RUT": 0.111, "AORD": 0.075,
               "DJI": 0.114, "IXIC": 0.135, "CAC": 0.141, "HSI": 0.080, "KS11": 0.134, "AEX": 0.149,
               "SSMI": 0.158, "IBEX": 0.136, "NSEI": 0.111, "MXX": 0.075, "BVSP": 0.120, "TSX": 0.102,
               "SX5E": 0.123, "STI": 0.113, "MIB": 0.134}


# ---------------------------------------------------------------- roughness
def log_vol_paths(n: int = 2000, seed: int = 12) -> dict[str, np.ndarray]:
    """Daily log-volatility, n days: a rough path (fBM, H = 0.1, 0.3 of log-vol after a year) and a classical
    one (Ornstein-Uhlenbeck, mean reversion 2 a year, the same stationary spread as the rough path at a year),
    plus the classical path observed with an estimation error: a realised variance from n = 78 five-minute
    returns has a relative standard error of about sqrt(2 / n) = 0.16, so its log volatility is off by about
    half of that, 0.08."""
    dt = 1 / 252
    rough = math.log(0.2) + 0.3 * fbm(n, 0.1, seed, dt)
    rng = np.random.default_rng(seed + 1)
    kappa, sd = 2.0, 0.3 / math.sqrt(1 - math.exp(-2 * 2.0))
    ou = np.empty(n)
    ou[0] = math.log(0.2)
    a = math.exp(-kappa * dt)
    for i in range(1, n):
        ou[i] = math.log(0.2) + a * (ou[i - 1] - math.log(0.2)) + sd * math.sqrt(1 - a * a) * rng.standard_normal()
    noisy = ou + NOISE * rng.standard_normal(n)
    return {"rough": rough, "ou": ou, "noisy": noisy}


def roughness_table(paths=None) -> dict[str, float]:
    paths = log_vol_paths() if paths is None else paths
    return {k: roughness(x, LAGS) for k, x in paths.items()}


def structure_curves(paths=None) -> dict[str, np.ndarray]:
    paths = log_vol_paths() if paths is None else paths
    return {k: structure_function(x, list(LAGS)) for k, x in paths.items()}


# ---------------------------------------------------------------- chapter 9's surface and its variance curve
def market_vol(k: float, t: float) -> float:
    """Chapter 9's market at log-moneyness k: SSVI with rho -0.6, eta 1.0, gamma 0.45."""
    theta = (0.20 - 0.06 * math.exp(-t / 0.5)) ** 2 * t
    return math.sqrt(float(ssvi(k, theta, -0.6, 1.0, 0.45)) / t)


def variance_curve(tenors=(1 / 12, 0.25, 0.5, 1.0, 2.0)) -> tuple[ForwardVarianceCurve, list[dict]]:
    """Variance-swap volatility from each expiry's log-contract strip, the at-the-money volatility, and the
    forward-variance curve built on them."""
    rows = []
    for t in tenors:
        vs = math.sqrt(log_strip_variance(lambda k, t=t: market_vol(k, t), t))
        rows.append({"t": t, "atm": market_vol(0.0, t), "vs": vs})
    curve = ForwardVarianceCurve.from_vs_vols(tenors, [r["vs"] for r in rows])
    for r in rows:
        r["fwd_vol"] = math.sqrt(curve.xi(r["t"]))
    return curve, rows


# ---------------------------------------------------------------- kernels: Bergomi against rough
def rough_kernel(tau, eta: float = ETA, hurst: float = H):
    """Instantaneous volatility of the forward variance xi_t(t + tau) in rough Bergomi."""
    return eta * math.sqrt(2 * hurst) * np.asarray(tau, float) ** (hurst - 0.5)


def bergomi_match(t1: float = 1 / 12, t2: float = 1.0) -> tuple[float, float]:
    """(omega, k) of a one-factor Bergomi kernel omega e^(-k tau) equal to the rough kernel at t1 and t2."""
    r1, r2 = rough_kernel(t1), rough_kernel(t2)
    k = math.log(r1 / r2) / (t2 - t1)
    return float(r1 * math.exp(k * t1)), float(k)


def vol_paths(days: int = 252, seed: int = 5) -> dict[str, np.ndarray]:
    """One year of daily instantaneous volatility in rough Bergomi and in the matched one-factor Bergomi,
    driven by the same Brownian increments."""
    dt = 1 / 252
    t = dt * np.arange(1, days + 1)
    lo = np.minimum.outer(t, t)
    cyy = lo ** (2 * H) * _g_ratio(np.maximum.outer(t, t) / lo, H)
    c = math.sqrt(2 * H) / (H + 0.5)
    cyw = c * (t[:, None] ** (H + 0.5) - (t[:, None] - lo) ** (H + 0.5))
    low = _chol(np.block([[cyy, cyw], [cyw.T, lo]]))
    g = low @ np.random.default_rng(seed).standard_normal(2 * days)
    y, w = g[:days], g[days:]
    rough = np.sqrt(XI0 * np.exp(ETA * y - 0.5 * ETA ** 2 * t ** (2 * H)))
    omega, k = bergomi_match()
    x, var_x = np.zeros(days), np.zeros(days)
    dw = np.diff(np.concatenate([[0.0], w]))
    xs = 0.0
    for i in range(days):
        xs = xs * math.exp(-k * dt) + dw[i]
        x[i] = xs
        var_x[i] = (1 - math.exp(-2 * k * t[i])) / (2 * k)
    berg = np.sqrt(XI0 * np.exp(omega * x - 0.5 * omega ** 2 * var_x))
    return {"t": t, "rough": rough, "bergomi": berg}


# ---------------------------------------------------------------- the skew term structure
def market_skews(tenors=TENORS) -> np.ndarray:
    return np.array([atm_skew(lambda ks, t: np.array([market_vol(k, t) for k in ks]), t) for t in tenors])


def rbergomi_skews(tenors=TENORS, hurst: float = H, eta: float = ETA, rho: float = RHO) -> np.ndarray:
    return np.array([atm_skew(lambda ks, t: rbergomi_smile(XI0, hurst, eta, rho, t, ks), t) for t in tenors])


def heston_skews(tenors=TENORS) -> np.ndarray:
    m = calibration()[0]
    return np.array([atm_skew(lambda ks, t: implied_vols(m, 100.0, 100.0 * np.exp(ks), t), t) for t in tenors])


def skew_term() -> dict:
    mk, rb, hs = market_skews(), rbergomi_skews(), heston_skews()
    fits = {name: power_law_fit(TENORS, s) for name, s in (("market", mk), ("rbergomi", rb), ("heston", hs))}
    short = {name: power_law_fit(TENORS[:4], s[:4]) for name, s in (("market", mk), ("rbergomi", rb), ("heston", hs))}
    return {"market": mk, "rbergomi": rb, "heston": hs, "fits": fits, "short": short}


# ---------------------------------------------------------------- the VIX in rough Bergomi
def vix_smile(t: float = 1 / 12, rel_strikes=(0.8, 0.9, 1.0, 1.1, 1.2, 1.4, 1.6)) -> dict:
    vix = rbergomi_vix(XI0, H, ETA, t)
    fut = float(vix.mean())
    vols = []
    for m in rel_strikes:
        price = float(np.maximum(vix - m * fut, 0.0).mean())
        vols.append(implied_vol(price, fut, m * fut, t, 1.0, "C"))
    return {"future": fut, "vix2": float((vix ** 2).mean()), "strikes": np.array(rel_strikes), "vols": np.array(vols)}


# ---------------------------------------------------------------- a path-dependent volatility
PDV = {"beta0": 0.04, "beta1": -0.06, "beta2": 0.65, "lam1": 25.0, "lam2": 15.0}


def pdv_vol(returns, sq_returns=None, p=PDV, dt: float = 1 / 252) -> np.ndarray:
    """sigma_t = beta0 + beta1 R1 + beta2 sqrt(R2): R1 an exponentially weighted average of past returns and R2
    of past squared returns, both per unit time (weights e^(-lam tau) summing to one), started at the calm
    fixed point sigma* = beta0 / (1 - beta2) with R1 = 0 and R2 = sigma*^2. sq_returns defaults to the squared
    returns. Returns the volatility after each day."""
    s_star = p["beta0"] / (1 - p["beta2"])
    sq_returns = [r * r for r in returns] if sq_returns is None else sq_returns
    a1, a2 = math.exp(-p["lam1"] * dt), math.exp(-p["lam2"] * dt)
    r1, r2 = 0.0, s_star ** 2
    out = []
    for r, r_sq in zip(returns, sq_returns, strict=True):
        r1 = a1 * r1 + (1 - a1) * r / dt
        r2 = a2 * r2 + (1 - a2) * r_sq / dt
        out.append(p["beta0"] + p["beta1"] * r1 + p["beta2"] * math.sqrt(r2))
    return np.array(out)


def pdv_shock(shock: float, days_after: int = 40, p=PDV, dt: float = 1 / 252) -> np.ndarray:
    """Volatility after one return `shock` from the calm state, then days of ordinary returns (mean zero,
    squared return sigma*^2 dt): the calm level first, then the shock day and its decay."""
    s_star = p["beta0"] / (1 - p["beta2"])
    rets = [0.0, shock] + [0.0] * days_after
    sq = [s_star ** 2 * dt, shock * shock] + [s_star ** 2 * dt] * days_after
    return pdv_vol(rets, sq, p, dt)
