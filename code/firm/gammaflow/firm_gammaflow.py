"""firm.gammaflow -- zero-day options, dealer gamma and intraday hedging feedback (build of One Quant Book 9, ch. 6).

Each simulated day an index opens at 100 with zero-day calls and puts on strikes every 0.1 from 97 to 103; call open
interest is centred above the open and put open interest below, each scaled by a daily lognormal amount and larger
on round strikes (every 0.5). Customers' net positions are drawn
each day, calls and puts separately, as a share of open interest between -1 (short) and 1 (long); dealers hold the
opposite. Through the day (78 five-minute bars) the dealers' options gain delta G x (index move) for dealer gamma G;
dealers trade a share of that unhedged delta each bar during the day and all that remains over the last 30 minutes,
and each trade moves the next bar's price by impact x trade: short gamma (G < 0) makes them buy after rises and sell
after falls, which carries the day's move into the close; long gamma makes them lean against it. An analyst
who sees open interest but not sides estimates dealer gamma under a convention (dealers long calls, short puts by
default). NumPy only.

API (stable):
    FlowConfig(...)                            parameters (seed 101)
    strikes(cfg), open_interest(cfg, centre)   strike grid and the shape of open interest per strike
    gamma(S, K, tau, vol)                      Black-Scholes gamma per unit of the index, vectorised
    dealer_gamma(S, tau, pos_c, pos_p, cfg)    total dealer gamma for dealer positions per strike (calls, puts)
    simulate_days(cfg)                         dict of paths (D, 79), true and estimated dealer gamma at the open,
                                               customer sides, and the no-feedback paths from the same shocks
    flip_level(pos_c, pos_p, cfg, tau)         index level at which the dealers' total gamma changes sign
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

YEAR_HOURS = 252 * 6.5


@dataclass(frozen=True)
class FlowConfig:
    days: int = 2000
    bars: int = 78
    seed: int = 101
    vol: float = 0.16             # annual vol of the exogenous shocks and of the options
    oi_width: float = 1.0         # open interest falls off as exp(-(K - centre)^2 / (2 width^2))
    oi_shift: float = 0.5         # calls centred above the open, puts below
    oi_dispersion: float = 0.5    # lognormal day-to-day dispersion of call and put open interest
    round_boost: float = 3.0      # open interest multiple on strikes that are multiples of 0.5
    call_side: float = -0.2       # mean customer net position in calls (share of OI; negative: customers short)
    put_side: float = 0.3         # mean customer net position in puts
    side_sd: float = 0.5          # day-to-day sd of the customer sides
    impact: float = 0.05          # next-bar move per unit of dealer hedge trade (index units)
    intraday_hedge: float = 0.1   # share of their unhedged delta dealers trade each bar during the day
    close_bars: int = 6           # over the last 30 minutes they trade out all of it, evenly
    conv_call: float = -1.0       # the analyst's assumed customer side in calls (customers short calls)
    conv_put: float = 1.0         # and in puts (customers long puts)


def strikes(cfg: FlowConfig | None = None):
    return np.round(np.arange(97.0, 103.0001, 0.1), 1)


def open_interest(cfg: FlowConfig | None = None, centre: float = 100.0):
    """Open interest shape per strike around a centre, boosted on round strikes."""
    cfg = cfg or FlowConfig()
    K = strikes(cfg)
    oi = np.exp(-((K - centre) ** 2) / (2 * cfg.oi_width**2))
    return oi * np.where(np.isclose(np.round(K * 2) / 2, K), cfg.round_boost, 1.0)


def gamma(S, K, tau, vol):
    S, K = np.asarray(S, float), np.asarray(K, float)
    sd = vol * math.sqrt(max(tau, 1e-9))
    d1 = (np.log(S / K) + 0.5 * sd * sd) / sd
    return np.exp(-0.5 * d1 * d1) / (math.sqrt(2 * math.pi) * S * sd)


def dealer_gamma(S, tau, pos_c, pos_p, cfg: FlowConfig | None = None):
    """Sum over strikes of dealer positions times gamma (calls and puts have the same gamma); S may be (D,)."""
    cfg = cfg or FlowConfig()
    g = gamma(np.asarray(S, float)[..., None], strikes(cfg), tau, cfg.vol)
    return (g * (np.asarray(pos_c, float) + np.asarray(pos_p, float))).sum(axis=-1)


def flip_level(pos_c, pos_p, cfg: FlowConfig | None = None, tau: float = 3 / YEAR_HOURS):
    """The index level on a grid from 97 to 103 nearest to where the dealers' total gamma changes sign (nan if none)."""
    grid = np.linspace(97, 103, 601)
    g = dealer_gamma(grid, tau, pos_c, pos_p, cfg)
    change = np.nonzero(np.diff(np.sign(g)))[0]
    return float(grid[change[0]]) if len(change) else float("nan")


def simulate_days(cfg: FlowConfig | None = None) -> dict:
    cfg = cfg or FlowConfig()
    rng = np.random.default_rng(cfg.seed)
    D, B = cfg.days, cfg.bars
    amt = np.exp(cfg.oi_dispersion * rng.standard_normal((2, D, 1)))
    oi_c = amt[0] * open_interest(cfg, 100 + cfg.oi_shift)
    oi_p = amt[1] * open_interest(cfg, 100 - cfg.oi_shift)
    c_call = np.clip(rng.normal(cfg.call_side, cfg.side_sd, D), -1, 1)
    c_put = np.clip(rng.normal(cfg.put_side, cfg.side_sd, D), -1, 1)
    pos_c, pos_p = -c_call[:, None] * oi_c, -c_put[:, None] * oi_p      # dealers hold the opposite
    est_c, est_p = -cfg.conv_call * oi_c, -cfg.conv_put * oi_p
    dt = 6.5 / B / YEAR_HOURS
    eps = cfg.vol * math.sqrt(dt) * rng.standard_normal((D, B))
    S, S0 = np.full((D, B + 1), 100.0), np.full((D, B + 1), 100.0)
    unhedged, push = np.zeros(D), np.zeros(D)
    trades = np.zeros((D, B))
    for b in range(B):
        tau = (B - b) * dt
        S[:, b + 1] = S[:, b] * (1 + eps[:, b]) + push
        S0[:, b + 1] = S0[:, b] * (1 + eps[:, b])
        G = dealer_gamma(S[:, b], tau, pos_c, pos_p, cfg)
        unhedged += G * (S[:, b + 1] - S[:, b])                       # the options' delta drifts with the index
        frac = 1.0 / (B - b) if b >= B - cfg.close_bars else cfg.intraday_hedge
        trade = -frac * unhedged                                        # dealers trade to offset it
        unhedged += trade
        trades[:, b] = trade
        push = cfg.impact * trade                                      # and move the next bar
    tau0 = B * dt
    return {"S": S, "S_free": S0, "true_gamma": dealer_gamma(np.full(D, 100.0), tau0, pos_c, pos_p, cfg),
            "est_gamma": dealer_gamma(np.full(D, 100.0), tau0, est_c, est_p, cfg), "call_side": c_call,
            "put_side": c_put,
            "trades": trades, "pos_c": pos_c, "pos_p": pos_p}
