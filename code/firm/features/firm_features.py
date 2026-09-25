"""firm.features -- bar features, point-in-time safe (build of One Quant Book 7, chapter 7).

Every function takes panels (dates, names) of bar data and returns a panel whose row t uses only rows <= t. The
leakage test perturbs every row after a cut-off and checks that no row up to the cut-off changes: a feature that
fails it looks into the future. NumPy only.

API (stable):
    past_return(ret, window, skip=0)       compounded return over t-skip-window+1 .. t-skip
    rolling_vol(ret, window)               standard deviation of the last `window` returns
    ewma_vol(ret, half_life)               exponentially weighted volatility
    parkinson(high, low)                   daily variance estimate (ln H/L)^2 / (4 ln 2)
    garman_klass(open_, high, low, close)  0.5 (ln H/L)^2 - (2 ln 2 - 1) (ln C/O)^2
    rogers_satchell(open_, high, low, close)   ln(H/C) ln(H/O) + ln(L/C) ln(L/O)
    yang_zhang(open_, high, low, close, window)  overnight + k open-to-close + (1 - k) Rogers-Satchell variance
    volume_surprise(volume, window)        ln(volume_t / mean of the previous `window` volumes)
    amihud(ret, dollar_volume, window)     mean of |r| / dollar volume over the window
    turnover(volume, shares, window)       mean volume / shares outstanding
    ma_crossover(price, short, long)       ln(mean of last `short` prices / mean of last `long` prices)
    crossover_weights(short, long)         the (approximate) weights the crossover puts on each past log return
    leakage_test(feature, inputs, cut)     True if rows <= cut are unchanged when rows > cut are perturbed
"""
from __future__ import annotations

import math

import numpy as np


def _rolling_sum(x: np.ndarray, w: int) -> np.ndarray:
    """Sum of the last w rows (NaN until w rows exist or if any is NaN)."""
    x = np.asarray(x, float)
    cs = np.concatenate([np.zeros((1,) + x.shape[1:]), np.cumsum(np.nan_to_num(x), axis=0)])
    miss = np.concatenate([np.zeros((1,) + x.shape[1:]), np.cumsum(np.isnan(x), axis=0)])
    out = np.full(x.shape, np.nan)
    out[w - 1:] = cs[w:] - cs[:-w]
    bad = np.zeros(x.shape, bool)
    bad[w - 1:] = (miss[w:] - miss[:-w]) > 0
    out[bad] = np.nan
    return out


def _shift(x: np.ndarray, k: int) -> np.ndarray:
    out = np.full(x.shape, np.nan)
    if k == 0:
        return np.array(x, float)
    out[k:] = x[:-k]
    return out


def past_return(ret, window: int, skip: int = 0) -> np.ndarray:
    lr = np.log1p(np.asarray(ret, float))
    return np.expm1(_shift(_rolling_sum(lr, window), skip))


def rolling_vol(ret, window: int) -> np.ndarray:
    r = np.asarray(ret, float)
    m = _rolling_sum(r, window) / window
    m2 = _rolling_sum(r * r, window) / window
    return np.sqrt(np.maximum(m2 - m * m, 0.0) * window / (window - 1))


def ewma_vol(ret, half_life: float) -> np.ndarray:
    r = np.asarray(ret, float)
    lam = 0.5 ** (1.0 / half_life)
    out = np.full(r.shape, np.nan)
    v = np.full(r.shape[1:], np.nan)
    for t in range(r.shape[0]):
        x2 = r[t] * r[t]
        v = np.where(np.isnan(v), x2, np.where(np.isnan(x2), v, lam * v + (1 - lam) * x2))
        out[t] = np.sqrt(v)
    return out


def parkinson(high, low):
    return np.log(np.asarray(high) / np.asarray(low)) ** 2 / (4.0 * math.log(2.0))


def garman_klass(open_, high, low, close):
    hl = np.log(np.asarray(high) / np.asarray(low))
    co = np.log(np.asarray(close) / np.asarray(open_))
    return 0.5 * hl * hl - (2.0 * math.log(2.0) - 1.0) * co * co


def rogers_satchell(open_, high, low, close):
    o, h, lo, c = (np.asarray(x, float) for x in (open_, high, low, close))
    return np.log(h / c) * np.log(h / o) + np.log(lo / c) * np.log(lo / o)


def yang_zhang(open_, high, low, close, window: int):
    """Yang-Zhang variance over `window` days (arrays of length days, or days x names): the previous close is the
    close of the row before, so the first row has no overnight return."""
    o, c = np.asarray(open_, float), np.asarray(close, float)
    overnight = np.log(o[1:] / c[:-1])
    oc = np.log(c[1:] / o[1:])
    rs = rogers_satchell(o[1:], np.asarray(high)[1:], np.asarray(low)[1:], c[1:])
    n = window
    k = 0.34 / (1.34 + (n + 1) / (n - 1))

    def var(x):
        m = _rolling_sum(x, n) / n
        return (_rolling_sum(x * x, n) - n * m * m) / (n - 1)

    out = var(overnight) + k * var(oc) + (1 - k) * _rolling_sum(rs, n) / n
    return np.concatenate([np.full((1,) + out.shape[1:], np.nan), out])


def volume_surprise(volume, window: int) -> np.ndarray:
    v = np.asarray(volume, float)
    base = _shift(_rolling_sum(v, window) / window, 1)
    return np.log(v / base)


def amihud(ret, dollar_volume, window: int) -> np.ndarray:
    x = np.abs(np.asarray(ret, float)) / np.asarray(dollar_volume, float)
    return _rolling_sum(x, window) / window


def turnover(volume, shares, window: int) -> np.ndarray:
    return _rolling_sum(np.asarray(volume, float) / np.asarray(shares, float), window) / window


def ma_crossover(price, short: int, long: int) -> np.ndarray:
    p = np.asarray(price, float)
    return np.log((_rolling_sum(p, short) / short) / (_rolling_sum(p, long) / long))


def crossover_weights(short: int, long: int) -> np.ndarray:
    """Weights w_j on the log return of j days ago (j = 0 .. long - 2) such that, to first order,
    ln(MA_short / MA_long) = sum_j w_j r_{t-j}: w_j = min(j + 1, long - ... ) derived from averaging log prices."""
    j = np.arange(long - 1)
    # mean of the last n log prices = log p_t - sum_{j < n - 1} (n - 1 - j) / n * r_{t-j}
    ws = np.where(j < short - 1, (short - 1 - j) / short, 0.0)
    wl = (long - 1 - j) / long
    return wl - ws


def leakage_test(feature, inputs: tuple, cut: int, seed: int = 0) -> bool:
    """Apply `feature(*inputs)`, then again with every row after `cut` of every input multiplied by random factors;
    rows 0..cut of the output must be identical (NaN where NaN)."""
    rng = np.random.default_rng(seed)
    a = feature(*inputs)
    pert = []
    for x in inputs:
        y = np.array(x, float, copy=True)
        y[cut + 1:] = y[cut + 1:] * rng.uniform(0.5, 1.5, y[cut + 1:].shape)
        pert.append(y)
    b = feature(*pert)
    return bool(np.array_equal(np.nan_to_num(a[: cut + 1], nan=-9e9), np.nan_to_num(b[: cut + 1], nan=-9e9)))
