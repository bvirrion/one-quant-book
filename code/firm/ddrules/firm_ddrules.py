"""firm.ddrules -- drawdown rules and the evidence that a strategy has broken (build of One Quant Book 16, ch. 8).

A strategy's daily return is normal with volatility sigma/sqrt(252) and mean S*sigma/252 while it is alive; at a
random day it breaks and its Sharpe ratio drops to S_dead. Rules decide, day by day, whether to keep, halve or stop
it:
  stop-loss       stop when the drawdown from the running peak exceeds a threshold;
  ladder          halve at a first drawdown, stop at a second;
  time stop       stop when the strategy has made no new high for a number of days;
  posterior       stop when the posterior probability that it has broken exceeds a threshold (a two-state hidden
                  Markov filter with an absorbing broken state and a daily hazard of breaking).
The evaluator runs many strategies, some alive throughout and some that break, and reports false stops per hundred
strategy-years, the detection delay of broken ones and the P&L kept. Drawdowns are in units of capital (the
strategy's P&L is a fraction of its capital). NumPy only; firm.perf and firm.multistrat hold the single-path
drawdown statistics and stop rates of Books 7 and 8.

API (stable):
    paths(n, days, sr, vol, rng, break_day=None, sr_dead=0.0) -> daily returns (n, days)
    posterior(returns, sr, sr_dead, vol, hazard) -> P(broken by day t | returns up to t), shape (n, days)
    Rule(kind, a, b=None)   kinds: "stop", "ladder", "time", "posterior"
    apply(rule, returns, post=None) -> (sizes (n, days), stop_day (n,) or -1)
    evaluate(rule, alive, dead, break_day, post_alive, post_dead, charge) -> dict
    cusum_delay(sr, sr_dead, arl_days) -> approximate delay in days (Lorden's bound)
"""
import math
from dataclasses import dataclass

import numpy as np

DAYS = 252


def paths(n: int, days: int, sr: float, vol: float, rng, break_day=None, sr_dead: float = 0.0) -> np.ndarray:
    d = vol / math.sqrt(DAYS)
    mu = np.full(days, sr * vol / DAYS)
    if break_day is not None:
        mu[break_day:] = sr_dead * vol / DAYS
    return mu + d * rng.standard_normal((n, days))


def posterior(ret: np.ndarray, sr: float, sr_dead: float, vol: float, hazard: float) -> np.ndarray:
    """Forward filter of a two-state chain alive -> broken (absorbing, daily hazard `hazard`), Gaussian emissions."""
    d = vol / math.sqrt(DAYS)
    m1, m0 = sr * vol / DAYS, sr_dead * vol / DAYS
    n, T = ret.shape
    p = np.zeros(n)                     # P(broken | data so far)
    out = np.zeros((n, T))
    for t in range(T):
        prior = p + (1 - p) * hazard
        l1 = np.exp(-0.5 * ((ret[:, t] - m1) / d) ** 2)
        l0 = np.exp(-0.5 * ((ret[:, t] - m0) / d) ** 2)
        p = prior * l0 / (prior * l0 + (1 - prior) * l1)
        out[:, t] = p
    return out


@dataclass(frozen=True)
class Rule:
    kind: str
    a: float
    b: float | None = None


def apply(rule: Rule, ret: np.ndarray, post: np.ndarray | None = None):
    """Sizes (1, 0.5 or 0) applied to each day's return, decided on the previous days' P&L; stop day or -1."""
    n, T = ret.shape
    size = np.ones(n)
    sizes = np.zeros((n, T))
    eq = np.zeros(n)
    peak = np.zeros(n)
    last_high = np.zeros(n, int)
    stop = np.full(n, -1)
    for t in range(T):
        sizes[:, t] = size
        eq += size * ret[:, t]
        new = eq > peak
        last_high[new] = t
        peak = np.maximum(peak, eq)
        dd = peak - eq
        live = size > 0
        if rule.kind == "stop":
            hit = live & (dd > rule.a)
        elif rule.kind == "ladder":
            size[live & (size == 1.0) & (dd > rule.a)] = 0.5
            hit = live & (dd > rule.b)
        elif rule.kind == "time":
            hit = live & (t - last_high > rule.a)
        elif rule.kind == "posterior":
            hit = live & (post[:, t] > rule.a)
        else:
            raise ValueError(rule.kind)
        size[hit] = 0.0
        stop[hit & (stop < 0)] = t
    return sizes, stop


def evaluate(rule: Rule, alive: np.ndarray, dead: np.ndarray, break_day: int, post_alive=None, post_dead=None,
             charge: float = 0.0) -> dict:
    """charge: capital charge per year of running at full size (a fraction of capital), deducted in `value_*`."""
    sa, stop_a = apply(rule, alive, post_alive)
    sd, stop_d = apply(rule, dead, post_dead)
    years = alive.shape[1] / DAYS
    false = float((stop_a >= 0).mean() * 100 / years)
    caught = stop_d >= break_day
    delay = np.where(caught, stop_d - break_day, np.nan)
    early = float((stop_d >= 0).mean() - caught.mean())
    return {"false_per_100y": false, "share_caught": float(caught.mean()), "early_stops_dead": early,
            "median_delay_days": float(np.nanmedian(delay)) if caught.any() else math.inf,
            "pnl_alive": float((sa * alive).sum(1).mean()), "pnl_dead": float((sd * dead).sum(1).mean()),
            "pnl_alive_unmanaged": float(alive.sum(1).mean()), "pnl_dead_unmanaged": float(dead.sum(1).mean()),
            "value_alive": float(((sa * alive).sum(1) - charge * sa.sum(1) / DAYS).mean()),
            "value_dead": float(((sd * dead).sum(1) - charge * sd.sum(1) / DAYS).mean()),
            "value_alive_unmanaged": float(alive.sum(1).mean() - charge * alive.shape[1] / DAYS),
            "value_dead_unmanaged": float(dead.sum(1).mean() - charge * dead.shape[1] / DAYS)}


def cusum_delay(sr: float, sr_dead: float, arl_days: float) -> float:
    """Lorden's asymptotic delay of an optimal sequential detector: log(ARL) / KL per day, with
    KL = (Delta mu)^2 / (2 sigma_d^2) = (S - S_dead)^2 / (2 * 252) for daily returns."""
    kl = (sr - sr_dead) ** 2 / (2 * DAYS)
    return math.log(arl_days) / kl
