"""firm.volrv -- volatility relative value on a surface (build of One Quant Book 9, chapter 3).

A daily index surface on firm.synthvol's truth, quoted by two at-the-money vols (one and three months) and a skew
coefficient: the fair one-month and three-month vols come from the variance dynamics (atm_iv), the fair skew moves
with the level (skew0 + beta x (atm1 - mean atm1)); the market adds two planted noises, one on the skew and one on
the three-month vol, each a mean-reverting AR(1), standing for demand pressure that fades. Features are extracted as
a trader would: level (the one-month vol), slope (three-month minus one-month) and skew, and their residuals after
an expanding regression on the level. Two unit trades, each vega-neutral and delta-hedged daily: a risk reversal
(long a call one standardised unit above the money, short a put one below, equal vegas) and a calendar (long
three-month, short one-month at-the-money calls, equal vegas), struck monthly and held to the month's end. P&L is in
percent of vol (each leg is worth one unit when its vol rises one percent) and is attributed by sequential repricing
to spot and time (delta, gamma, theta), level (the move of the fair surface), skew noise and slope noise. NumPy
only.

API (stable):
    SurfaceConfig(...)                         noise and level-dependence parameters (seed 93)
    surface_path(r, v, cfg, scfg)              dict atm1, atm3, skew and the fair parts and noises, (T,) each
    features(s, warmup)                        level, slope, skew and residuals of slope and skew on the level
    trade_pnl(r, s, kind, pos, cfg, scfg)      monthly P&L buckets (spot_time, level, skew, slope, cost, total, start)
    attribution(b)                             each bucket's share of the total P&L
"""
from __future__ import annotations

import pathlib
import sys
from dataclasses import dataclass

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "synthvol"))
from firm_synthvol import YEAR, atm_iv, bs_delta, bs_price  # noqa: E402

T1, T3 = 21 / YEAR, 63 / YEAR


@dataclass(frozen=True)
class SurfaceConfig:
    seed: int = 93
    skew0: float = -0.12          # fair skew coefficient at the average level
    skew_beta: float = -0.4       # fair skew moves with the one-month vol (steeper when vol is high)
    phi: float = 0.98             # daily persistence of both noises (half-life 34 days)
    skew_sd: float = 0.06         # stationary sd of the skew noise
    slope_sd: float = 0.015       # stationary sd of the three-month vol noise (1.5 vol points)
    half_spread: float = 0.01     # cost of opening a leg: one percent of its vol (0.18 vol points at 18)
    roll_days: int = 21           # the whole book is re-struck (paid again) this often


def _ar1(rng, T, phi, sd):
    e = np.empty(T)
    e[0] = rng.normal(0, sd)
    for t in range(1, T):
        e[t] = phi * e[t - 1] + rng.normal(0, sd * np.sqrt(1 - phi * phi))
    return e


def surface_path(r, v, cfg, scfg: SurfaceConfig | None = None) -> dict:
    scfg = scfg or SurfaceConfig()
    rng = np.random.default_rng(scfg.seed)
    fair1, fair3 = atm_iv(v, cfg, T1), atm_iv(v, cfg, T3)
    fair_skew = scfg.skew0 + scfg.skew_beta * (fair1 - fair1.mean())
    e_skew, e_slope = _ar1(rng, len(v), scfg.phi, scfg.skew_sd), _ar1(rng, len(v), scfg.phi, scfg.slope_sd)
    return {"atm1": fair1, "atm3": fair3 + e_slope, "skew": fair_skew + e_skew, "fair3": fair3,
            "fair_skew": fair_skew, "e_skew": e_skew, "e_slope": e_slope}


def _residual(y, x, warmup):
    """y minus its expanding-window OLS fit on x, using only data up to each day (zero before warmup)."""
    out = np.zeros(len(y))
    sx, sy, sxx, sxy = np.cumsum(x), np.cumsum(y), np.cumsum(x * x), np.cumsum(x * y)
    n = np.arange(1, len(y) + 1)
    b = (sxy - sx * sy / n) / np.maximum(sxx - sx * sx / n, 1e-12)
    a = (sy - b * sx) / n
    out[warmup:] = (y - a - b * x)[warmup:]
    return out


