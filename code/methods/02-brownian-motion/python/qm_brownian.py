"""Chapter 2 of Book 4: Brownian motion.

Sample paths and the square-root envelope, a reflected path, the stop-loss of the hook and weekend
problem (continuous monitoring, daily closes, the Broadie-Glasserman-Kou shift and the Brownian-
bridge correction), and the quadratic variation of a path sampled ever more finely."""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/mcengine"))
from firm_mcengine import bridge_crossing_probability, bridge_paths, brownian_paths

SIGMA, DAYS, YEAR, STOP = 0.30, 21, 252, 0.02       # volatility, horizon in days, days a year, 2% stop
BETA_BGK = 0.5826                                    # -zeta(1/2) / sqrt(2 pi), Broadie-Glasserman-Kou


def Phi(x: float) -> float:
    return 0.5 * math.erfc(-x / math.sqrt(2))


def touch_probability(b: float, sigma: float, T: float, mu: float = 0.0) -> float:
    """P(min_{t <= T} (mu t + sigma W_t) <= b) for b < 0: reflection principle with drift."""
    s = sigma * math.sqrt(T)
    return Phi((b - mu * T) / s) + math.exp(2 * mu * b / sigma**2) * Phi((b + mu * T) / s)


def bgk_probability(b: float, sigma: float, T: float, dt: float) -> float:
    """Discrete-monitoring approximation: the continuous formula with the barrier moved away from
    the start by beta sigma sqrt(dt)."""
    return touch_probability(b - BETA_BGK * sigma * math.sqrt(dt), sigma, T)


def simulate_touch(b: float, sigma: float, days: int, per_day: int, n_paths: int, seed: int,
                   bridge: bool = False) -> tuple[float, float]:
    """Monte Carlo probability that the log price (driftless, volatility sigma) is at or below b at
    one of `per_day` equally spaced observations a day; with bridge=True, each interval's
    crossing probability is added analytically (the Brownian-bridge correction). Returns the
    estimate and its standard error."""
    n = days * per_day
    dt = 1.0 / (YEAR * per_day)
    x = sigma * brownian_paths(n_paths, n, n * dt, seed)          # log price minus its start
    hit_grid = (x <= b).any(axis=1)
    if not bridge:
        est = hit_grid.astype(float)
    else:
        p_cross = bridge_crossing_probability(x[:, :-1], x[:, 1:], b, sigma**2 * dt)
        est = 1.0 - np.prod(1.0 - p_cross, axis=1)
    return float(est.mean()), float(est.std() / math.sqrt(n_paths))


def stop_problem() -> dict:
    b = math.log(1 - STOP)
    T = DAYS / YEAR
    s = SIGMA * math.sqrt(T)
    out = {"b": b, "s": s, "p_end": Phi(b / s), "p_touch": touch_probability(b, SIGMA, T)}
    out["p_touch_drift"] = touch_probability(b, SIGMA, T, mu=-0.5 * SIGMA**2)
    out["p_daily_sim"], out["se_daily"] = simulate_touch(b, SIGMA, DAYS, 1, 200_000, seed=21)
    out["shift"] = BETA_BGK * SIGMA * math.sqrt(1 / YEAR)
    out["p_bgk_daily"] = bgk_probability(b, SIGMA, T, 1 / YEAR)
    out["p_q15_sim"], _ = simulate_touch(b, SIGMA, DAYS, 26, 100_000, seed=22)
    out["p_bgk_q15"] = bgk_probability(b, SIGMA, T, 1 / (YEAR * 26))
    out["p_cross_1pct"] = float(bridge_crossing_probability(0.01, 0.01, 0.0, SIGMA**2 / YEAR))
    out["p_bridge_sim"], out["se_bridge"] = simulate_touch(b, SIGMA, DAYS, 1, 200_000, seed=23, bridge=True)
    out["p_touch_15vol"] = touch_probability(b, 0.15, T)
    out["p_touch_3m"] = touch_probability(b, SIGMA, 63 / YEAR)
    out["p_bgk_daily_3m"] = bgk_probability(b, SIGMA, 63 / YEAR, 1 / YEAR)
    return out


def stop_table(dists=(0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10)) -> list[tuple]:
    """Probability of touching a stop within 21 days: continuous formula, daily closes simulated,
    daily closes by the BGK shift, and daily closes with the bridge correction."""
    T = DAYS / YEAR
    rows = []
    for i, d in enumerate(dists):
        b = math.log(1 - d)
        daily, _ = simulate_touch(b, SIGMA, DAYS, 1, 40_000, seed=100 + i)
        brid, _ = simulate_touch(b, SIGMA, DAYS, 1, 40_000, seed=200 + i, bridge=True)
        rows.append((100 * d, touch_probability(b, SIGMA, T), daily, bgk_probability(b, SIGMA, T, 1 / YEAR), brid))
    return rows


def convergence_table(b: float = math.log(0.98), per_days=(1, 4, 16, 64)) -> list[tuple]:
    """Time-step study: the discretely monitored probability rises toward the continuous one as the
    grid is refined (a factor of four each time)."""
    return [(k, simulate_touch(b, SIGMA, DAYS, k, 40_000, seed=300 + k)[0]) for k in per_days]


def envelope_paths(n: int = 6, steps: int = 250, seed: int = 5) -> np.ndarray:
    return brownian_paths(n, steps, 1.0, seed)


def reflection_example(level: float = 0.6, steps: int = 500, seed: int = 8) -> dict:
    """First seeded path that reaches `level` before t = 1; its reflection after the hitting time."""
    for k in range(seed, seed + 500):
        w = brownian_paths(1, steps, 1.0, k)[0]
        idx = np.flatnonzero(w >= level)
        if idx.size and idx[0] < 0.7 * steps and w[-1] < level:
            tau = idx[0]
            refl = w.copy()
            refl[tau:] = 2 * w[tau] - w[tau:]
            return {"seed": k, "t": np.linspace(0, 1, steps + 1), "w": w, "refl": refl, "tau": tau / steps}
    raise RuntimeError("no path found")


def qv_table(levels: int = 16, seed: int = 9) -> list[tuple]:
    """Realised quadratic variation and total variation of one Brownian path on [0, 1], sampled at
    2^k points for k = 2..levels (the fine path is built once, by the bridge construction)."""
    w = bridge_paths(1, levels, 1.0, seed)[0]
    rows = []
    for k in range(2, levels + 1):
        sub = w[:: 2 ** (levels - k)]
        d = np.diff(sub)
        rows.append((2**k, float(d @ d), float(np.abs(d).sum())))
    return rows
