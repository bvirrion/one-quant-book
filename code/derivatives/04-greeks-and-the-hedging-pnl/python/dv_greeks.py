"""Greeks and the hedging P&L: the gamma-theta identity, discrete hedging, break-even volatility,
and hedging at implied against hedging at realised volatility (Book 5, Chapter 4).

Vectorised over paths: every path is hedged at the same dates, the option is revalued with the
Black-Scholes formula at the hedging volatility, and the hedge is financed at r.
"""
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/bs"))
from firm_bs import bs, greeks  # noqa: E402

SQ2 = math.sqrt(2.0)


def _ncdf(x: np.ndarray) -> np.ndarray:
    from math import erfc
    return 0.5 * np.vectorize(erfc)(-x / SQ2)


def call_put_vec(s: np.ndarray, k: float, tau: float, r: float, vol: float):
    """Vectorised Black-Scholes call, put, call delta and gamma (q = 0)."""
    if tau <= 0:
        c = np.maximum(s - k, 0.0)
        return c, np.maximum(k - s, 0.0), (s > k).astype(float), np.zeros_like(s)
    sq = vol * math.sqrt(tau)
    d1 = (np.log(s / k) + r * tau) / sq + 0.5 * sq
    n1, n2 = _ncdf(d1), _ncdf(d1 - sq)
    c = s * n1 - k * math.exp(-r * tau) * n2
    p = c - s + k * math.exp(-r * tau)
    gamma = np.exp(-0.5 * d1 * d1) / math.sqrt(2 * math.pi) / (s * sq)
    return c, p, n1, gamma


def straddle(s: float, k: float, t: float, r: float, vol: float) -> dict:
    gc, gp = greeks(s, k, t, r, 0.0, vol, "C"), greeks(s, k, t, r, 0.0, vol, "P")
    out = {g: gc[g] + gp[g] for g in gc}
    out["price"] = bs(s, k, t, r, 0.0, vol, "C") + bs(s, k, t, r, 0.0, vol, "P")
    return out


def hedge_short_straddle(n_paths: int, steps: int, t: float = 1 / 12, s0: float = 100.0, k: float = 100.0,
                         r: float = 0.0, vol_imp: float = 0.20, vol_real: float = 0.25,
                         hedge_vol: float | None = None, seed: int = 1, mu: float = 0.0):
    """Sell one straddle at vol_imp, delta-hedge `steps` times at hedge_vol (default: vol_imp) while the
    share realises vol_real. Returns the P&L at expiry per path (in currency, per straddle)."""
    rng = np.random.default_rng(seed)
    hv = vol_imp if hedge_vol is None else hedge_vol
    dt = t / steps
    s = np.full(n_paths, s0)
    c, p, n1, _ = call_put_vec(s, k, t, r, hv)
    premium = bs(s0, k, t, r, 0.0, vol_imp, "C") + bs(s0, k, t, r, 0.0, vol_imp, "P")
    delta = 2 * n1 - 1                       # straddle delta; the short position holds +delta shares
    cash = premium - delta * s
    for i in range(1, steps + 1):
        z = rng.standard_normal(n_paths)
        s = s * np.exp((mu - 0.5 * vol_real ** 2) * dt + vol_real * math.sqrt(dt) * z)
        cash = cash * math.exp(r * dt)
        tau = t - i * dt
        if i < steps:
            _, _, n1, _ = call_put_vec(s, k, tau, r, hv)
            new = 2 * n1 - 1
            cash -= (new - delta) * s
            delta = new
    return cash + delta * s - np.abs(s - k)


