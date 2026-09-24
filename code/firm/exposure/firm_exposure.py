"""Counterparty exposure simulation (build of One Quant Book 6, chapter 17).

Scenarios: the USD short rate in chapter 7's Hull-White Gaussian form (x simulated exactly on the grid,
risk-neutral drift y(t)), EUR rates deterministic, EURUSD (USD per EUR) lognormal around its forward.
Trades are revalued on every path and grid date in closed form: a USD fixed-float swap (annual, floating
leg reset on the path), a EUR/USD fixed-fixed cross-currency swap with final notional exchange, an FX
forward. A netting set sums its trades; a two-way CSA holds variation margin with a threshold and a minimum
transfer amount; the exposure at t uses the collateral agreed one margin period of risk earlier, less any
independent amount. Profiles: expected exposure (EE), expected negative exposure (ENE), potential future
exposure (PFE, a quantile) and expected positive exposure (time average of EE). The aggregation step
(netting, collateral, profiles) has C++20 and Rust twins in cpp/ and rust/, tested on the same fixture.
Values in USD; times in years.
"""
import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Market:
    usd: object              # discount curve with df_t (USD)
    eur: object              # discount curve with df_t (EUR, deterministic)
    kappa: float = 0.03
    sigma: float = 0.0090    # Hull-White normal volatility of the USD short rate
    fx0: float = 1.10        # USD per EUR
    fx_vol: float = 0.08


def _B(k: float, tau):
    return (1.0 - np.exp(-k * tau)) / k


def _y(m: Market, t: float) -> float:
    return m.sigma ** 2 * (1.0 - math.exp(-2 * m.kappa * t)) / (2 * m.kappa)


@dataclass
class Scenarios:
    times: np.ndarray
    x: np.ndarray            # paths x times, Hull-White state
    fx: np.ndarray           # paths x times, EURUSD
    market: Market

    def usd_bond(self, k: int, T: float) -> np.ndarray:
        """P_USD(t_k, T) on every path."""
        m, t = self.market, float(self.times[k])
        if T <= t:
            return np.ones(self.x.shape[0])
        b = _B(m.kappa, T - t)
        return m.usd.df_t(T) / m.usd.df_t(t) * np.exp(-b * self.x[:, k] - 0.5 * b * b * _y(m, t))

    def eur_bond(self, k: int, T: float) -> float:
        t = float(self.times[k])
        return 1.0 if T <= t else self.market.eur.df_t(T) / self.market.eur.df_t(t)


def simulate(m: Market, horizon: float, steps_per_year: int, paths: int, seed: int = 21) -> Scenarios:
    n = round(horizon * steps_per_year)
    times = np.arange(n + 1) / steps_per_year
    dt, k, s = 1.0 / steps_per_year, m.kappa, m.sigma
    rng = np.random.default_rng(seed)
    half = paths // 2
    x, fx = np.zeros((2 * half, n + 1)), np.zeros((2 * half, n + 1))
    fx[:, 0] = m.fx0
    e = math.exp(-k * dt)
    sd = s * math.sqrt((1 - e * e) / (2 * k))
    w = np.zeros(2 * half)
    for j in range(1, n + 1):
        t0, t1 = times[j - 1], times[j]
        drift = s * s / (2 * k) * ((1 - e) / k - math.exp(-k * t1) * (math.exp(-k * t0) - math.exp(-k * t1)) / k)
        z = rng.standard_normal((half, 2))
        z = np.concatenate([z, -z])
        x[:, j] = e * x[:, j - 1] + drift + sd * z[:, 0]
        w = w + math.sqrt(dt) * z[:, 1]
        fwd = m.fx0 * m.eur.df_t(t1) / m.usd.df_t(t1)
        fx[:, j] = fwd * np.exp(m.fx_vol * w - 0.5 * m.fx_vol ** 2 * t1)
    return Scenarios(times, x, fx, m)


@dataclass(frozen=True)
class Swap:
    """USD swap, annual fixed and floating legs; value to the receiver of fixed if receive_fixed."""
    notional: float
    fixed: float
    maturity: int
    receive_fixed: bool = True

    def values(self, sc: Scenarios) -> np.ndarray:
        steps = round(1.0 / (sc.times[1] - sc.times[0]))
        out = np.zeros(sc.x.shape)
        reset_df = np.full(sc.x.shape[0], sc.market.usd.df_t(1.0))       # P(reset, pay) of the current period
        for k, t in enumerate(sc.times):
            if k % steps == 0 and k > 0 and t < self.maturity - 1e-9:
                reset_df = sc.usd_bond(k, t + 1.0)
            if t >= self.maturity - 1e-9:
                break
            nxt = math.floor(t + 1e-9) + 1.0
            fixed = sum(self.fixed * sc.usd_bond(k, float(T)) for T in range(int(nxt), self.maturity + 1))
            flo = sc.usd_bond(k, nxt) / reset_df - sc.usd_bond(k, float(self.maturity))
            v = self.notional * (fixed - flo)
            out[:, k] = v if self.receive_fixed else -v
        return out


