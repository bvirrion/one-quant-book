"""firm.decay -- how fast a predictor dies, across horizons and across years (build of One Quant Book 7, chapter 13).

IC decay curves (the IC of a signal at date t with the return of the single day t + h, for each h), the half-life of the
curve by a log-linear fit, the half-life of the signal itself from its lag-one rank autocorrelation and the implied
turnover of a portfolio that holds it, block-bootstrap intervals, the CUSUM test of Brown, Durbin and Evans for a
constant mean with its 5% boundary, the sup-F statistic for one break at an unknown date with a simulated critical
value, and the power analysis of a measured decline. NumPy only.

API (stable):
    ic_decay(signal, ret, horizons, dates)         {h: mean rank IC of signal[t] with ret[t + h]} over `dates`
    half_life_fit(horizons, ic)                     least-squares (ic0, half-life) of ic0 * 2 ** (-h / half-life)
    rank_autocorr(signal, dates, lag)               mean cross-sectional rank correlation of signal[t], signal[t - lag]
    half_life_ar(rho, lag=1)                        -lag ln 2 / ln rho
    turnover(rho)                                   1 - rho: the share of a rank-weighted book traded per period
    block_bootstrap(x, stat, block, n, seed)        bootstrap distribution of stat over moving blocks
    cusum(x)                                        (path W_t, boundary b_t): reject a constant mean if |W| > b
    sup_f(x, trim)                                  (sup F, index) for one mean break in the middle 1 - 2 trim
    sup_f_critical(n, trim, level, reps, seed)      simulated critical value of sup F under no break (Gaussian)
    sup_f_pvalue(x, trim, reps, seed)               permutation p-value of sup F (any distribution, no order)
    decline_power(ic, sd, n, ratio, reps, seed)     probabilities of a measured decline of `ratio` or more
"""
from __future__ import annotations

import math

import numpy as np


def _rank_corr(a: np.ndarray, b: np.ndarray) -> float:
    ok = ~np.isnan(a) & ~np.isnan(b)
    if ok.sum() < 3:
        return float("nan")
    ra, rb = np.argsort(np.argsort(a[ok])), np.argsort(np.argsort(b[ok]))
    return float(np.corrcoef(ra, rb)[0, 1])


def ic_decay(signal, ret, horizons, dates) -> dict:
    """signal and ret are (T, N); the IC at horizon h pairs signal[t] with the return of day t + h alone."""
    signal, ret = np.asarray(signal, float), np.asarray(ret, float)
    return {h: float(np.nanmean([_rank_corr(signal[t], ret[t + h]) for t in dates if t + h < len(ret)]))
            for h in horizons}


def half_life_fit(horizons, ic, grid=None) -> tuple[float, float]:
    """Least squares over all horizons (negative ICs included): for each half-life on a log grid the best ic0 is
    closed-form; returns the pair with the smallest squared error (the grid's top end means 'no visible decay')."""
    h, y = np.asarray(horizons, float), np.asarray(ic, float)
    grid = np.geomspace(0.1, 2000.0, 800) if grid is None else np.asarray(grid, float)
    best = (np.inf, 0.0, 0.0)
    for hl in grid:
        g = 2.0 ** (-h / hl)
        ic0 = float(g @ y / (g @ g))
        sse = float(np.sum((y - ic0 * g) ** 2))
        if sse < best[0]:
            best = (sse, ic0, float(hl))
    return best[1], best[2]


def rank_autocorr(signal, dates, lag: int = 1) -> float:
    s = np.asarray(signal, float)
    return float(np.nanmean([_rank_corr(s[t], s[t - lag]) for t in dates if t - lag >= 0]))


def half_life_ar(rho: float, lag: int = 1) -> float:
    return float(-lag * math.log(2.0) / math.log(rho)) if 0 < rho < 1 else float("inf")


def turnover(rho: float) -> float:
    return 1.0 - rho


def block_bootstrap(x, stat, block: int, n: int = 1000, seed: int = 0) -> np.ndarray:
    x = np.asarray(x)
    rng = np.random.default_rng(seed)
    T = len(x)
    k = int(np.ceil(T / block))
    out = np.empty(n)
    for i in range(n):
        starts = rng.integers(0, T - block + 1, k)
        idx = (starts[:, None] + np.arange(block)[None, :]).ravel()[:T]
        out[i] = stat(x[idx])
    return out


def cusum(x) -> tuple[np.ndarray, np.ndarray]:
    """Recursive residuals of a constant-mean model, w_t = (x_t - mean of x_1..x_{t-1}) * sqrt((t-1)/t), scaled by
    their standard deviation and cumulated; the 5% boundary is +/- 0.948 (sqrt(K) + 2 (t - k) / sqrt(K)), K the
    number of recursive residuals (Brown, Durbin and Evans)."""
    x = np.asarray(x, float)
    t = np.arange(1, len(x))
    prev_mean = np.cumsum(x)[:-1] / t
    w = (x[1:] - prev_mean) * np.sqrt(t / (t + 1.0))
    W = np.cumsum(w) / w.std(ddof=1)
    K = len(w)
    b = 0.948 * (np.sqrt(K) + 2.0 * np.arange(1, K + 1) / np.sqrt(K))
    return W, b


def sup_f(x, trim: float = 0.15) -> tuple[float, int]:
    """F statistic of a break in the mean at each split in the middle of the sample; the largest and its index."""
    x = np.asarray(x, float)
    n = len(x)
    c, c2 = np.cumsum(x), np.cumsum(x * x)
    ssr0 = c2[-1] - c[-1] ** 2 / n
    k = np.arange(int(trim * n), int((1 - trim) * n) + 1)
    ssr1 = (c2[k - 1] - c[k - 1] ** 2 / k) + (c2[-1] - c2[k - 1] - (c[-1] - c[k - 1]) ** 2 / (n - k))
    f = (ssr0 - ssr1) / (ssr1 / (n - 2))
    i = int(np.argmax(f))
    return float(f[i]), int(k[i])


def sup_f_critical(n: int, trim: float = 0.15, level: float = 0.05, reps: int = 2000, seed: int = 0) -> float:
    rng = np.random.default_rng(seed)
    return float(np.quantile([sup_f(rng.standard_normal(n), trim)[0] for _ in range(reps)], 1 - level))


def sup_f_pvalue(x, trim: float = 0.15, reps: int = 1000, seed: int = 0) -> float:
    """Share of random orderings of the same values whose sup F reaches the observed one: a test of 'no break' that
    keeps the data's own distribution (heavy tails included) and assumes only exchangeability."""
    x = np.asarray(x, float)
    rng = np.random.default_rng(seed)
    obs = sup_f(x, trim)[0]
    return float((1 + sum(sup_f(rng.permutation(x), trim)[0] >= obs for _ in range(reps))) / (reps + 1))


def decline_power(ic: float, sd: float, n: int, ratio: float = 0.5, reps: int = 100_000, seed: int = 0) -> dict:
    """Two periods of n observations each of a per-period IC with standard deviation sd. The probability that the
    second period's mean is at most `ratio` times the first's when the true IC is unchanged (bad luck), and when the
    true IC has fallen to ratio * ic (true decay)."""
    rng = np.random.default_rng(seed)
    se = sd / math.sqrt(n)
    first = ic + se * rng.standard_normal(reps)
    same = ic + se * rng.standard_normal(reps)
    fell = ratio * ic + se * rng.standard_normal(reps)
    return {"se": se, "luck": float(np.mean(same <= ratio * first)), "decay": float(np.mean(fell <= ratio * first))}
