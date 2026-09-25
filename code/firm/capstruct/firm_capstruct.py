"""firm.capstruct -- capital-structure arbitrage on a structural model (build of One Quant Book 9, chapter 9).

Firms whose shares follow a geometric Brownian motion and whose five-year credit default swap is priced by a first-
passage model in the spirit of CreditGrades: assets V = E + L D (equity plus the recovered part of debt per share),
asset vol sigma_E E / V, default when V first touches L D; the five-year survival q gives a spread (1 - R) (-ln q) / 5.
The market's spread is the model's at the true debt times a mean-reverting mispricing; now and then a firm's debt
per share jumps (a leverage shift, as in a leveraged buyout) while its share jumps on the premium, and the trader
learns the new debt only `lag` days later; each firm's true barrier share L differs from the one the trader assumes.
The trader's equity-implied spread uses the known debt and the trailing year's equity vol. Convergence trades: when
the market spread is far from the implied one, sell (or buy) protection and hedge with the shares, and close on
convergence or after `max_days`. NumPy only.

API (stable):
    CapConfig(...)                             parameters (seed 103)
    implied_spread(E, D, sigma_E, cfg)         five-year spread from the first-passage model (vectorised)
    hedge_ratio(E, D, sigma_E, cfg)            shares per unit of protection notional that offset the spread's move
    simulate_firms(cfg)                        dict of daily E, market spread, true and known debt, trailing vol, shifts
    trades(sim, cfg)                           closed trades (entry, exit, side, P&L in CDS and shares), the book's
                                               daily P&L and the number of trades open each day
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

YEAR = 252


@dataclass(frozen=True)
class CapConfig:
    firms: int = 60
    days: int = 10 * YEAR
    seed: int = 103
    E0: float = 50.0
    D0: float = 40.0              # debt per share
    L: float = 0.5                # recovered share of debt assumed by the trader: the default barrier is L D
    L_dispersion: float = 0.25    # each firm's true L is L times a lognormal with this dispersion
    R: float = 0.4                # CDS recovery
    sigma_E: float = 0.35
    mis_sd: float = 0.10          # sd of the log mispricing of the market spread
    mis_phi: float = 0.98         # its daily persistence
    shift_rate: float = 0.05      # leverage shifts a firm-year
    shift_mult: float = 2.0       # debt per share multiplied by this (a leveraged buyout or recapitalisation)
    shift_jump: float = 0.20      # the share jumps this much on the day (a takeover premium)
    lag: int = 63                 # days before the trader's debt catches up
    enter: float = 0.4            # enter when |log(market / implied)| exceeds this
    exit: float = 0.05            # exit when it falls below this ...
    max_days: int = 180           # ... or after this many days
    rpv01: float = 4.5            # risky annuity of the five-year CDS (years)
    cost: float = 0.0002          # CDS half-spread in spread units at entry and at exit


def _ncdf(x):
    return 0.5 * np.vectorize(math.erfc)(-np.asarray(x, float) / math.sqrt(2))


class _with_L:
    """A config whose barrier share L may be an array (one per firm)."""

    def __init__(self, cfg, L):
        self.L, self.R = L, cfg.R


def implied_spread(E, D, sigma_E, cfg: CapConfig):
    E, D, sigma_E = (np.asarray(a, float) for a in (E, D, sigma_E))
    V = E + cfg.L * D
    s = sigma_E * E / V
    x = np.log(V / (cfg.L * D))
    t = 5.0
    nu = -0.5 * s * s
    st = s * math.sqrt(t)
    q = _ncdf((x + nu * t) / st) - np.exp(x) * _ncdf((-x + nu * t) / st)
    return (1 - cfg.R) * -np.log(np.clip(q, 1e-12, 1.0)) / t


def hedge_ratio(E, D, sigma_E, cfg: CapConfig, h: float = 0.01):
    """Shares to short per unit of protection notional sold: minus the risky annuity times d(spread)/dE."""
    E = np.asarray(E, float)
    ds = (implied_spread(E * (1 + h), D, sigma_E, cfg) - implied_spread(E * (1 - h), D, sigma_E, cfg)) / (2 * h * E)
    return -cfg.rpv01 * ds                                          # spreads fall as E rises: a positive number


def simulate_firms(cfg: CapConfig | None = None) -> dict:
    cfg = cfg or CapConfig()
    rng = np.random.default_rng(cfg.seed)
    N, T = cfg.firms, cfg.days
    r = cfg.sigma_E / math.sqrt(YEAR) * rng.standard_normal((T, N)) - 0.5 * cfg.sigma_E**2 / YEAR
    D_true = np.full((T, N), cfg.D0)
    shifts = []
    for i in range(N):
        n = rng.poisson(cfg.shift_rate * T / YEAR)
        for day in sorted(rng.integers(YEAR, T - YEAR, n)):
            D_true[day:, i] *= cfg.shift_mult
            r[day, i] += math.log(1 + cfg.shift_jump)
            shifts.append((int(day), i))
    E = cfg.E0 * np.exp(np.cumsum(r, axis=0))
    D_known = D_true.copy()
    for day, i in shifts:
        D_known[day:day + cfg.lag, i] = D_true[day - 1, i]
    u = np.empty((T, N))
    u[0] = cfg.mis_sd * rng.standard_normal(N)
    for t in range(1, T):
        u[t] = cfg.mis_phi * u[t - 1] + cfg.mis_sd * math.sqrt(1 - cfg.mis_phi**2) * rng.standard_normal(N)
    L_true = cfg.L * np.exp(cfg.L_dispersion * rng.standard_normal(N))
    true_spread = implied_spread(E, D_true, cfg.sigma_E, _with_L(cfg, L_true))
    vol = np.full((T, N), cfg.sigma_E)
    csum, csq = np.cumsum(r, axis=0), np.cumsum(r * r, axis=0)
    for t in range(YEAR, T):
        m = (csum[t] - csum[t - YEAR]) / YEAR
        vol[t] = np.sqrt(np.maximum((csq[t] - csq[t - YEAR]) / YEAR - m * m, 1e-8) * YEAR)
    return {"E": E, "spread": true_spread * np.exp(u - 0.5 * cfg.mis_sd**2), "true_spread": true_spread,
            "L_true": L_true,
            "D_true": D_true, "D_known": D_known, "vol": vol, "shifts": shifts}


def trades(sim: dict, cfg: CapConfig | None = None) -> dict:
    """Convergence trades from day YEAR on, one unit of protection notional each; side +1 sells protection (market
    spread rich). Returns the closed trades, the book's daily P&L and the number of open trades each day."""
    cfg = cfg or CapConfig()
    E, s, T = sim["E"], sim["spread"], sim["E"].shape[0]
    implied = implied_spread(E, sim["D_known"], sim["vol"], cfg)
    gap = np.log(s / implied)
    shift_days = {}
    for d, j in sim["shifts"]:
        shift_days.setdefault(j, []).append(d)
    out, daily, n_open = [], np.zeros(T), np.zeros(T)
    for i in range(E.shape[1]):
        t = YEAR
        while t < T - 1:
            if abs(gap[t, i]) <= cfg.enter:
                t += 1
                continue
            side, t0 = (1.0 if gap[t, i] > 0 else -1.0), t
            h = side * float(hedge_ratio(E[t, i], sim["D_known"][t, i], sim["vol"][t, i], cfg))
            cds = equity = 0.0
            daily[t] -= cfg.cost * cfg.rpv01
            while t < T - 1:
                c = side * (s[t, i] / YEAR - cfg.rpv01 * (s[t + 1, i] - s[t, i]))
                e = -h * (E[t + 1, i] - E[t, i])
                cds, equity = cds + c, equity + e
                daily[t + 1] += c + e
                n_open[t + 1] += 1
                t += 1
                if abs(gap[t, i]) < cfg.exit or t - t0 >= cfg.max_days:
                    break
            daily[t] -= cfg.cost * cfg.rpv01
            cds -= 2 * cfg.cost * cfg.rpv01
            through = any(t0 < d <= t for d in shift_days.get(i, []))
            out.append({"firm": i, "entry": t0, "exit": t, "side": side, "cds": cds, "equity": equity,
                        "pnl": cds + equity, "through_shift": through})
            t += 1
    return {"trades": out, "daily": daily, "open": n_open}