@dataclass(frozen=True)
class XccySwap:
    """Receive USD fixed on usd_notional, pay EUR fixed on eur_notional, annual, final exchange (value in USD)."""
    usd_notional: float
    eur_notional: float
    usd_fixed: float
    eur_fixed: float
    maturity: int

    def values(self, sc: Scenarios) -> np.ndarray:
        out = np.zeros(sc.x.shape)
        for k, t in enumerate(sc.times):
            if t >= self.maturity - 1e-9:
                break
            pays = [float(T) for T in range(math.floor(t + 1e-9) + 1, self.maturity + 1)]
            usd = sum(self.usd_fixed * sc.usd_bond(k, T) for T in pays) + sc.usd_bond(k, float(self.maturity))
            eur = sum(self.eur_fixed * sc.eur_bond(k, T) for T in pays) + sc.eur_bond(k, float(self.maturity))
            out[:, k] = self.usd_notional * usd - sc.fx[:, k] * self.eur_notional * eur
        return out


@dataclass(frozen=True)
class FxForward:
    """Buy eur_notional EUR for strike USD per EUR at maturity (value in USD)."""
    eur_notional: float
    strike: float
    maturity: float

    def values(self, sc: Scenarios) -> np.ndarray:
        out = np.zeros(sc.x.shape)
        for k, t in enumerate(sc.times):
            if t >= self.maturity - 1e-9:
                break
            out[:, k] = self.eur_notional * (sc.fx[:, k] * sc.eur_bond(k, self.maturity)
                                             - self.strike * sc.usd_bond(k, self.maturity))
        return out


def usd_par_rate(curve, maturity: int) -> float:
    return (1.0 - curve.df_t(maturity)) / sum(curve.df_t(float(T)) for T in range(1, maturity + 1))


# ---- aggregation: the kernel twinned in C++20 and Rust ----------------------------------------------
def collateral(V: np.ndarray, threshold: float, mta: float) -> np.ndarray:
    """Two-way variation margin held (positive: received) agreed at each grid date."""
    C = np.zeros_like(V)
    for k in range(1, V.shape[1]):
        v = V[:, k]
        target = np.where(v > threshold, v - threshold, np.where(v < -threshold, v + threshold, 0.0))
        move = np.abs(target - C[:, k - 1]) >= mta
        C[:, k] = np.where(move, target, C[:, k - 1])
    return C


def exposure(V: np.ndarray, C: np.ndarray | None = None, lag: int = 0) -> np.ndarray:
    """Signed exposure V_k - C_{k - lag}: the collateral agreed one margin period of risk earlier."""
    if C is None:
        return V
    Cl = np.concatenate([np.zeros((V.shape[0], lag)), C[:, :V.shape[1] - lag]], axis=1) if lag else C
    return V - Cl


def profiles(E: np.ndarray, q: float = 0.975, ia: float = 0.0) -> dict:
    """EE and PFE (quantile, 'lower' convention) of max(E - IA, 0); ENE of min(E, 0) (IA posted to us
    protects our side only)."""
    pos = np.maximum(E - ia, 0.0)
    return {"ee": pos.mean(axis=0), "ene": np.minimum(E, 0.0).mean(axis=0),
            "pfe": np.quantile(pos, q, axis=0, method="lower")}


def epe(ee: np.ndarray, times: np.ndarray, horizon: float) -> float:
    """Time average of EE over [0, horizon] (trapezoid on the grid)."""
    mask = times <= horizon + 1e-12
    t, e = times[mask], ee[mask]
    return float(np.sum(0.5 * (e[1:] + e[:-1]) * np.diff(t)) / (t[-1] - t[0]))


def aggregate(trade_values: list[np.ndarray], threshold: float | None = None, mta: float = 0.0, lag: int = 0,
              ia: float = 0.0, q: float = 0.975) -> dict:
    """Net the trades of one netting set, apply the CSA (if threshold is not None), return profiles."""
    V = np.sum(trade_values, axis=0)
    C = collateral(V, threshold, mta) if threshold is not None else None
    return profiles(exposure(V, C, lag), q, ia)


def conditional_ee(E: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """EE conditional on default in each period, with path weights proportional to the default density."""
    return (np.maximum(E, 0.0) * weights).sum(axis=0) / weights.sum(axis=0)


def fixture(paths: int = 4, steps: int = 12) -> np.ndarray:
    """Deterministic value matrix shared with the C++20 and Rust tests (two trades stacked)."""
    p = np.arange(paths)[:, None]
    k = np.arange(steps + 1)[None, :]
    a = 10.0 * np.sin(0.5 * k + p) + 0.8 * k * (p % 3 - 1)
    b = 4.0 * np.cos(0.3 * k * (p + 1))
    return np.stack([a, b])
