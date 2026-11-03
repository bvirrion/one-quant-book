import numpy as np


def window_sum(v, w):
    """Sum of the last w values at each row, using only values inside that window."""
    n = len(v)
    a = np.concatenate([v, np.zeros(-n % w)]).reshape(-1, w)
    prefix = np.cumsum(a, axis=1).ravel()
    suffix = np.cumsum(a[:, ::-1], axis=1)[:, ::-1].ravel()
    out = prefix[:n].copy()                     # rows up to w - 1, and ends of blocks
    i = np.arange(w, n)
    i = i[i % w != w - 1]                       # a window spans exactly two blocks
    out[i] = suffix[i - w + 1] + prefix[i]
    return out


def rolling_beta(x, y, w, min_obs):
    """Beta of y on x over the last w rows; a row counts only if both are present."""
    ok = ~(np.isnan(x) | np.isnan(y))
    x0, y0 = np.where(ok, x, 0.0), np.where(ok, y, 0.0)
    n = window_sum(ok.astype(float), w)
    sx, sy = window_sum(x0, w), window_sum(y0, w)
    sxx, sxy = window_sum(x0 * x0, w), window_sum(x0 * y0, w)
    with np.errstate(divide="ignore", invalid="ignore"):
        beta = (n * sxy - sx * sy) / (n * sxx - sx * sx)
    return np.where(n >= min_obs, beta, np.nan)


# Not printed: the usual cumulative-sum form, for the wrong answer.
def cumsum_window_sum(v, w):
    c = np.concatenate([[0.0], np.cumsum(v)])
    c[w:] -= c[:-w].copy()
    return c[1:]
