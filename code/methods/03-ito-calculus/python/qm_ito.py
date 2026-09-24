"""Chapter 3 of Book 4: Ito calculus.

Left-point, right-point and midpoint sums of the integral of W against itself; a trend rule
backtested honestly (next bar) and with look-ahead (same bar) on a pure random walk, with the
covariation that separates them; the mean and median of geometric Brownian motion."""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/stochint"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/mcengine"))
from firm_mcengine import bridge_paths
from firm_stochint import covariation, gains, riemann_sums, same_bar_gains

SIG_D, LOOKBACK, YEAR = 0.01, 20, 252            # daily volatility of the log price, MA window, days


def sums_table(levels: int = 16, seed: int = 3) -> tuple[float, list[tuple]]:
    """Left, right and midpoint sums of int_0^1 W dW on one path sampled at 2^k points."""
    w = bridge_paths(1, levels, 1.0, seed)[0]
    rows = []
    for k in range(2, levels + 1):
        sub = w[:: 2 ** (levels - k)]
        rows.append((2**k, riemann_sums(lambda x: x, sub, "left"), riemann_sums(lambda x: x, sub, "right"),
                     riemann_sums(lambda x: x, sub, "mid")))
    return float(w[-1]), rows


def trend_signal(s: np.ndarray, L: int = LOOKBACK) -> np.ndarray:
    """theta_t = (S_t - MA_L(t)) / sd, scaled to unit variance under a random walk; zero while
    the window fills."""
    c = np.cumsum(np.concatenate([[0.0], s]))
    ma = np.full(s.size, np.nan)
    ma[L - 1:] = (c[L:] - c[:-L]) / L
    scale = SIG_D * math.sqrt(sum((m / L) ** 2 for m in range(1, L)))
    th = (s - ma) / scale
    th[: L - 1] = 0.0
    return th


def spurious_mean(L: int = LOOKBACK, sig: float = SIG_D) -> float:
    """E[theta_t dS_t] for the same-bar rule on a random walk: (L-1)/L sig / sqrt(sum (m/L)^2)."""
    return (L - 1) / L * sig / math.sqrt(sum((m / L) ** 2 for m in range(1, L)))


def backtest(days: int = 2520, seed: int = 1, L: int = LOOKBACK) -> dict:
    """One random-walk history of log prices; the trend rule's same-bar and next-bar P&L."""
    rng = np.random.default_rng(seed)
    s = np.concatenate([[0.0], np.cumsum(SIG_D * rng.standard_normal(days))])
    th = trend_signal(s, L)
    honest = gains(th, s)
    cheat = same_bar_gains(th, s)
    cov = covariation(th, s)

    def sharpe(cum):
        d = np.diff(cum)[L:]
        return float(d.mean() / d.std() * math.sqrt(YEAR))

    return {"s": s, "theta": th, "honest": honest, "cheat": cheat, "cov": cov,
            "sr_honest": sharpe(honest), "sr_cheat": sharpe(cheat)}


def sharpe_distribution(n: int = 400, days: int = 2520, L: int = LOOKBACK) -> dict:
    """Same-bar and next-bar Sharpe ratios over n independent ten-year random walks."""
    sc = np.array([backtest(days, seed=1000 + i, L=L)["sr_cheat"] for i in range(n)])
    sh = np.array([backtest(days, seed=1000 + i, L=L)["sr_honest"] for i in range(n)])
    return {"cheat_mean": float(sc.mean()), "cheat_sd": float(sc.std()),
            "honest_mean": float(sh.mean()), "honest_sd": float(sh.std())}


def spurious_sharpe_theory(L: int = LOOKBACK) -> float:
    """Annualised Sharpe of the same-bar P&L: mean over standard deviation of theta_t dS_t.

    theta_t = a Z + sqrt(1 - a^2) Y with dS_t = sig Z, Y independent of Z, a = corr(theta_t, dS_t):
    E[theta dS] = a sig and E[(theta dS)^2] = sig^2 (3 a^2 + 1 - a^2), so the daily Sharpe ratio
    is a / sqrt(1 + a^2)."""
    a = spurious_mean(L) / SIG_D
    return a / math.sqrt(1 + a * a) * math.sqrt(YEAR)


def gbm_quantiles(mu: float = 0.10, sigma: float = 0.40, years: int = 10, n: int = 100_000, seed: int = 4) -> list:
    """Mean, median and 10th/90th percentiles of S_t/S_0 for geometric Brownian motion, simulated
    exactly each year, with the formulas exp(mu t) and exp((mu - sigma^2/2) t)."""
    rng = np.random.default_rng(seed)
    logs = np.cumsum((mu - 0.5 * sigma**2) + sigma * rng.standard_normal((n, years)), axis=1)
    rows = [(0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0)]
    for t in range(1, years + 1):
        x = np.exp(logs[:, t - 1])
        rows.append((t, float(x.mean()), math.exp(mu * t), float(np.median(x)), math.exp((mu - 0.5 * sigma**2) * t),
                     float(np.quantile(x, 0.1)), float(np.quantile(x, 0.9))))
    return rows


def ito_check(n: int = 2**14, seed: int = 5, mu: float = 0.10, sigma: float = 0.40) -> dict:
    """Ito's formula pathwise: ln S_T from the path equals the integral of dS/S minus half the
    quadratic variation of S over S^2, to discretisation error."""
    rng = np.random.default_rng(seed)
    dt = 1.0 / n
    dw = math.sqrt(dt) * rng.standard_normal(n)
    s = np.concatenate([[1.0], np.cumprod(1 + mu * dt + sigma * dw)])
    lhs = math.log(s[-1])
    ds = np.diff(s)
    rhs = float(np.sum(ds / s[:-1]) - 0.5 * np.sum((ds / s[:-1]) ** 2))
    naive = float(np.sum(ds / s[:-1]))
    return {"log": lhs, "ito": rhs, "naive": naive}
