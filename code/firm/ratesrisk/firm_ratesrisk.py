"""Rates risk: ladders, Jacobians, principal components and hedges (build of One Quant Book 6, ch. 3).

Works on any pricing function `pv(curve) -> float` and any instrument set calibrated with
`firm_curvebuild`. Sensitivities are per basis point (a bump of `bump`, scaled to 1e-4).
"""
import math
import pathlib
import sys
from collections.abc import Callable, Sequence

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "curvebuild"))
from firm_curvebuild import ZeroCurve, calibrate, with_quote  # noqa: E402

BP = 1e-4


def par_ladder(spot, instruments: Sequence, kind: str, pv: Callable, bump: float = 1e-6) -> np.ndarray:
    """Bucketed sensitivity to each input quote (recalibrate the curve), per basis point."""
    base = pv(calibrate(spot, instruments, kind).curve)
    out = []
    for k, inst in enumerate(instruments):
        sh = list(instruments)
        sh[k] = with_quote(inst, inst.quote() + bump)
        out.append((pv(calibrate(spot, sh, kind).curve) - base) * BP / bump)
    return np.array(out)


def zero_ladder(curve: ZeroCurve, pv: Callable, bump: float = 1e-6) -> np.ndarray:
    """Sensitivity to each pillar zero rate (curve not recalibrated), per basis point."""
    base = pv(curve)
    return np.array([(pv(curve.bumped(lab, bump)) - base) * BP / bump for lab in curve.labels])


def par_to_zero(g_par: np.ndarray, jacobian: np.ndarray) -> np.ndarray:
    """g_z = J^T g_q, with J = d(model quote)/d(pillar zero) at the calibrated curve."""
    return jacobian.T @ g_par


def zero_to_par(g_zero: np.ndarray, jacobian: np.ndarray) -> np.ndarray:
    return np.linalg.solve(jacobian.T, g_zero)


class TentBumped:
    """Curve whose zero rate is raised by `size` times the tent (hat) function of key rate j:
    1 at key j, falling linearly to 0 at the neighbouring keys (flat beyond the end keys).
    The tents sum to one, so key-rate sensitivities add up to the parallel one."""

    def __init__(self, base, keys: Sequence[float], j: int, size: float):
        self.base, self.keys, self.j, self.size, self.spot = base, list(keys), j, size, base.spot

    def weight(self, t: float) -> float:
        k, j = self.keys, self.j
        if t <= k[0]:
            return 1.0 if j == 0 else 0.0
        if t >= k[-1]:
            return 1.0 if j == len(k) - 1 else 0.0
        i = int(np.searchsorted(k, t))
        w = (t - k[i - 1]) / (k[i] - k[i - 1])
        return (1 - w) if j == i - 1 else (w if j == i else 0.0)

    def t(self, d) -> float:
        return self.base.t(d)

    def df_t(self, t: float) -> float:
        return self.base.df_t(t) * math.exp(-self.size * self.weight(t) * t)

    def df(self, d) -> float:
        return self.df_t(self.base.t(d))


def key_rate_ladder(curve, keys: Sequence[float], pv: Callable, bump: float = 1e-6) -> np.ndarray:
    base = pv(curve)
    return np.array([(pv(TentBumped(curve, keys, j, bump)) - base) * BP / bump for j in range(len(keys))])


def pca(changes: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Eigenvalues (descending), eigenvectors as columns, variance shares, of the covariance of
    `changes` (rows = days, columns = maturities). Signs fixed: component 1 has a positive sum,
    component 2 rises with maturity, component 3 is positive at the first maturity."""
    cov = np.cov(changes.T)
    w, v = np.linalg.eigh(cov)
    w, v = w[::-1], v[:, ::-1].copy()
    if v[:, 0].sum() < 0:
        v[:, 0] *= -1
    if v.shape[1] > 1 and v[-1, 1] < v[0, 1]:
        v[:, 1] *= -1
    if v.shape[1] > 2 and v[0, 2] < 0:
        v[:, 2] *= -1
    return w, v, w / w.sum()


def min_variance_hedge(g: np.ndarray, hedges: np.ndarray, cov: np.ndarray) -> tuple[np.ndarray, float]:
    """Quantities h of the hedge instruments (columns of `hedges` are their ladders) minimising the
    variance of (g + hedges h) . dq under covariance `cov` of the moves dq. Returns h and the share
    of the book's variance that remains."""
    a = hedges.T @ cov @ hedges
    h = -np.linalg.solve(a, hedges.T @ cov @ g)
    resid = g + hedges @ h
    return h, float(resid @ cov @ resid / (g @ cov @ g))


def cross_gamma(spot, instruments: Sequence, kind: str, pv: Callable, bump: float = 1e-4) -> np.ndarray:
    """Matrix of second derivatives of pv with respect to pairs of quotes, per bp^2 (central differences)."""
    n = len(instruments)

    def val(shifts):
        sh = [with_quote(i, i.quote() + s) for i, s in zip(instruments, shifts, strict=True)]
        return pv(calibrate(spot, sh, kind).curve)
    base = val([0.0] * n)
    g = np.zeros((n, n))
    for i in range(n):
        for j in range(i, n):
            if i == j:
                e = [0.0] * n
                e[i] = bump
                up = val(e)
                e[i] = -bump
                g[i, i] = (up - 2 * base + val(e)) / bump**2 * BP**2
            else:
                vals = []
                for si, sj in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                    e = [0.0] * n
                    e[i], e[j] = si * bump, sj * bump
                    vals.append(val(e))
                g[i, j] = g[j, i] = (vals[0] - vals[1] - vals[2] + vals[3]) / (4 * bump**2) * BP**2
    return g
