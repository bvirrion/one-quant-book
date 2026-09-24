"""Value at risk and expected shortfall (build of One Quant Book 6, chapter 21).

Conventions: P&L positive is a gain; VaR and ES are reported as positive losses. Historical VaR at level a
is the k-th largest loss with k = ceil((1 - a) n) and ES the average of the k largest losses. EWMA
covariance with decay lambda (RiskMetrics: 0.94 for daily trading data). Filtered historical simulation
rescales each factor's past return by its EWMA volatility then and now. Parametric (delta-normal) VaR and ES,
Monte Carlo VaR with a user revaluation, delta-gamma approximation. Backtests: Kupiec's proportion of
failures, Christoffersen's independence test (likelihood ratios, chi-square with one degree of freedom),
and the Basel traffic light for 250 observations. Euler contributions of parametric VaR.
"""
import math
from collections.abc import Callable
from statistics import NormalDist

import numpy as np

ND = NormalDist()
# Basel (1996) traffic light, 250 observations: exceptions -> (zone, increase in the scaling factor)
TRAFFIC = {0: ("green", 0.0), 1: ("green", 0.0), 2: ("green", 0.0), 3: ("green", 0.0), 4: ("green", 0.0),
           5: ("yellow", 0.40), 6: ("yellow", 0.50), 7: ("yellow", 0.65), 8: ("yellow", 0.75), 9: ("yellow", 0.85)}


def hs_var_es(pnl: np.ndarray, alpha: float) -> tuple[float, float]:
    losses = np.sort(-np.asarray(pnl))[::-1]
    k = max(1, math.ceil((1.0 - alpha) * len(losses) - 1e-9))
    return float(losses[k - 1]), float(losses[:k].mean())


def ewma_cov(x: np.ndarray, lam: float = 0.94) -> np.ndarray:
    """EWMA covariance of the rows of x (oldest first), zero mean, weights normalised."""
    n = x.shape[0]
    w = (1 - lam) * lam ** np.arange(n - 1, -1, -1)
    w = w / w.sum()
    return (x * w[:, None]).T @ x


def ewma_vol_path(x: np.ndarray, lam: float = 0.94, seed_obs: int = 20) -> np.ndarray:
    """EWMA volatility of each column before each observation (sigma_t uses returns up to t-1)."""
    v = np.empty_like(x)
    s2 = x[:seed_obs].var(axis=0) + 1e-18
    for t in range(x.shape[0]):
        v[t] = np.sqrt(s2)
        s2 = lam * s2 + (1 - lam) * x[t] ** 2
    return v, np.sqrt(s2)


def fhs_scenarios(x: np.ndarray, lam: float = 0.94) -> np.ndarray:
    """Filtered historical scenarios: each past return rescaled by (current vol / vol then)."""
    past, now = ewma_vol_path(x, lam)
    return x / past * now


def parametric_var_es(delta: np.ndarray, cov: np.ndarray, alpha: float) -> tuple[float, float]:
    s = float(math.sqrt(delta @ cov @ delta))
    z = ND.inv_cdf(alpha)
    return z * s, ND.pdf(z) / (1 - alpha) * s


def euler_var(delta: np.ndarray, cov: np.ndarray, alpha: float) -> np.ndarray:
    """Contributions of each factor to parametric VaR (they add up to the VaR)."""
    s = math.sqrt(delta @ cov @ delta)
    return ND.inv_cdf(alpha) * delta * (cov @ delta) / s


def mc_var_es(revalue: Callable[[np.ndarray], np.ndarray], cov: np.ndarray, alpha: float, n: int = 100_000,
              seed: int = 7) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    z = rng.standard_normal((n // 2, cov.shape[0]))
    x = np.concatenate([z, -z]) @ np.linalg.cholesky(cov).T
    return hs_var_es(revalue(x), alpha)


def delta_gamma(delta: np.ndarray, gamma: np.ndarray, x: np.ndarray) -> np.ndarray:
    return x @ delta + 0.5 * np.einsum("ni,ij,nj->n", x, gamma, x)


def kupiec(n: int, exceptions: int, p: float) -> tuple[float, float]:
    """Likelihood ratio of the proportion of failures and its chi-square(1) p-value."""
    x = exceptions

    def ll(q: float) -> float:
        return (n - x) * math.log(1 - q) + (x * math.log(q) if x else 0.0)

    phat = x / n
    lr = -2 * (ll(p) - (ll(phat) if 0 < phat < 1 else 0.0))
    return lr, math.erfc(math.sqrt(max(lr, 0.0) / 2))


def christoffersen(hits: np.ndarray) -> tuple[float, float]:
    """Independence test: do exceptions cluster (first-order Markov against independence)?"""
    h = np.asarray(hits, dtype=int)
    a, b = h[:-1], h[1:]
    n00, n01 = int(((a == 0) & (b == 0)).sum()), int(((a == 0) & (b == 1)).sum())
    n10, n11 = int(((a == 1) & (b == 0)).sum()), int(((a == 1) & (b == 1)).sum())
    p01 = n01 / max(n00 + n01, 1)
    p11 = n11 / max(n10 + n11, 1)
    p = (n01 + n11) / max(n00 + n01 + n10 + n11, 1)

    def ll(q, k0, k1):
        return (k0 * math.log(1 - q) if k0 else 0.0) + (k1 * math.log(q) if k1 else 0.0) if 0 < q < 1 else 0.0

    lr = -2 * (ll(p, n00 + n10, n01 + n11) - ll(p01, n00, n01) - ll(p11, n10, n11))
    return lr, math.erfc(math.sqrt(max(lr, 0.0) / 2))


def traffic_light(exceptions: int) -> tuple[str, float]:
    """Zone and increase in the scaling factor of 3 for 250 daily observations."""
    return TRAFFIC.get(exceptions, ("red", 1.0))


def sqrt_time(var_1d: float, days: int) -> float:
    return var_1d * math.sqrt(days)
