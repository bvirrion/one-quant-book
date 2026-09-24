"""Multi-asset options (build of Book 5, Chapter 17): correlated paths (Cholesky, per-asset volatility functions,
quanto drift), an equicorrelated generator whose correlation may depend on the state (local correlation),
basket, worst-of and best-of payoffs, moment-matched baskets, implied and realised correlation, and the quanto
and composite adjustments.

Paths have shape (n_paths, n_dates + 1, n_assets); column 0 is today.
"""
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "bs"))
from firm_bs import black  # noqa: E402


# ---------------------------------------------------------------- paths
def correlated_paths(s0, vols, corr, times, r: float = 0.0, q=0.0, n_paths: int = 100_000, seed: int = 17,
                     quanto: tuple[float, np.ndarray] | None = None, steps_per_date: int = 1) -> np.ndarray:
    """Lognormal paths with constant correlation matrix corr. vols[i] is a number or a function sigma_i(t, S_i)
    (a local volatility). quanto = (sigma_x, rho_sx): each asset's drift is lowered by rho_i sigma_i sigma_x,
    the drift of a foreign asset under the domestic measure when paid at a fixed exchange rate."""
    s0 = np.asarray(s0, float)
    m = len(s0)
    q = np.broadcast_to(np.asarray(q, float), (m,))
    low = np.linalg.cholesky(np.asarray(corr, float))
    rng = np.random.default_rng(seed)
    half = n_paths // 2
    x = np.tile(np.log(s0), (2 * half, 1))
    out = [np.exp(x)]
    now = 0.0
    for target in np.asarray(times, float):
        dt = (target - now) / steps_per_date
        for j in range(steps_per_date):
            z = rng.standard_normal((half, m))
            z = np.vstack([z, -z]) @ low.T
            t_mid = now + (j + 0.5) * dt
            sig = np.column_stack([v(t_mid, np.exp(x[:, i])) if callable(v) else np.full(2 * half, v)
                                   for i, v in enumerate(vols)])
            drift = r - q - 0.5 * sig * sig
            if quanto is not None:
                sx, rho_sx = quanto
                drift = drift - np.asarray(rho_sx, float) * sig * sx
            x = x + drift * dt + sig * math.sqrt(dt) * z
        out.append(np.exp(x))
        now = target
    return np.stack(out, axis=1)


def local_correlation_paths(s0, vols, weights, rho_fn, times, n_paths: int = 100_000, seed: int = 17,
                            steps_per_date: int = 21) -> np.ndarray:
    """Equicorrelated lognormal assets (zero rates) whose common correlation rho_fn(t, x) depends on the index's
    log-moneyness x = ln(I_t / I_0), I = sum w_i S_i: each shock is sqrt(rho) Z + sqrt(1 - rho) Z_i."""
    s0, vols, w = (np.asarray(a, float) for a in (s0, vols, weights))
    m = len(s0)
    i0 = float(w @ s0)
    rng = np.random.default_rng(seed)
    half = n_paths // 2
    x = np.tile(np.log(s0), (2 * half, 1))
    out = [np.exp(x)]
    now = 0.0
    for target in np.asarray(times, float):
        dt = (target - now) / steps_per_date
        for j in range(steps_per_date):
            idx = np.exp(x) @ w
            rho = np.clip(rho_fn(now + (j + 0.5) * dt, np.log(idx / i0)), 0.0, 0.999)[:, None]
            zc = rng.standard_normal((half, 1))
            zi = rng.standard_normal((half, m))
            zc, zi = np.vstack([zc, -zc]), np.vstack([zi, -zi])
            z = np.sqrt(rho) * zc + np.sqrt(1 - rho) * zi
            x = x - 0.5 * vols * vols * dt + vols * math.sqrt(dt) * z
        out.append(np.exp(x))
        now = target
    return np.stack(out, axis=1)


def equicorrelation(m: int, rho: float) -> np.ndarray:
    return np.full((m, m), rho) + (1 - rho) * np.eye(m)


# ---------------------------------------------------------------- payoffs (at the last date, performance S_T / S_0)
def performances(paths: np.ndarray) -> np.ndarray:
    return paths[:, -1, :] / paths[:, 0, :]


def basket_payoff(paths: np.ndarray, weights, strike: float, right: str = "C") -> np.ndarray:
    b = performances(paths) @ np.asarray(weights, float)
    return np.maximum(b - strike, 0.0) if right == "C" else np.maximum(strike - b, 0.0)


def worst_of_payoff(paths: np.ndarray, strike: float, right: str = "P") -> np.ndarray:
    w = performances(paths).min(axis=1)
    return np.maximum(w - strike, 0.0) if right == "C" else np.maximum(strike - w, 0.0)


def best_of_payoff(paths: np.ndarray, strike: float, right: str = "C") -> np.ndarray:
    b = performances(paths).max(axis=1)
    return np.maximum(b - strike, 0.0) if right == "C" else np.maximum(strike - b, 0.0)


def worst_of_digital(paths: np.ndarray, level: float) -> np.ndarray:
    """Pays 1 if every asset ends at or above level times its start."""
    return (performances(paths).min(axis=1) >= level).astype(float)


# ---------------------------------------------------------------- closed forms and approximations
def basket_moment_match(weights, fwds, vols, corr, t: float, strike: float, df: float = 1.0,
                        right: str = "C") -> float:
    """Lognormal approximation of a basket sum w_i S_i: match its mean and second moment and price with Black."""
    w, f, v = (np.asarray(a, float) for a in (weights, fwds, vols))
    c = np.asarray(corr, float)
    m1 = float(w @ f)
    m2 = float((w * f) @ np.exp(c * np.outer(v, v) * t) @ (w * f))
    vol = math.sqrt(math.log(m2 / (m1 * m1)) / t)
    return black(m1, strike, t, df, vol, right)


def implied_correlation(index_vol: float, weights, vols) -> float:
    """The single correlation that makes the index variance equal sum_ij w_i w_j rho_ij sigma_i sigma_j."""
    w, v = np.asarray(weights, float), np.asarray(vols, float)
    own = float(np.sum((w * v) ** 2))
    cross = float(np.sum(w * v)) ** 2 - own
    return (index_vol ** 2 - own) / cross


def index_variance(weights, vols, rho: float) -> float:
    w, v = np.asarray(weights, float), np.asarray(vols, float)
    own = float(np.sum((w * v) ** 2))
    return own + rho * (float(np.sum(w * v)) ** 2 - own)


def realised_correlation(returns: np.ndarray, weights) -> float:
    """Weighted average pairwise correlation of an (n_days, n_assets) return matrix, sum_(i<j) w_i w_j rho_ij over
    sum_(i<j) w_i w_j: the quantity a correlation swap pays."""
    w = np.asarray(weights, float)
    c = np.corrcoef(returns, rowvar=False)
    ww = np.outer(w, w)
    iu = np.triu_indices(len(w), 1)
    return float(np.sum(ww[iu] * c[iu]) / np.sum(ww[iu]))


def quanto_forward(fwd: float, sigma_s: float, sigma_x: float, rho: float, t: float) -> float:
    """Forward of a foreign asset paid in domestic currency at a fixed rate: F e^(-rho sigma_S sigma_X T), rho the
    correlation between the asset and the exchange rate quoted as domestic per foreign."""
    return fwd * math.exp(-rho * sigma_s * sigma_x * t)


def composite_vol(sigma_s: float, sigma_x: float, rho: float) -> float:
    """Volatility of the foreign asset converted at the prevailing rate into domestic currency."""
    return math.sqrt(sigma_s ** 2 + sigma_x ** 2 + 2 * rho * sigma_s * sigma_x)
