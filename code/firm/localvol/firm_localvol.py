"""Local volatility from an implied-volatility surface, and a local-volatility path generator
(build of Book 5, Chapter 9).

Dupire's formula in total implied variance w(k, T), k = ln(K / F_T):
    sigma_loc^2(k, T) = dw/dT / g(k),
where g is the butterfly density factor of Chapter 7: the denominator is positive exactly when the
slice is free of butterfly arbitrage, and the numerator when it is free of calendar arbitrage.
Derivatives are central differences of any smooth w(k, t) (SSVI, SVI slices, a spline surface).
"""
import math
import pathlib
import sys
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "volsurface"))
from firm_volsurface import density_factor  # noqa: E402


def local_variance(w_fn: Callable[[float, float], float], k: float, t: float, dk: float = 1e-4,
                   dt: float = 1e-5) -> float:
    """sigma_loc^2 at log-moneyness k and time t from a total-variance function w_fn(k, t)."""
    w = w_fn(k, t)
    wk = (w_fn(k + dk, t) - w_fn(k - dk, t)) / (2 * dk)
    wkk = (w_fn(k + dk, t) - 2 * w + w_fn(k - dk, t)) / (dk * dk)
    wt = (w_fn(k, t + dt) - w_fn(k, t - dt)) / (2 * dt)
    g = density_factor(w, wk, wkk, k)
    if g <= 0 or wt < 0:
        raise ValueError(f"arbitrage in the surface at k={k}, t={t}: g={g}, dw/dt={wt}")
    return wt / g


@dataclass(frozen=True)
class LocalVolGrid:
    """Local volatility on a grid of times and log-moneyness k = ln(S / F_ref(t)) against the forward of
    the calibration date, so that the function is fixed in absolute spot: a later spot move reads it at a
    different k. Linear interpolation in t and k, flat beyond the grid."""
    times: np.ndarray
    ks: np.ndarray
    vol: np.ndarray                                    # vol[i, j] at times[i], ks[j]
    s_ref: float = 100.0
    carry: float = 0.0                                 # r - q of the calibration forward F_ref(t) = s_ref e^{carry t}

    def sigma(self, t: float, s: np.ndarray) -> np.ndarray:
        k = np.log(s / (self.s_ref * math.exp(self.carry * t)))
        i = int(np.searchsorted(self.times, t))
        if i <= 0 or i >= len(self.times):
            return np.interp(k, self.ks, self.vol[min(max(i, 0), len(self.times) - 1)])
        w = (t - self.times[i - 1]) / (self.times[i] - self.times[i - 1])
        return (1 - w) * np.interp(k, self.ks, self.vol[i - 1]) + w * np.interp(k, self.ks, self.vol[i])


def build_grid(w_fn, times, ks, s_ref: float = 100.0, carry: float = 0.0) -> LocalVolGrid:
    times, ks = np.asarray(times, float), np.asarray(ks, float)
    vol = np.array([[math.sqrt(local_variance(w_fn, float(k), float(t))) for k in ks] for t in times])
    return LocalVolGrid(times, ks, vol, s_ref, carry)


def simulate(grid: LocalVolGrid, s0: float, horizon: float, steps: int, n_paths: int, seed: int,
             record: tuple[float, ...] = ()):
    """Log-Euler scheme dlnS = (carry - sigma^2/2) dt + sigma(t, S) dW, sigma read at mid-step, with
    antithetic pairs. Returns terminal spots and a dict of spots at the recorded times."""
    rng = np.random.default_rng(seed)
    dt = horizon / steps
    half = n_paths // 2
    x = np.full(2 * half, math.log(s0))
    rec = {}
    targets = {round(r / dt): r for r in record}
    for n in range(steps):
        z = rng.standard_normal(half)
        z = np.concatenate([z, -z])
        sig = grid.sigma((n + 0.5) * dt, np.exp(x))
        x = x + (grid.carry - 0.5 * sig * sig) * dt + sig * math.sqrt(dt) * z
        if n + 1 in targets:
            rec[targets[n + 1]] = np.exp(x)
    return np.exp(x), rec
