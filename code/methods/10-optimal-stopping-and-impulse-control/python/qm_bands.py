"""Chapter 10 of Book 4: optimal stopping and impulse control.

The treasury desk's hedging band (fixed ticket fee, quadratic risk charge), its fourth-root law, the
cube-root law for proportional costs, both combined; and a take-profit threshold found by smooth
pasting and checked by backward induction on a grid."""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm/impulse"))
sys.path.insert(0, str(ROOT / "firm/dpsolve"))
from firm_dpsolve import backward_induction  # noqa: E402
from firm_impulse import (  # noqa: E402
    band_cost,
    optimal_band,
    optimal_fixed_band,
    optimal_proportional_band,
    simulate_band,
    stop_threshold_drift,
)

SIGMA = 20.0        # USD millions of exposure per square-root day, from client flows
GAMMA = 0.5         # USD of risk charge per (USD million)^2 per day
K = 300.0           # USD per hedge ticket
C = 25.0            # USD per USD million traded (0.25 bp)


def cost_curve(bs=None) -> list[tuple]:
    bs = np.linspace(8, 90, 83) if bs is None else bs
    return [(float(b), band_cost(b, 0.0, SIGMA, GAMMA, K)) for b in bs]


def daily_hedge_cost() -> float:
    """Hedge to zero once a day: one ticket plus the expected risk charge of a day's drift,
    gamma E[int_0^1 X^2 dt] = gamma sigma^2 / 2."""
    return K + GAMMA * SIGMA**2 / 2


def fee_table(fees=(50, 100, 200, 300, 600, 1200, 2400)) -> list[tuple]:
    return [(f, *optimal_fixed_band(SIGMA, GAMMA, f)) for f in fees]


def dp_stopping_check(mu=0.5, sigma=2.0, r=0.02, cost=5.0, h=0.05) -> dict:
    """Backward induction for the perpetual take-profit problem on a grid (long horizon, daily steps,
    three-point quadrature), against the smooth-pasting threshold."""
    b_star, theta = stop_threshold_drift(mu, sigma, r, cost)
    grid = np.arange(-40.0, 80.0 + h, h)
    dt = 1.0
    disc = math.exp(-r * dt)
    step = sigma * math.sqrt(3 * dt)

    def transition(t, x, u):
        nxt = x[..., None] + mu * dt + np.array([-step, 0.0, step])
        return nxt, disc * np.array([1 / 6, 2 / 3, 1 / 6])

    res = backward_induction(grid, np.array([0.0]), 1500, lambda t, x, u: 0.0 * x, transition,
                             lambda x: np.maximum(x - cost, 0.0), stop=lambda t, x: x - cost)
    stop0 = res["stop"][0]
    idx = int(np.argmax(stop0 & (grid > cost)))
    return {"b_star": b_star, "theta": theta, "b_grid": float(grid[idx]),
            "v_at_0": float(np.interp(0.0, grid, res["values"][0])),
            "v_theory_at_0": (b_star - cost) * math.exp(theta * (0.0 - b_star))}


def problem() -> dict:
    b_fix, c_fix = optimal_fixed_band(SIGMA, GAMMA, K)
    b_half, _ = optimal_fixed_band(SIGMA, GAMMA, K / 2)
    b_prop, c_prop = optimal_proportional_band(SIGMA, GAMMA, C)
    a_both, b_both, c_both = optimal_band(SIGMA, GAMMA, K, C)
    sim = simulate_band(b_fix, 0.0, SIGMA, GAMMA, K, 0.0, T=20_000.0, dt=1 / 390, seed=1)
    sim4 = simulate_band(b_fix, 0.0, SIGMA, GAMMA, K, 0.0, T=20_000.0, dt=1 / 1560, seed=2)
    return {
        "b_fix": b_fix, "cost_fix": c_fix, "trades_per_day": SIGMA**2 / b_fix**2,
        "daily_cost": daily_hedge_cost(), "saving": 1 - c_fix / daily_hedge_cost(),
        "b_half": b_half, "narrowing": 1 - b_half / b_fix,
        "b_prop": b_prop, "cost_prop": c_prop,
        "a_both": a_both, "b_both": b_both, "cost_both": c_both,
        "sim_cost": sim["avg_cost"], "sim_trades_per_day": sim["trades"] / 20_000.0,
        "sim4_cost": sim4["avg_cost"],
        "risk_share": GAMMA * b_fix**2 / 6 / c_fix,
    }
