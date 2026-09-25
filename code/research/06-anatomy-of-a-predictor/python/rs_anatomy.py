"""Anatomy of a predictor (One Quant Book 7, chapter 6).

One predictor, five-day reversal (minus the last five days' return), measured on firm.synthmkt against three
targets over the next five days: the raw return, the return in excess of the equal-weighted market, and the residual
after the market beta and the industries. The same predictor, neutralised to industries; the rank IC, its
information ratio and its t-statistics, with and without the correction for overlapping targets; quintile spreads.
NumPy only.
"""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("synthmkt", "predictor"):
    sys.path.insert(0, str(ROOT / c))
from firm_predictor import (  # noqa: E402
    PredictorCard,
    excess,
    forward_return,
    ic_series,
    ic_summary,
    neutralise,
    quantile_spread,
    rank_transform,
    residualise,
)
from firm_synthmkt import MarketConfig, simulate  # noqa: E402

H = 5
BURN = 21


@functools.lru_cache(maxsize=1)
def panel():
    return simulate(MarketConfig())


def exposures(p) -> np.ndarray:
    """Per-name exposures used to neutralise: market beta and industry dummies (one dropped)."""
    K = p.cfg.n_industries
    d = np.eye(K)[p.industry][:, 1:]
    return np.column_stack([p.beta, d])


def past_return(ret, h):
    """Compounded return over t-h+1..t, known at the close of t."""
    lr = np.log1p(ret)
    out = np.full(ret.shape, np.nan)
    cs = np.cumsum(np.nan_to_num(lr), axis=0)
    miss = np.cumsum(np.isnan(lr), axis=0)
    out[h:] = np.where(miss[h:] - miss[:-h] > 0, np.nan, np.expm1(cs[h:] - cs[:-h]))
    return out


def horizon_ics(p=None, signal_days=(1, 5), target_days=(1, 5)):
    """Mean rank IC of the reversal over s days against the return over the next t days, for each pair (s, t)."""
    p = p or panel()
    ret = np.where(p.listed, p.ret, np.nan)
    out = {}
    for hs in signal_days:
        sig = -past_return(ret, hs)
        for ht in target_days:
            st = ic_summary(ic_series(sig[BURN:], forward_return(ret, ht)[BURN:], "rank"), h=ht)
            out[(hs, ht)] = (st["mean"], st["t_hac"])
    return out


def lag_profile(ks=range(1, 11), p=None):
    """Mean rank IC of the one-day reversal at the close of t against the single-day return of t + k."""
    p = p or panel()
    ret = np.where(p.listed, p.ret, np.nan)
    sig = -ret
    return {k: ic_summary(ic_series(sig[BURN:-k], ret[BURN + k:], "rank"))["mean"] for k in ks}


def neutralisation(p) -> dict:
    """Five-day reversal against five-day targets in panel p: raw/raw, raw/residual, neutral/residual, and the
    share of the target's cross-sectional variance left in the residual."""
    ret = np.where(p.listed, p.ret, np.nan)
    X = exposures(p)
    s, y = -past_return(ret, H), forward_return(ret, H)
    yr = residualise(y, X)
    out = {name: ic_summary(ic_series(a[BURN:], b[BURN:], "rank"), h=H)
           for name, a, b in (("raw", s, y), ("residual", s, yr), ("neutral", neutralise(s, X), yr))}
    with np.errstate(all="ignore"):
        out["share"] = float(np.nanmean(np.nanvar(yr[BURN:-H], axis=1)) / np.nanmean(np.nanvar(y[BURN:-H], axis=1)))
    return out


@functools.lru_cache(maxsize=1)
def study():
    p = panel()
    ret = np.where(p.listed, p.ret, np.nan)
    X = exposures(p)
    signal = -past_return(ret, H)
    fwd = forward_return(ret, H)
    with np.errstate(all="ignore"):
        ew = np.nanmean(fwd, axis=1)
    targets = {"raw": fwd, "excess": excess(fwd, ew), "residual": residualise(fwd, X)}
    sig_n = neutralise(signal, X)
    out = {}
    for name, y in targets.items():
        ic = ic_series(rank_transform(signal[BURN:]), y[BURN:], "rank")
        out[name] = ic_summary(ic, h=H)
    out["neutral_residual"] = ic_summary(ic_series(sig_n[BURN:], targets["residual"][BURN:], "rank"), h=H)
    # the same IC read every H days (non-overlapping) for comparison
    nonov = ic_series(signal[BURN::H], targets["residual"][BURN::H], "rank")
    out["residual_every_h"] = ic_summary(nonov, h=1, periods=252 // H)
    qs = quantile_spread(sig_n[BURN:], targets["residual"][BURN:], 5)
    out["quintile_spread_5d"] = float(np.nanmean(qs))
    with np.errstate(all="ignore"):
        out["share_residual_var"] = float(np.nanmean(np.nanvar(targets["residual"][BURN:-H], axis=1))
                                          / np.nanmean(np.nanvar(fwd[BURN:-H], axis=1)))
    return out


def card() -> PredictorCard:
    p = panel()
    ret = np.where(p.listed, p.ret, np.nan)
    st = ic_summary(ic_series(neutralise(-ret, exposures(p))[BURN:-1], ret[BURN + 1:], "rank"))
    lp = lag_profile(range(1, 3))
    hl = float(np.log(0.5) / np.log(max(lp[2], 1e-6) / lp[1])) if lp[2] > 0 else None
    return PredictorCard(
        name="one-day reversal",
        definition="minus the day's return, ranked, neutralised to beta and industries",
        inputs="the close of the decision day and the previous close; betas and industries as of that day",
        rationale="liquidity providers are paid to absorb demand for immediacy; the price pressure reverts",
        horizon=1, normalisation="cross-sectional rank, then residual on beta and industry dummies",
        failure_modes="moves on news (earnings days) do not revert; trading costs of a daily signal; crowding",
        sources="Jegadeesh (1990); Lehmann (1990); the chapter's measurement on firm.synthmkt",
        half_life=hl, stats={"ic": st["mean"], "icir_annual": st["icir_annual"], "t": st["t_hac"],
                             "ic_lag1": lp[1], "ic_lag2": lp[2]})
