"""firm.convarb -- a convertible arbitrage book (build of One Quant Book 9, chapter 8).

A convertible on one of firm.synthvol's members, priced by firm.convertible (Book 5's Crank-Nicolson pricer with an
equity-to-credit hazard lambda(S) = lam0 (S / s0)^-p), tabulated once for each remaining maturity (monthly) and for
a normal and a stressed hazard (times `hazard_stress`). The market pays the model value less a cheapness: 3% at
issue, falling to 1% over six months, jumping to `cheap_stress` in a forced-selling episode and decaying back after
it; the hazard multiplier and the borrow fee jump in the same episode. The book is long one bond and short its delta
in shares (rebalanced daily), and optionally long credit protection that pays back the bond's loss from the hazard
multiplier, for a premium of the bond's value at risk from a doubled hazard divided by the protection's annuity each
year. P&L is attributed each day to the bond's model move, the credit state, cheapness, the stock hedge, the credit
hedge, coupons and borrow. NumPy only.

API (stable):
    ArbConfig(...)                              parameters of the bond, the market and the episode
    value_tables(cfg)                           (taus, spots, normal values, stressed values), cached
    mark(tables, tau, S, stressed)              model value by interpolation in maturity and log spot
    delta(tables, tau, S, stressed)             shares per bond from the table
    scenario(T, cfg)                            dict of daily cheapness, hazard multiplier and borrow fee
    run_book(S, cfg, credit_hedge)              dict of daily P&L buckets per bond (units of face 100)
"""
from __future__ import annotations

import functools
import math
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "convertible"))
from firm_convertible import Convertible, power_hazard, price_grid  # noqa: E402

YEAR = 252


@dataclass(frozen=True)
class ArbConfig:
    maturity: float = 5.0
    s0: float = 40.0              # share price at issue; conversion price 40 (ratio 2.5)
    vol: float = 0.30             # pricing vol
    r: float = 0.03
    lam0: float = 0.03            # hazard at s0
    p: float = 1.0                # equity-to-credit exponent
    hazard_stress: float = 2.0    # hazard multiplier in the episode
    new_issue: float = 0.03       # cheapness at issue, when the book buys ...
    new_issue_days: int = 126     # ... falling to the normal level over this many days
    cheap: float = 0.01           # normal cheapness (share of model value)
    cheap_stress: float = 0.06    # cheapness at the depth of the episode
    borrow: float = 0.005         # annual borrow fee on the short shares
    borrow_stress: float = 0.05
    stress_start: int = 500       # day of the episode's start (after purchase)
    stress_len: int = 63          # days of stress
    recovery_days: int = 126      # cheapness decays back over this many days after the episode


def _bond(cfg: ArbConfig, tau: float) -> Convertible:
    elapsed = cfg.maturity - tau
    return Convertible(maturity=tau, ratio=100 / cfg.s0, call_start=max(2.0 - elapsed, 0.0),
                       call_trigger=1.3 * cfg.s0)


@functools.lru_cache(maxsize=4)
def value_tables(cfg: ArbConfig):
    taus = np.array([cfg.maturity - k / 12 for k in range(int(cfg.maturity * 12))])
    rows = {False: [], True: []}
    spots = None
    for tau in taus:
        for stressed in (False, True):
            lam = cfg.lam0 * (cfg.hazard_stress if stressed else 1.0)
            spots, v = price_grid(_bond(cfg, tau), cfg.r, 0.0, cfg.vol, power_hazard(lam, cfg.s0, cfg.p), nx=300,
                                  steps_per_year=100)
            rows[stressed].append(v)
    return taus, spots, np.array(rows[False]), np.array(rows[True])


def mark(tables, tau: float, S: float, stressed: bool = False) -> float:
    taus, spots, normal, stress = tables
    vals = stress if stressed else normal
    k = np.clip(np.searchsorted(-taus, -tau), 1, len(taus) - 1)      # taus decrease
    w = (taus[k - 1] - tau) / (taus[k - 1] - taus[k])
    x = math.log(S)
    lo, hi = np.interp(x, np.log(spots), vals[k - 1]), np.interp(x, np.log(spots), vals[k])
    return float((1 - w) * lo + w * hi)