def features(s: dict, warmup: int = 252) -> dict:
    level, slope, skew = s["atm1"], s["atm3"] - s["atm1"], s["skew"]
    return {"level": level, "slope": slope, "skew": skew,
            "slope_res": _residual(slope, level, warmup), "skew_res": _residual(skew, level, warmup)}


def _atm(state, tau):
    """At-the-money vol for maturity tau, total variance interpolated between one and three months (flat outside)."""
    w = np.clip((tau - T1) / (T3 - T1), 0.0, 1.0)
    return np.sqrt(((1 - w) * state[0] ** 2 * T1 + w * state[1] ** 2 * T3) / np.clip(tau, T1, T3))


def _value(state, S, K, tau, right, curv):
    tau = max(tau, 1e-8)
    a = _atm(state, max(tau, 1 / YEAR))
    x = np.log(K / S) / (a * np.sqrt(max(tau, 1 / YEAR)))
    vol = a * np.maximum(1 + state[2] * x + curv * x * x, 0.2)
    return bs_price(S, K, tau, vol, right), bs_delta(S, K, tau, vol, right)


def _legs(kind):
    """(maturity, standardised moneyness at inception, right, sign) of each leg of one unit trade."""
    if kind == "skew":
        return [(T1, 1.0, "C", 1.0), (T1, -1.0, "P", -1.0)]      # risk reversal: long the call wing, short the put
    return [(T3, 0.0, "C", 1.0), (T1, 0.0, "C", -1.0)]           # calendar: long three months, short one month


def trade_pnl(r, s: dict, kind: str, pos, cfg, scfg: SurfaceConfig | None = None) -> dict:
    """Per-period P&L buckets of pos[start] unit trades struck every roll_days and held, delta-hedged daily, for the
    period (kind 'skew' or 'calendar'). Each leg is sized so that a one-percent rise in its vol is worth one unit at
    inception: P&L is in percent of vol, whatever the level."""
    scfg = scfg or SurfaceConfig()
    st = lambda t, a3, sk: (s["atm1"][t], a3, sk)                                   # noqa: E731
    starts = np.arange(0, len(r) - scfg.roll_days - 1, scfg.roll_days)
    out = {k: np.zeros(len(starts)) for k in ("spot_time", "level", "skew", "slope", "cost")}
    for i, t0 in enumerate(starts):
        p = float(pos[t0])
        now0 = st(t0, s["atm3"][t0], s["skew"][t0])
        for tau0, x, right, sign in _legs(kind):
            K = float(np.exp(x * _atm(now0, tau0) * np.sqrt(tau0)))
            q = sign * p / (_value((now0[0] * 1.01, now0[1] * 1.01, now0[2]), 1.0, K, tau0, right, cfg.curv)[0]
                            - _value(now0, 1.0, K, tau0, right, cfg.curv)[0])
            S = 1.0
            for d in range(scfg.roll_days):
                t, tau = t0 + d, tau0 - d / YEAR
                S1 = S * np.exp(r[t + 1])
                now = st(t, s["atm3"][t], s["skew"][t])
                lvl = (s["atm1"][t + 1], s["fair3"][t + 1] + s["e_slope"][t], s["fair_skew"][t + 1] + s["e_skew"][t])
                skw = (lvl[0], lvl[1], s["skew"][t + 1])
                nxt = st(t + 1, s["atm3"][t + 1], s["skew"][t + 1])
                v0, delta = _value(now, S, K, tau, right, cfg.curv)
                v1, v2, v3, v4 = (_value(z, S1, K, tau - 1 / YEAR, right, cfg.curv)[0] for z in (now, lvl, skw, nxt))
                out["spot_time"][i] += q * (v1 - v0 - delta * (S1 - S))
                out["level"][i] += q * (v2 - v1)
                out["skew"][i] += q * (v3 - v2)
                out["slope"][i] += q * (v4 - v3)
                S = S1
        out["cost"][i] = -100 * scfg.half_spread * 2 * abs(p)                     # both legs opened each period
    out["total"] = sum(out[k] for k in ("spot_time", "level", "skew", "slope", "cost"))
    out["start"] = starts
    return out


def attribution(b: dict) -> dict:
    tot = b["total"].sum()
    return {k: float(b[k].sum() / tot) for k in ("spot_time", "level", "skew", "slope", "cost")}
