"""firm.synthfut -- a synthetic futures universe (build of One Quant Book 8, chapter 19).

Forty futures markets in four asset classes (equity indices, government bonds, currencies, commodities), daily, with
the features that the futures strategies of chapters 19-25 trade, each planted and kept as truth:
* a persistent drift a_it per market (an AR(1) with a half-life of months): the trend;
* a carry c_it per market (the futures' return if spot prices stay unchanged, annual), slow-moving around a market
  mean, of which a share `carry_premium` is earned as expected excess return;
* volatility clustering: each class's volatility follows an AR(1) in logs; Student-t shocks, a class factor
  (correlation within the class) and a specific part;
* stock-crash episodes of `crash_days` days, in which equities, commodities and high-carry currencies fall steadily,
  bonds rally, and volatility rises by half;
* seasonal commodities, whose spot price has an annual cycle that futures curves anticipate (their returns do not).
Excess returns r are those of a position rolled in the nearby contract. The spot log price is s = x + season, with
dx = r - c dt; the log futures price for delivery T is x_t - c_t (T - t) + season(T). NumPy only.

API (stable):
    FutConfig(...)                    parameters; defaults: 30 years of 252 days, 10 markets per class, seed 7
    simulate_futures(cfg) -> dict     names, cls (N,) class index, r (T, N) daily excess returns, carry (T, N) annual,
                                      drift (T, N) annual (truth), vol (T, N) daily volatility (truth), x (T, N) log
                                      spot without season, amp (N,), phase (N,), crashes [(start, end)]
    season(amp, phase, t)             seasonal log component at day(s) t (252-day year)
    curve(F, t, taus)                 (N, len(taus)) log futures prices for deliveries t + tau (tau in days)
    contracts(F, t, n, every)         (N, n) log prices of the next n contracts expiring every `every` days
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

CLASSES = ("equity", "bond", "currency", "commodity")
YEAR = 252


@dataclass(frozen=True)
class FutConfig:
    years: int = 30
    per_class: int = 10
    seed: int = 7
    vol: tuple = (0.16, 0.06, 0.09, 0.25)          # annual volatility by class
    within: tuple = (0.7, 0.6, 0.4, 0.25)          # share of variance from the class factor
    trend_sr: float = 0.5                          # annual sd of the drift, in units of the market's volatility
    trend_half_life: float = 252.0                 # days
    carry_sd: tuple = (0.01, 0.01, 0.025, 0.06)    # cross-sectional sd of carry by class (annual)
    carry_half_life: float = 252.0
    carry_premium: float = 0.5                     # share of carry earned as expected excess return
    vol_persist: float = 0.99                      # daily persistence of log volatility
    vol_sd: float = 0.25                           # stationary sd of log volatility
    t_df: float = 5.0
    crashes: tuple = (0.25, 0.6, 0.9)              # start of each stock crash, as a share of the sample
    crash_days: int = 100
    crash_move: tuple = (-0.30, 0.03, 0.0, -0.10)  # total drift of each class over a crash
    carry_crash: float = 0.08                      # currency loss per unit of carry z-score over a crash
    crash_vol: float = 1.5                         # volatility multiplier during a crash
    seasonal: int = 3                              # the first commodities with an annual cycle in spot
    season_amp: float = 0.15


def _student(rng, df, size):
    return rng.standard_t(df, size) / math.sqrt(df / (df - 2))


def season(amp, phase, t):
    return np.asarray(amp) * np.sin(2 * math.pi * (np.asarray(t, float)[..., None] / YEAR) + np.asarray(phase))


def simulate_futures(cfg: FutConfig | None = None) -> dict:
    cfg = cfg or FutConfig()
    rng = np.random.default_rng(cfg.seed)
    K, n = len(CLASSES), cfg.per_class
    N, T = K * n, cfg.years * YEAR
    cls = np.repeat(np.arange(K), n)
    names = [f"{CLASSES[k][:3].upper()}{j + 1:02d}" for k in range(K) for j in range(n)]
    sig = np.array(cfg.vol)[cls]
    w = np.array(cfg.within)[cls]
    phi_a = math.exp(-math.log(2) / cfg.trend_half_life)
    phi_c = math.exp(-math.log(2) / cfg.carry_half_life)
    csd = np.array(cfg.carry_sd)[cls]
    cmean = rng.normal(0, 0.6, N) * csd
    starts = [int(s * T) for s in cfg.crashes]
    in_crash = np.zeros(T, bool)
    for s in starts:
        in_crash[s:s + cfg.crash_days] = True
    a = rng.normal(0, 1, N) * cfg.trend_sr * sig
    c = cmean + rng.normal(0, 0.8, N) * csd
    lv = np.zeros(K)
    out = {k: np.zeros((T, N)) for k in ("r", "carry", "drift", "vol")}
    for t in range(T):
        a = phi_a * a + math.sqrt(1 - phi_a**2) * cfg.trend_sr * sig * rng.standard_normal(N)
        c = cmean + phi_c * (c - cmean) + math.sqrt(1 - phi_c**2) * 0.8 * csd * rng.standard_normal(N)
        lv = cfg.vol_persist * lv + math.sqrt(1 - cfg.vol_persist**2) * cfg.vol_sd * rng.standard_normal(K)
        boost = math.log(cfg.crash_vol) if in_crash[t] else 0.0
        vol_t = sig * np.exp(lv[cls] - cfg.vol_sd**2 / 2 + boost) / math.sqrt(YEAR)
        shock = np.sqrt(w) * _student(rng, cfg.t_df, K)[cls] + np.sqrt(1 - w) * _student(rng, cfg.t_df, N)
        mu = (a + cfg.carry_premium * c) / YEAR
        if in_crash[t]:
            mu = mu + np.array(cfg.crash_move)[cls] / cfg.crash_days
            fx = cls == 2
            z = (c[fx] - c[fx].mean()) / (c[fx].std() + 1e-12)
            mu[fx] -= cfg.carry_crash * z / cfg.crash_days
        out["r"][t] = mu + vol_t * shock
        out["carry"][t], out["drift"][t], out["vol"][t] = c, a, vol_t
    out["x"] = np.cumsum(out["r"] - out["carry"] / YEAR, axis=0)
    amp = np.zeros(N)
    phase = np.zeros(N)
    com = np.flatnonzero(cls == 3)[:cfg.seasonal]
    amp[com] = cfg.season_amp
    phase[com] = rng.uniform(0, 2 * math.pi, len(com))
    out.update({"names": names, "cls": cls, "amp": amp, "phase": phase,
                "crashes": [(s, s + cfg.crash_days) for s in starts]})
    return out


def curve(F: dict, t: int, taus) -> np.ndarray:
    taus = np.asarray(taus, float)
    x, c = F["x"][t][:, None], F["carry"][t][:, None]
    seas = season(F["amp"], F["phase"], t + taus).T
    return x - c * taus[None, :] / YEAR + seas


def contracts(F: dict, t: int, n: int = 4, every: int = 21) -> np.ndarray:
    first = (t // every + 1) * every
    return curve(F, t, np.arange(n) * every + first - t)