def delta(tables, tau: float, S: float, stressed: bool = False, h: float = 0.01) -> float:
    return (mark(tables, tau, S * (1 + h), stressed) - mark(tables, tau, S * (1 - h), stressed)) / (2 * S * h)


def scenario(T: int, cfg: ArbConfig) -> dict:
    cheap, mult, fee = np.full(T, cfg.cheap), np.ones(T), np.full(T, cfg.borrow)
    n = min(cfg.new_issue_days, T)
    cheap[:n] = cfg.new_issue + (cfg.cheap - cfg.new_issue) * np.linspace(0.0, 1.0, n)
    a, b = cfg.stress_start, cfg.stress_start + cfg.stress_len
    ramp = cfg.cheap + (cfg.cheap_stress - cfg.cheap) * np.linspace(0.3, 1.0, cfg.stress_len)
    decay = cfg.cheap + (cfg.cheap_stress - cfg.cheap) * np.linspace(1.0, 0.0, cfg.recovery_days)
    cheap[a:b] = ramp[:max(0, min(b, T) - a)]
    cheap[b:b + cfg.recovery_days] = decay[:max(0, min(b + cfg.recovery_days, T) - b)]
    mult[a:b], fee[a:b] = cfg.hazard_stress, cfg.borrow_stress
    return {"cheap": cheap, "stressed": mult > 1, "fee": fee}


def run_book(S, cfg: ArbConfig | None = None, credit_hedge: bool = False) -> dict:
    """One bond bought at the market price on day 0, short its delta daily, held to the end of S (at most maturity)."""
    cfg = cfg or ArbConfig()
    tables = value_tables(cfg)
    S = np.asarray(S, float) * cfg.s0 / S[0]
    T = min(len(S) - 1, int(cfg.maturity * YEAR) - 1)
    sc = scenario(T + 1, cfg)
    keys = ("bond", "hedge", "cheapness", "credit", "credit_hedge", "coupon", "borrow")
    out = {k: np.zeros(T) for k in keys}
    coupon_days = {int(round((cfg.maturity - k) * YEAR)) for k in range(int(cfg.maturity))}
    for t in range(T):
        tau0, tau1 = cfg.maturity - t / YEAR, cfg.maturity - (t + 1) / YEAR
        st0, st1 = bool(sc["stressed"][t]), bool(sc["stressed"][t + 1])
        m0 = mark(tables, tau0, S[t], st0)
        m1 = mark(tables, tau1, S[t + 1], st0)                        # the day's move at yesterday's credit state
        m1s = mark(tables, tau1, S[t + 1], st1)                       # then the credit state changes
        d = delta(tables, tau0, S[t], st0)
        out["bond"][t] = m1 - m0
        out["credit"][t] = m1s - m1
        out["cheapness"][t] = -(m1s * sc["cheap"][t + 1] - m0 * sc["cheap"][t])
        out["hedge"][t] = -d * (S[t + 1] - S[t])
        out["borrow"][t] = -d * S[t] * sc["fee"][t] / YEAR
        if credit_hedge:                                              # protection that pays the credit bucket back
            sens = mark(tables, tau0, S[t], False) - mark(tables, tau0, S[t], True)
            lam = cfg.lam0 * (S[t] / cfg.s0) ** -cfg.p
            annuity = (1 - math.exp(-(cfg.r + lam) * tau0)) / (cfg.r + lam)
            out["credit_hedge"][t] = -out["credit"][t] - sens / annuity / YEAR   # its premium, a year's worth / annuity
        if (t + 1) in coupon_days:
            out["coupon"][t] = 2.0
    out["total"] = sum(out[k] for k in keys)
    out["price0"] = mark(tables, cfg.maturity, S[0]) * (1 - cfg.new_issue)
    return out
