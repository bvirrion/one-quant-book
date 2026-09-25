"""firm.fxcarry -- currency carry baskets, crash hedges and the cross-currency basis (build of Book 9, chapter 14).

Carry baskets on any set of markets with a carry signal (firm.synthfut's ten currencies, or real ones): every
`every` days, long the k highest-carry and short the k lowest, equal weights. A crash hedge buys, at each rebalance,
a put on the basket's return for the period, struck `strike_sd` standard deviations below zero, priced by Black-Scholes
at the trailing volatility times `vol_mult` (a premium for crash risk). A cross-currency basis (basis points a
year, negative when borrowing dollars through FX swaps costs more than covered parity says) with a level, quarter-end
spikes that are deeper at year-end, and a mean-reverting noise; lending dollars through the swap earns minus the
basis, less a balance-sheet cost. NumPy only.

API (stable):
    carry_basket(r, carry, k, every)            dict of daily basket returns and positions (T, N)
    crash_hedge(basket, every, strike_sd, vol_mult, lookback)   dict of per-period hedge premium, payoff, P&L
    BasisConfig(...), simulate_basis(cfg)       daily basis (bp a year) and quarter-end flags
    basis_trade(b, cfg, days)                   daily return (bp a year, accrued daily) of lending dollars on those days
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

YEAR = 252


def carry_basket(r, carry, k: int = 3, every: int = 21) -> dict:
    """Long the k highest-carry markets and short the k lowest, rebalanced every `every` days on yesterday's carry."""
    r, carry = np.asarray(r, float), np.asarray(carry, float)
    T, N = r.shape
    pos = np.zeros((T, N))
    w = np.zeros(N)
    for t in range(1, T):
        if (t - 1) % every == 0:
            order = np.argsort(carry[t - 1])
            w = np.zeros(N)
            w[order[-k:]], w[order[:k]] = 1.0 / k, -1.0 / k
        pos[t] = w
    return {"r": (pos * r).sum(axis=1), "pos": pos}


def _ncdf(x):
    return 0.5 * math.erfc(-x / math.sqrt(2))


def crash_hedge(basket, every: int = 21, strike_sd: float = 1.5, vol_mult: float = 1.3, lookback: int = 63) -> dict:
    """At each rebalance a put on the basket's simple return over the period, struck strike_sd period-sds below zero,
    priced by Black-Scholes (forward 1, strike 1 + K) at the trailing vol times vol_mult; paid at the start, settled at
    the end. Returns per period: premium, payoff, and the hedged and unhedged period returns."""
    b = np.asarray(basket, float)
    starts = np.arange(lookback + 1, len(b) - every, every)
    prem, pay, raw = [], [], []
    for s in starts:
        sd = b[s - lookback:s].std() * math.sqrt(every)
        vol = sd * vol_mult
        K = 1.0 - strike_sd * sd
        d1 = (math.log(1.0 / K) + 0.5 * vol * vol) / vol
        price = K * _ncdf(-(d1 - vol)) - _ncdf(-d1)
        ret = float(np.prod(1 + b[s:s + every]) - 1)
        prem.append(price)
        pay.append(max(K - (1 + ret), 0.0))
        raw.append(ret)
    prem, pay, raw = np.array(prem), np.array(pay), np.array(raw)
    return {"start": starts, "premium": prem, "payoff": pay, "raw": raw, "hedged": raw - prem + pay}


@dataclass(frozen=True)
class BasisConfig:
    days: int = 10 * YEAR
    seed: int = 131
    level: float = -20.0          # basis level (bp a year)
    qe_extra: float = -30.0       # extra over the quarter-end window (bp a year) ...
    ye_extra: float = -60.0       # ... and at year-end instead
    window: int = 10              # trading days before a quarter-end
    noise_sd: float = 6.0
    noise_hl: float = 40.0
    bs_cost: float = 15.0         # the lender's balance-sheet cost (bp a year)


def simulate_basis(cfg: BasisConfig | None = None) -> dict:
    cfg = cfg or BasisConfig()
    rng = np.random.default_rng(cfg.seed)
    t = np.arange(cfg.days)
    q = YEAR // 4
    in_q = (t % q) >= q - cfg.window
    in_y = (t % YEAR) >= YEAR - cfg.window
    phi = 0.5 ** (1 / cfg.noise_hl)
    u = np.empty(cfg.days)
    u[0] = cfg.noise_sd * rng.standard_normal()
    for i in range(1, cfg.days):
        u[i] = phi * u[i - 1] + cfg.noise_sd * math.sqrt(1 - phi * phi) * rng.standard_normal()
    extra = np.where(in_y, cfg.ye_extra, np.where(in_q, cfg.qe_extra, 0.0))
    return {"basis": cfg.level + extra + u, "quarter_end": in_q, "year_end": in_y}


def basis_trade(b: dict, cfg: BasisConfig | None = None, days=None) -> np.ndarray:
    """Lend dollars through the FX swap on the chosen days (all if None): earn minus the basis less the balance-sheet
    cost, in bp a year accrued daily (0 on other days)."""
    cfg = cfg or BasisConfig()
    on = np.ones(len(b["basis"]), bool) if days is None else np.asarray(days, bool)
    return np.where(on, -b["basis"] - cfg.bs_cost, 0.0) / YEAR