def gamma_path(steps: int = 84, t: float = 1 / 12, vol_imp: float = 0.20, vol_real: float = 0.25, seed: int = 4):
    """One path of a short straddle hedged four times a day (21 trading days): cumulative P&L and
    the gamma-theta prediction
    sum of -1/2 Gamma S^2 ((dS/S)^2 - vol_imp^2 dt)."""
    rng = np.random.default_rng(seed)
    dt, s, k = t / steps, 100.0, 100.0
    prem = straddle(s, k, t, 0.0, vol_imp)["price"]
    _, _, n1, g = call_put_vec(np.array([s]), k, t, 0.0, vol_imp)
    delta, gam = 2 * n1[0] - 1, 2 * g[0]
    cash, pnl, pred = prem - delta * s, [0.0], [0.0]
    for i in range(1, steps + 1):
        s_new = s * math.exp(-0.5 * vol_real ** 2 * dt + vol_real * math.sqrt(dt) * rng.standard_normal())
        ret = s_new / s - 1.0
        pred.append(pred[-1] - 0.5 * gam * s * s * (ret * ret - vol_imp ** 2 * dt))
        s = s_new
        tau = t - i * dt
        c, p, n1, g = call_put_vec(np.array([s]), k, tau, 0.0, vol_imp)
        value = cash + delta * s - (c[0] + p[0])
        pnl.append(value)
        if i < steps:
            new = 2 * n1[0] - 1
            cash -= (new - delta) * s
            delta, gam = new, 2 * g[0]
    return np.arange(steps + 1) * 21.0 / steps, np.array(pnl), np.array(pred)


def derman_kamal_sd(vega: float, vol: float, n_hedges: int) -> float:
    """Approximate standard deviation of the discrete-hedging error of an at-the-money option."""
    return math.sqrt(math.pi / 4.0) * vega * vol / math.sqrt(n_hedges)


def breakeven_move(theta_per_day: float, gamma: float) -> float:
    """Daily spot move at which gamma P&L pays the day's theta: 1/2 Gamma dS^2 = -theta."""
    return math.sqrt(-2.0 * theta_per_day / gamma)


def problem() -> dict[str, float]:
    """The weekend problem: short 1,000 one-month at-the-money straddles (multiplier 100) at 20 %
    implied volatility while the share realises 25 %, hedged daily."""
    t, n = 1 / 12, 100_000.0                          # 1,000 straddles x multiplier 100
    st20, st25 = straddle(100, 100, t, 0.0, 0.20), straddle(100, 100, t, 0.0, 0.25)
    daily = hedge_short_straddle(20_000, 21, seed=1)
    hourly = hedge_short_straddle(20_000, 168, seed=1)
    at_real = hedge_short_straddle(20_000, 21, hedge_vol=0.25, seed=1)
    fair = hedge_short_straddle(20_000, 21, vol_real=0.20, seed=1)
    theta_day = st20["theta"] / 365.0
    cash_gamma = 0.5 * st20["gamma"] * 100.0 ** 2
    return {"premium": st20["price"], "premium_usd": st20["price"] * n, "straddle25": st25["price"],
            "exp_loss": st25["price"] - st20["price"], "exp_loss_usd": (st25["price"] - st20["price"]) * n,
            "delta": st20["delta"], "gamma": st20["gamma"], "vega_pt": 0.01 * st20["vega"],
            "theta_day": theta_day, "cash_gamma": cash_gamma, "gamma_1pct": st20["gamma"] * 100.0,
            "be_move": breakeven_move(theta_day, st20["gamma"]),
            "be_move_252": breakeven_move(st20["theta"] / 252.0, st20["gamma"]),
            "daily_mean": daily.mean(), "daily_sd": daily.std(), "daily_sd_usd": daily.std() * n,
            "hourly_sd": hourly.std(), "at_real_mean": at_real.mean(), "at_real_sd": at_real.std(),
            "fair_sd": fair.std(), "dk_daily": derman_kamal_sd(st20["vega"], 0.20, 21),
            "p_loss_daily": float((daily < 0).mean()), "vega_usd": 0.01 * st20["vega"] * n,
            "loss_from_vega": 5 * 0.01 * st20["vega"]}
