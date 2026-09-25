"""firm.swapspread -- swap-spread trades and the balance sheet they use (build of One Quant Book 9, chapter 12).

A synthetic ten-year swap spread (swap rate minus Treasury yield, in basis points): before a regulation date it
sits near a small positive credit-and-liquidity premium; after it, dealers charge for balance sheet, the spread
falls to minus that cost and dips further around quarter-ends (most at year-end), with a mean-reverting noise
throughout. The long-swap-spread trade buys the Treasury, finances it in repo and pays fixed in the swap (receiving
a floating rate that stays a fixed gap above repo); it earns the Treasury yield over the swap rate as carry and
gains when the spread widens. A balance-sheet charge, capital held against the Treasury position times a hurdle
rate, is a running cost on the notional. NumPy only.

API (stable):
    SwapConfig(...)                            parameters (seed 113)
    simulate_spread(cfg)                       dict of the daily spread (bp), the balance-sheet cost and quarter-ends
    long_spread(s, cfg, start, days, charge)   daily P&L parts per unit notional: carry, marks, float-repo, charge
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

YEAR = 252


@dataclass(frozen=True)
class SwapConfig:
    days: int = 10 * YEAR
    seed: int = 113
    premium: float = 10.0         # spread before the regulation (bp)
    regulation: int = 3 * YEAR    # day balance sheet starts to be charged
    ramp: int = YEAR              # the charge phases in over this many days
    bs_cost: float = 45.0         # balance-sheet cost reflected in the spread after (bp a year)
    qe_dip: float = 6.0           # extra dip at a quarter-end (bp), twice at year-end ...
    qe_days: int = 5              # ... over the last days of the quarter
    noise_sd: float = 8.0         # sd of the spread's noise (bp)
    noise_hl: float = 60.0        # its half-life (days)
    dv01: float = 8.5             # DV01 of the ten-year position per unit notional (bp of notional per bp)
    float_repo: float = 5.0       # floating rate received minus repo paid (bp a year)
    leverage_ratio: float = 0.05  # capital held against the Treasury notional ...
    hurdle: float = 0.10          # ... at this required return: a charge of 50 bp a year


def simulate_spread(cfg: SwapConfig | None = None) -> dict:
    cfg = cfg or SwapConfig()
    rng = np.random.default_rng(cfg.seed)
    T = cfg.days
    t = np.arange(T)
    phase = np.clip((t - cfg.regulation) / cfg.ramp, 0.0, 1.0)
    cost = cfg.bs_cost * phase
    q_end = (t % (YEAR // 4)) >= (YEAR // 4 - cfg.qe_days)
    y_end = (t % YEAR) >= (YEAR - cfg.qe_days)
    dip = cfg.qe_dip * phase * (q_end.astype(float) + y_end.astype(float))
    phi = 0.5 ** (1 / cfg.noise_hl)
    u = np.empty(T)
    u[0] = cfg.noise_sd * rng.standard_normal()
    for i in range(1, T):
        u[i] = phi * u[i - 1] + cfg.noise_sd * math.sqrt(1 - phi * phi) * rng.standard_normal()
    spread = cfg.premium * (1 - phase) - cost - dip + u
    return {"spread": spread, "cost": cost, "dip": dip, "quarter_end": q_end, "year_end": y_end}


def long_spread(s, cfg: SwapConfig | None = None, start: int = 0, days: int | None = None, charge: bool = True) -> dict:
    """Hold one unit notional long the spread from `start` for `days`: daily carry (minus the spread, a year), marks
    (DV01 times the spread's change), float over repo, and the balance-sheet charge, all per unit notional."""
    cfg = cfg or SwapConfig()
    sp = s["spread"]
    end = len(sp) - 1 if days is None else min(len(sp) - 1, start + days)
    w = slice(start, end)
    carry = -sp[w] / 1e4 / YEAR
    marks = cfg.dv01 * np.diff(sp[start:end + 1]) / 1e4
    fr = np.full(end - start, cfg.float_repo / 1e4 / YEAR)
    chg = np.full(end - start, -cfg.leverage_ratio * cfg.hurdle / YEAR if charge else 0.0)
    return {"carry": carry, "marks": marks, "float_repo": fr, "charge": chg, "total": carry + marks + fr + chg}
