"""firm.mmattrib -- daily P&L attribution and the strategy lifecycle (One Quant Book 11, chapter 28).

Built on Book 7's firm.abtest (randomised assignment, differences in means, CUPED). A market maker trades on two
venues. Each day and venue its expected P&L is market volume x its share x (capture ratio x market half-spread -
adverse selection), all per share, plus inventory noise; fees and rebates are folded into the capture ratio. A year of
252 days in months of 21 has planted events: the half-spread narrows and market volume rises in month 9; a
competitor arrives on venue B on a given day (our share and capture ratio there fall); a parameter change, run as a
randomised experiment on the days after it, raises our share and our adverse selection on both venues.

API (stable):
    Year(seed, ...)                         daily arrays by venue: market volume, half-spread, share, capture ratio,
                                            adverse selection, treated flag, P&L and its parts
    attribution(year) -> dict               daily capture, adverse selection, inventory and total, by venue
    cusum_down(x, target, k, h) -> int      first day a one-sided CUSUM of target - x exceeds h (-1 if none)
    experiment(year, first, last) -> dict   the parameter's effect on daily P&L by difference in means and by CUPED
                                            (market volume as the covariate), and on share and adverse selection
    month_change(year, m0, m1, est) -> dict the change in P&L from month m0 to m1 split into spread, volume,
                                            competition, parameter and residual, from estimates (est) or the truth
    retire_day(pnl, window, floor) -> int   first day the rolling mean of daily P&L falls below floor (-1 if none)
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "abtest"))
import firm_abtest as ab  # noqa: E402

MONTH = 21


class Year:
    def __init__(self, seed: int = 0, days: int = 252, mv=(2.0e7, 1.5e7), share=(0.10, 0.12), kappa=(0.8, 0.8),
                 half=1.0, adverse=(0.35, 0.35), spread_cut: float = 0.10, volume_rise: float = 0.15,
                 comp_day: int = 175, comp_share: float = 0.30, comp_kappa: float = 0.15, param_day: int = 182,
                 param_share: float = 0.10, param_adverse: float = 0.10, noise_mv: float = 0.10,
                 noise_half: float = 0.05, inv_sd: float = 3000.0):
        rng = np.random.default_rng(seed)
        d = np.arange(days)
        month = d // MONTH
        self.days, self.month = days, month
        m9 = month == 8                                  # month 9 (zero-based 8)
        shock = np.exp(noise_mv * rng.standard_normal((days, 2)))
        self.mv = np.array(mv)[None, :] * (1 + volume_rise * m9)[:, None] * shock
        self.half = half * (1 - spread_cut * m9) * np.exp(noise_half * rng.standard_normal(days))
        self.share = np.tile(np.array(share, float), (days, 1))
        self.kappa = np.tile(np.array(kappa, float), (days, 1))
        self.adverse = np.tile(np.array(adverse, float), (days, 1))
        comp = d >= comp_day
        self.share[comp, 1] *= 1 - comp_share
        self.kappa[comp, 1] *= 1 - comp_kappa
        self.treated = np.zeros(days, bool)
        after = d >= param_day
        self.treated[after] = ab.assign([f"day{i}" for i in d[after]], "param", 0.5)
        self.share[self.treated] *= 1 + param_share
        self.adverse[self.treated] += param_adverse
        self.inv = inv_sd * rng.standard_normal((days, 2))
        self.cfg = dict(spread_cut=spread_cut, volume_rise=volume_rise, comp_day=comp_day, comp_share=comp_share,
                        comp_kappa=comp_kappa, param_day=param_day, param_share=param_share,
                        param_adverse=param_adverse, share=share, kappa=kappa, adverse=adverse, mv=mv, half=half)
        vol = self.mv * self.share                        # our shares traded
        self.capture = vol * self.kappa * self.half[:, None] / 100.0          # dollars (half-spread in cents)
        self.adv_cost = vol * self.adverse / 100.0
        self.pnl = self.capture - self.adv_cost + self.inv


def attribution(y: Year) -> dict:
    return {"capture": y.capture, "adverse": -y.adv_cost, "inventory": y.inv, "total": y.pnl,
            "capture_ratio_obs": y.capture / (y.mv * y.share * y.half[:, None] / 100.0)}


def cusum_down(x, target: float, k: float, h: float) -> int:
    s = 0.0
    for i, v in enumerate(np.asarray(x, float)):
        s = max(0.0, s + (target - v) - k)
        if s > h:
            return i
    return -1


def experiment(y: Year, first: int, last: int) -> dict:
    sel = np.arange(y.days)
    sel = sel[(sel >= first) & (sel <= last)]
    t = y.treated[sel]
    tot = y.pnl[sel].sum(axis=1)
    mvx = y.mv[sel].sum(axis=1)
    d, se = ab.diff_means(tot, t)
    dc, sec, _ = ab.cuped(tot, mvx[:, None], t)
    share = y.share[sel]
    adv = y.adverse[sel]
    return {"effect": d, "se": se, "cuped": dc, "cuped_se": sec,
            "share_mult": float(share[t].mean(axis=0).mean() / share[~t].mean(axis=0).mean()),
            "adverse_add": float(adv[t].mean() - adv[~t].mean()), "n_treated": int(t.sum()), "n": len(sel)}


def month_change(y: Year, m0: int, m1: int, est: dict | None = None) -> dict:
    """Sequential attribution of E[P&L(m1)] - E[P&L(m0)] (and the realised change): the half-spread, then market
    volume, then the competitor on venue B, then the parameter. `est` (from the chapter's estimates) supplies
    comp_share, comp_kappa, param_share_mult and param_adverse_add; without it the planted truth is used. The spread
    and volume changes are measured from market data in both cases."""
    c = y.cfg
    a, b = y.month == m0, y.month == m1
    n1 = int(b.sum())
    half0, half1 = y.half[a].mean(), y.half[b].mean()
    mv0, mv1 = y.mv[a].mean(axis=0), y.mv[b].mean(axis=0)
    base = a & ~y.treated
    share0, kappa0, adv0 = y.share[base].mean(axis=0), y.kappa[a].mean(axis=0), y.adverse[base].mean(axis=0)
    if est is None:
        cs, ck, ps, pa = c["comp_share"], c["comp_kappa"], c["param_share"] + 1.0, c["param_adverse"]
    else:
        cs, ck, ps, pa = est["comp_share"], est["comp_kappa"], est["param_share_mult"], est["param_adverse_add"]
    days = np.arange(y.days)[b]
    comp_day = c["comp_day"] if est is None else est.get("comp_day", c["comp_day"])
    comp_frac = float(np.mean(days >= comp_day))
    treat_frac = float(np.mean(y.treated[b]))

    def total(half, mv, share, kappa, adverse):
        return n1 * float(np.sum(mv * share * (kappa * half - adverse) / 100.0))

    s0 = total(half0, mv0, share0, kappa0, adv0) * int(a.sum()) / n1
    s1 = total(half1, mv0, share0, kappa0, adv0)
    s2 = total(half1, mv1, share0, kappa0, adv0)
    share_c = share0.copy()
    kappa_c = kappa0.copy()
    share_c[1] *= 1 - cs * comp_frac
    kappa_c[1] *= 1 - ck * comp_frac
    s3 = total(half1, mv1, share_c, kappa_c, adv0)
    share_p = share_c * (1 + (ps - 1) * treat_frac)
    adv_p = adv0 + pa * treat_frac
    s4 = total(half1, mv1, share_p, kappa_c, adv_p)
    realised = float(y.pnl[b].sum() - y.pnl[a].sum() * n1 / int(a.sum()))
    parts = {"spread": s1 - s0, "volume": s2 - s1, "competition": s3 - s2, "parameter": s4 - s3}
    return {**parts, "explained": s4 - s0, "realised": realised, "residual": realised - (s4 - s0)}


def retire_day(pnl, window: int = 60, floor: float = 0.0) -> int:
    x = np.asarray(pnl, float)
    c = np.convolve(x, np.ones(window) / window, mode="valid")
    idx = np.where(c < floor)[0]
    return int(idx[0] + window - 1) if len(idx) else -1
