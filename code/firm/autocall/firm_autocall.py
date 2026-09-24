"""Autocallables (build of Book 5, Chapter 18): a term sheet, a Monte Carlo pricer on any volatility function
(flat, local volatility) for single-underlying and worst-of notes, Phoenix and snowball coupons, a knock-in
monitored at expiry or daily, and the issuer's hedge across the knock-in near maturity.

Conventions: prices per 100 of notional; performances relative to the initial fixing; coupons are paid on
observation dates (Phoenix) or accrue and are paid at the autocall or at maturity (snowball).
"""
import math
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

FIRM = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FIRM / "barrier"))
from firm_barrier import barrier, bgk_shift, no_touch  # noqa: E402


@dataclass(frozen=True)
class TermSheet:
    obs_times: tuple[float, ...]            # observation dates (years); the last is maturity
    trigger: float = 1.0                    # autocall if the (worst) performance is at or above this
    coupon: float = 0.0                     # Phoenix coupon per period, per 100 of notional
    coupon_barrier: float = 0.7             # Phoenix coupon paid if the performance is at or above this
    memory: bool = True                     # missed Phoenix coupons are paid later when the barrier is met
    protection: float = 0.6                 # capital protected at maturity unless knocked in below this
    ki_daily: bool = False                  # knock-in monitored daily (True) or at maturity only (False)
    snowball_rate: float = 0.0              # annual coupon accrued to the autocall or maturity (snowball)
    first_call: int = 0                     # index of the first observation at which the note can autocall

    @property
    def maturity(self) -> float:
        return self.obs_times[-1]


def simulate(sigma_fn, s0, t_end: float, r: float, q, n_paths: int, seed: int, steps_per_year: int = 252,
             corr=None) -> tuple[np.ndarray, np.ndarray]:
    """Daily log-Euler paths of one or several assets (performances, start 1) under sigma_fn(t, S) (one function
    per asset, or one shared). Returns (times, paths) with paths of shape (n_paths, n_steps + 1, n_assets)."""
    s0 = np.atleast_1d(np.asarray(s0, float))
    m = len(s0)
    fns = sigma_fn if isinstance(sigma_fn, (list, tuple)) else [sigma_fn] * m
    q = np.broadcast_to(np.asarray(q, float), (m,))
    low = np.linalg.cholesky(np.asarray(corr, float)) if corr is not None else np.eye(m)
    steps = round(t_end * steps_per_year)
    dt = t_end / steps
    rng = np.random.default_rng(seed)
    half = n_paths // 2
    x = np.tile(np.log(s0), (2 * half, 1))
    out = np.empty((2 * half, steps + 1, m))
    out[:, 0, :] = np.exp(x)
    for i in range(steps):
        z = rng.standard_normal((half, m))
        z = np.vstack([z, -z]) @ low.T
        t_mid = (i + 0.5) * dt
        sig = np.column_stack([fns[j](t_mid, np.exp(x[:, j])) for j in range(m)])
        x = x + (r - q - 0.5 * sig * sig) * dt + sig * math.sqrt(dt) * z
        out[:, i + 1, :] = np.exp(x)
    return np.linspace(0.0, t_end, steps + 1), out / s0


def cashflows(ts: TermSheet, times: np.ndarray, perf: np.ndarray, r: float) -> dict:
    """Discounted value of the note per path (per 100) from simulated performances (n_paths, n_times, n_assets;
    worst-of when n_assets > 1), with the probability of each outcome."""
    worst = perf.min(axis=2)
    n = len(worst)
    idx = [int(np.argmin(np.abs(times - t))) for t in ts.obs_times]
    alive = np.ones(n, bool)
    pv = np.zeros(n)
    missed = np.zeros(n)
    called_at = np.full(n, -1)
    for j, (i, t) in enumerate(zip(idx, ts.obs_times, strict=True)):
        w = worst[:, i]
        df = math.exp(-r * t)
        if ts.coupon > 0:
            pay = alive & (w >= ts.coupon_barrier)
            amount = ts.coupon + (missed if ts.memory else 0.0)
            pv += np.where(pay, amount * df, 0.0)
            missed = np.where(alive & ~pay, missed + ts.coupon, np.where(pay, 0.0, missed))
        if j >= ts.first_call and j < len(idx) - 1:
            call = alive & (w >= ts.trigger)
            pv += np.where(call, (100.0 + 100.0 * ts.snowball_rate * t) * df, 0.0)
            called_at = np.where(call, j, called_at)
            alive &= ~call
    # maturity for the survivors
    wt = worst[:, idx[-1]]
    ki = (worst[:, : idx[-1] + 1].min(axis=1) < ts.protection) if ts.ki_daily else (wt < ts.protection)
    df = math.exp(-r * ts.maturity)
    redemption = np.where(ki, 100.0 * np.minimum(wt, 1.0), 100.0)
    if ts.snowball_rate > 0:
        ko = wt >= ts.trigger
        redemption = redemption + np.where(ko | ~ki, 100.0 * ts.snowball_rate * ts.maturity, 0.0)
    pv += np.where(alive, redemption * df, 0.0)
    return {"pv": pv, "called_at": called_at, "ki": alive & ki, "alive": alive}


