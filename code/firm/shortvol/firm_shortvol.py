"""firm.shortvol -- short-volatility implementations (build of One Quant Book 9, chapter 1).

Monthly (every `tenor` trading days) implementations on firm.synthvol's index, each returning one P&L per period
per unit of notional (fractions of the index level at inception): a short variance swap (variance strike from the
surface minus realised variance, in variance units times tenor/252); a delta-hedged short at-the-money straddle,
hedged daily at the surface's current at-the-money vol; covered-call overwriting (long the index, short a call
`otm` above the forward); and put writing (short a put `otm` below, fully collateralised). A book levers or
volatility-targets the per-unit P&L. NumPy only.

API (stable):
    periods(T, tenor)                          start days of non-overlapping periods
    short_variance(r, v, cfg, tenor)           (n,) variance strike minus realised variance over each period
    hedged_straddle(r, v, cfg, tenor)          (n,) P&L of a short ATM straddle delta-hedged daily, per unit of index
    overwrite(r, v, cfg, tenor, otm)           (n,) index return plus call premium minus call payoff
    put_write(r, v, cfg, tenor, otm)           (n,) put premium minus put payoff
    lever(pnl, leverage)                       compounded capital path and whether it was wiped out (capital <= 0)
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "synthvol"))
from firm_synthvol import YEAR, atm_iv, bs_delta, bs_price, smile_iv  # noqa: E402


def periods(T: int, tenor: int = 21):
    return np.arange(0, T - tenor - 1, tenor)


def short_variance(r, v, cfg, tenor: int = 21):
    tau = tenor / YEAR
    out = []
    for s in periods(len(r), tenor):
        strike = float(atm_iv(v[s], cfg, tau)) ** 2
        realised = float((r[s + 1:s + 1 + tenor] ** 2).sum() / tau)
        out.append((strike - realised) * tau)
    return np.array(out)


def hedged_straddle(r, v, cfg, tenor: int = 21):
    out = []
    for s in periods(len(r), tenor):
        S, K = 1.0, 1.0
        vol0 = float(atm_iv(v[s], cfg, tenor / YEAR))
        premium = float(bs_price(S, K, tenor / YEAR, vol0, "C") + bs_price(S, K, tenor / YEAR, vol0, "P"))
        hedge_pnl = 0.0
        for d in range(tenor):
            tau = (tenor - d) / YEAR
            vol = float(atm_iv(v[s + d], cfg, tau))
            delta = float(bs_delta(S, K, tau, vol, "C") + bs_delta(S, K, tau, vol, "P"))
            S_new = S * np.exp(r[s + 1 + d])
            hedge_pnl += delta * (S_new - S)           # the short straddle's hedge is long its delta
            S = S_new
        out.append(premium - abs(S - K) + hedge_pnl)
    return np.array(out)


def overwrite(r, v, cfg, tenor: int = 21, otm: float = 0.02):
    tau = tenor / YEAR
    out = []
    for s in periods(len(r), tenor):
        K = 1.0 + otm
        vol = float(smile_iv(atm_iv(v[s], cfg, tau), np.log(K), tau, cfg))
        premium = float(bs_price(1.0, K, tau, vol, "C"))
        ST = float(np.exp(r[s + 1:s + 1 + tenor].sum()))
        out.append(ST - 1.0 + premium - max(ST - K, 0.0))
    return np.array(out)


def put_write(r, v, cfg, tenor: int = 21, otm: float = 0.05):
    tau = tenor / YEAR
    out = []
    for s in periods(len(r), tenor):
        K = 1.0 - otm
        vol = float(smile_iv(atm_iv(v[s], cfg, tau), np.log(K), tau, cfg))
        premium = float(bs_price(1.0, K, tau, vol, "P"))
        ST = float(np.exp(r[s + 1:s + 1 + tenor].sum()))
        out.append(premium - max(K - ST, 0.0))
    return np.array(out)


def lever(pnl, leverage: float):
    cap = np.cumprod(1.0 + leverage * np.asarray(pnl, float))
    dead = bool((cap <= 0).any())
    return np.where(np.maximum.accumulate(cap <= 0), 0.0, cap), dead
