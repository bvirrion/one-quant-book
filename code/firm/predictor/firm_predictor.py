"""firm.predictor -- predictors, targets and the information coefficient (build of One Quant Book 7, chapter 6).

Everything here works on panels: arrays of shape (dates, names), NaN where a name is absent. A predictor value at
row t is known at the close of date t; a target at row t is the return it is meant to predict, over dates
t + 1 .. t + h. Normalisers and neutralisation act on each date's cross-section; the IC engine correlates each
date's predictor with its target and summarises the series with standard errors that respect overlapping targets.
NumPy only.

API (stable):
    forward_return(ret, h)                          compounded return over t+1..t+h (NaN if any day is missing)
    excess(target, market)                          target minus a per-date market return (T,) or (T, N)
    residualise(y, X)                               per-date OLS residual of y (T, N) on exposures X (T, N, K) or (N, K)
    zscore(x, clip=3.0)                             per-date z-score, clipped at +-clip
    rank_transform(x)                               per-date ranks mapped to (-0.5, 0.5)
    neutralise(x, X)                                = residualise, for predictors
    ic_series(signal, target, method)               per-date Pearson or Spearman ("rank") correlation
    ic_summary(ic, h=1, periods=252)                dict(mean, sd, icir, icir_annual, t_naive, t_hac, n)
    quantile_spread(signal, target, q=5)            per-date mean target of the top minus the bottom quantile
    PredictorCard                                   the record every predictor of the book fills
"""
from __future__ import annotations

import math
import pathlib
import sys
from dataclasses import dataclass, field

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "estim"))
from firm_estim import long_run_variance  # noqa: E402


def forward_return(ret: np.ndarray, h: int) -> np.ndarray:
    ret = np.asarray(ret, float)
    T = ret.shape[0]
    lr = np.log1p(ret)
    out = np.full(ret.shape, np.nan)
    cs = np.concatenate([np.zeros((1,) + ret.shape[1:]), np.cumsum(np.nan_to_num(lr), axis=0)])
    nan_cs = np.concatenate([np.zeros((1,) + ret.shape[1:]), np.cumsum(np.isnan(lr), axis=0)])
    for t in range(T - h):
        s = cs[t + 1 + h] - cs[t + 1]
        bad = (nan_cs[t + 1 + h] - nan_cs[t + 1]) > 0
        out[t] = np.where(bad, np.nan, np.expm1(s))
    return out


def excess(target: np.ndarray, market) -> np.ndarray:
    m = np.asarray(market, float)
    return target - (m[:, None] if m.ndim == 1 else m)


def residualise(y: np.ndarray, X: np.ndarray) -> np.ndarray:
    """Per date, the residual of y on a constant and the exposures (names with any missing value are skipped)."""
    y = np.asarray(y, float)
    out = np.full(y.shape, np.nan)
    for t in range(y.shape[0]):
        Xt = X[t] if X.ndim == 3 else X
        Xt = np.column_stack([np.ones(y.shape[1]), Xt])
        ok = ~np.isnan(y[t]) & ~np.isnan(Xt).any(axis=1)
        if ok.sum() <= Xt.shape[1] + 1:
            continue
        b = np.linalg.lstsq(Xt[ok], y[t, ok], rcond=None)[0]
        out[t, ok] = y[t, ok] - Xt[ok] @ b
    return out


neutralise = residualise


def zscore(x: np.ndarray, clip: float | None = 3.0) -> np.ndarray:
    x = np.asarray(x, float)
    mu = np.nanmean(x, axis=1, keepdims=True)
    sd = np.nanstd(x, axis=1, keepdims=True)
    z = (x - mu) / np.where(sd > 0, sd, np.nan)
    return np.clip(z, -clip, clip) if clip else z


def rank_transform(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, float)
    out = np.full(x.shape, np.nan)
    for t in range(x.shape[0]):
        ok = ~np.isnan(x[t])
        n = ok.sum()
        if n:
            r = np.argsort(np.argsort(x[t, ok]))
            out[t, ok] = (r + 0.5) / n - 0.5
    return out


def ic_series(signal: np.ndarray, target: np.ndarray, method: str = "rank", min_names: int = 20) -> np.ndarray:
    s, y = np.asarray(signal, float), np.asarray(target, float)
    out = np.full(s.shape[0], np.nan)
    for t in range(s.shape[0]):
        ok = ~np.isnan(s[t]) & ~np.isnan(y[t])
        if ok.sum() < min_names:
            continue
        a, b = s[t, ok], y[t, ok]
        if method == "rank":
            a, b = np.argsort(np.argsort(a)).astype(float), np.argsort(np.argsort(b)).astype(float)
        if a.std() == 0 or b.std() == 0:
            continue
        out[t] = np.corrcoef(a, b)[0, 1]
    return out


def ic_summary(ic, h: int = 1, periods: int = 252) -> dict:
    """Mean IC and its t-statistics: naive (as if the dates were independent) and Newey-West with h - 1 lags,
    the right correction when h-day targets overlap on consecutive dates. The IC information ratio is the mean
    over the standard deviation; its annual version scales by sqrt(periods / h)."""
    x = np.asarray(ic, float)
    x = x[~np.isnan(x)]
    n = len(x)
    mean, sd = float(x.mean()), float(x.std(ddof=1))
    se_naive = sd / math.sqrt(n)
    se_hac = math.sqrt(long_run_variance(x, max(0, h - 1)) / n) if h > 1 else se_naive
    return {"mean": mean, "sd": sd, "icir": mean / sd, "icir_annual": mean / sd * math.sqrt(periods / h),
            "t_naive": mean / se_naive, "t_hac": mean / se_hac, "n": n}


def quantile_spread(signal: np.ndarray, target: np.ndarray, q: int = 5, min_names: int = 20) -> np.ndarray:
    s, y = np.asarray(signal, float), np.asarray(target, float)
    out = np.full(s.shape[0], np.nan)
    for t in range(s.shape[0]):
        ok = ~np.isnan(s[t]) & ~np.isnan(y[t])
        if ok.sum() < max(min_names, 2 * q):
            continue
        a, b = s[t, ok], y[t, ok]
        order = np.argsort(a)
        k = len(a) // q
        out[t] = b[order[-k:]].mean() - b[order[:k]].mean()
    return out


@dataclass
class PredictorCard:
    """The fields of a predictor card (One Quant Book 7, chapter 6); `stats` holds the measured numbers."""
    name: str
    definition: str
    inputs: str                       # the data used, each with its knowledge time
    rationale: str
    horizon: int                      # trading days of the target
    normalisation: str
    failure_modes: str
    sources: str
    half_life: float | None = None    # days, measured in chapter 13's way
    stats: dict = field(default_factory=dict)

    def fields(self) -> list[tuple[str, str]]:
        hl = "not yet measured" if self.half_life is None else f"{self.half_life:.0f} days"
        return [("Definition", self.definition), ("Inputs and timestamps", self.inputs),
                ("Rationale", self.rationale), ("Horizon and half-life", f"{self.horizon} days; {hl}"),
                ("Normalisation", self.normalisation), ("Failure modes", self.failure_modes),
                ("Sources", self.sources)]