def price(ts: TermSheet, sigma_fn, r: float = 0.0, q=0.0, n_paths: int = 100_000, seed: int = 18,
          corr=None, n_assets: int = 1) -> dict:
    times, perf = simulate(sigma_fn, np.ones(n_assets), ts.maturity, r, q, n_paths, seed, corr=corr)
    cf = cashflows(ts, times, perf, r)
    pv = cf["pv"]
    probs = [float(np.mean(cf["called_at"] == j)) for j in range(len(ts.obs_times) - 1)]
    return {"price": float(pv.mean()), "se": float(pv.std() / math.sqrt(len(pv))), "call_probs": probs,
            "ki_prob": float(cf["ki"].mean()), "maturity_prob": float(cf["alive"].mean())}


# ---------------------------------------------------------------- the knock-in cliff near maturity
def snowball_tail(s: float, ki: float, tau: float, vol: float, final_coupon: float, knocked: bool) -> float:
    """Value per 100 of a snowball with tau left, no autocall possible before maturity (spot far below the trigger),
    zero rates: if never knocked in it repays 100 plus final_coupon; if knocked in it repays 100 min(S_T, 1).
    Daily monitoring through the barrier shift; performances with initial level 1."""
    if knocked:
        return 100.0 * (s - _call(s, 1.0, tau, vol))
    h = bgk_shift(ki, s, vol, 1 / 252)
    p_survive = no_touch(s, h, tau, 0.0, 0.0, vol)
    # E[min(S_T, 1) ; knocked in] = E[S_T ; KI] - E[(S_T - 1)^+ ; KI]
    e_s_ki = s - barrier(s, 1e-6, h, tau, 0.0, 0.0, vol, "down-out", "C")
    dic = barrier(s, 1.0, h, tau, 0.0, 0.0, vol, "down-in", "C")
    return (100.0 + final_coupon) * p_survive + 100.0 * (e_s_ki - dic)


def _call(s: float, k: float, tau: float, vol: float) -> float:
    d1 = (math.log(s / k) + 0.5 * vol * vol * tau) / (vol * math.sqrt(tau))
    return s * 0.5 * math.erfc(-d1 / math.sqrt(2)) - k * 0.5 * math.erfc(-(d1 - vol * math.sqrt(tau)) / math.sqrt(2))


def hedge_across_ki(ki: float, tau: float, vol: float, final_coupon: float, notional: float = 100e6,
                    above: float = 0.01, h: float = 1e-4) -> dict:
    """The issuer is short the note and hedges with delta units of the underlying. Spot `above` above the knock-in
    level with tau left: the delta before the knock-in, the delta after a fall of `above` knocks it in, and the
    underlying sold in between, per `notional` of notes (in currency at the knock-in level)."""
    s = ki * (1 + above)

    def delta(x, knocked):
        return (snowball_tail(x + h, ki, tau, vol, final_coupon, knocked)
                - snowball_tail(x - h, ki, tau, vol, final_coupon, knocked)) / (2 * h) / 100.0
    d_before = delta(s, False)
    d_after = delta(ki * (1 - 1e-6), True)
    sold = (d_before - d_after) * notional * ki
    return {"delta_before": d_before, "delta_after": d_after, "sold": sold, "spot": s}
