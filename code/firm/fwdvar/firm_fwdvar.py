"""Forward variance and rough volatility (build of Book 5, Chapter 12).

Three tools:

* the forward-variance curve xi0(u), read from variance-swap volatilities or from the log-contract strip of
  one smile per expiry;
* the rough Bergomi model of Bayer, Friz and Gatheral (2016),
      v_t = xi0(t) exp(eta Y_t - eta^2 t^(2H) / 2),   Y_t = sqrt(2H) int_0^t (t - s)^(H - 1/2) dW1_s,
      dS_t / S_t = sqrt(v_t) (rho dW1_t + sqrt(1 - rho^2) dWperp_t),
  simulated exactly on a grid (Cholesky of the joint law of Y and W1; the hybrid scheme of Bennedsen, Lunde
  and Pakkanen is the O(n log n) alternative for long grids), with smiles by the mixing formula and the VIX;
* a roughness estimator: the slope of log E|x_{t+lag} - x_t|^q against log lag, divided by q.
"""
import math
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "bs"))
from firm_bs import black, implied_vol  # noqa: E402

_ERFC = np.frompyfunc(math.erfc, 1, 1)


def ncdf(x: np.ndarray) -> np.ndarray:
    """Standard normal cdf on arrays (math.erfc, element by element)."""
    return 0.5 * _ERFC(-np.asarray(x, float) / math.sqrt(2.0)).astype(float)


# ---------------------------------------------------------------- the forward-variance curve
def log_strip_variance(vol_of_k, t: float, n: int = 4001) -> float:
    """Fair annualised variance of the log contract, forward 1 and zero rates:
    (2 / T) int OTM(k) e^(-k) dk over log-moneyness k = ln(K / F), OTM = put below the forward, call above."""
    width = max(1.0, 10.0 * vol_of_k(0.0) * math.sqrt(t))
    ks = np.linspace(-width, width, n)
    otm = np.array([black(1.0, math.exp(k), t, 1.0, vol_of_k(k), "P" if k < 0 else "C") for k in ks])
    f = otm * np.exp(-ks)
    return float(2.0 / t * np.sum(0.5 * (f[1:] + f[:-1]) * np.diff(ks)))


@dataclass(frozen=True)
class ForwardVarianceCurve:
    """Total variance w(T) = T sigma_VS(T)^2 at pillar expiries, linear in between: the forward variance
    xi0(u) = dw/du is piecewise constant, and flat beyond the last pillar."""
    times: tuple[float, ...]
    total: tuple[float, ...]

    @classmethod
    def from_vs_vols(cls, times, vols) -> "ForwardVarianceCurve":
        return cls(tuple(float(t) for t in times), tuple(float(v * v * t) for t, v in zip(times, vols, strict=True)))

    def _knots(self) -> tuple[np.ndarray, np.ndarray]:
        return np.concatenate([[0.0], self.times]), np.concatenate([[0.0], self.total])

    def xi(self, u: float) -> float:
        ts, ws = self._knots()
        i = min(max(int(np.searchsorted(ts, u, side="left")), 1), len(ts) - 1)
        return float((ws[i] - ws[i - 1]) / (ts[i] - ts[i - 1]))

    def total_variance(self, t: float) -> float:
        ts, ws = self._knots()
        if t <= ts[-1]:
            return float(np.interp(t, ts, ws))
        return float(ws[-1] + self.xi(ts[-1]) * (t - ts[-1]))

    def vs_vol(self, t: float) -> float:
        return math.sqrt(self.total_variance(t) / t)

    def forward_vol(self, t1: float, t2: float) -> float:
        """Volatility of a variance swap starting at t1 and ending at t2, as seen today."""
        return math.sqrt((self.total_variance(t2) - self.total_variance(t1)) / (t2 - t1))

    def negative_intervals(self) -> list[tuple[float, float]]:
        """Pillar intervals on which total variance falls: a calendar arbitrage in variance swaps."""
        ts, ws = self._knots()
        return [(float(ts[i - 1]), float(ts[i])) for i in range(1, len(ts)) if ws[i] < ws[i - 1]]


# ---------------------------------------------------------------- rough Bergomi: the Gaussian skeleton
def _g_ratio(x: np.ndarray, hurst: float, m: int = 200) -> np.ndarray:
    """G(x) = 2H int_0^1 (1 - s)^(H - 1/2) (x - s)^(H - 1/2) ds for x >= 1, so that
    Cov(Y_u, Y_v) = u^(2H) G(v / u) for u <= v. The substitution 1 - s = z^p, p = 1 / H, removes the
    singularity at s = 1."""
    z, wts = np.polynomial.legendre.leggauss(m)
    z, wts = 0.5 * (z + 1.0), 0.5 * wts
    p, a = 1.0 / hurst, hurst - 0.5
    x = np.asarray(x, float)[..., None]
    integrand = p * z ** (p * (hurst + 0.5) - 1.0) * (x - 1.0 + z ** p) ** a
    return 2.0 * hurst * np.sum(integrand * wts, axis=-1)


def joint_cov(times, hurst: float) -> np.ndarray:
    """Covariance of (Y_{t_1..t_n}, W1_{t_1..t_n}), a 2n x 2n matrix."""
    t = np.asarray(times, float)
    lo, hi = np.minimum.outer(t, t), np.maximum.outer(t, t)
    cyy = lo ** (2 * hurst) * _g_ratio(hi / lo, hurst)
    c = math.sqrt(2 * hurst) / (hurst + 0.5)
    cyw = c * (t[:, None] ** (hurst + 0.5) - (t[:, None] - lo) ** (hurst + 0.5))   # Cov(Y_{t_i}, W_{t_j})
    return np.block([[cyy, cyw], [cyw.T, lo]])


def _chol(c: np.ndarray) -> np.ndarray:
    """Cholesky factor; a diagonal jitter (relative 1e-14, growing tenfold) only if rounding breaks it."""
    scale, eps = np.trace(c) / len(c), 0.0
    while True:
        try:
            return np.linalg.cholesky(c + eps * scale * np.eye(len(c)))
        except np.linalg.LinAlgError:
            eps = 1e-14 if eps == 0.0 else 10 * eps


def rbergomi_integrals(xi0, hurst: float, eta: float, t: float, steps: int, n_paths: int,
                       seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Per path, the Ito sum I = sum sqrt(v_i) dW1_i and the integrated variance Q = sum v_i dt on a uniform
    grid of `steps` steps to t (left points; antithetic pairs). xi0 is a number or a function of time."""
    xi = xi0 if callable(xi0) else (lambda u: float(xi0))
    grid = np.linspace(t / steps, t, steps)
    low = _chol(joint_cov(grid, hurst))
    rng = np.random.default_rng(seed)
    half = rng.standard_normal((n_paths // 2, 2 * steps))
    g = np.vstack([half, -half]) @ low.T
    y, w = g[:, :steps], g[:, steps:]
    left = np.concatenate([[0.0], grid[:-1]])
    xis = np.array([xi(u) for u in left])
    v = np.empty((len(g), steps))
    v[:, 0] = xis[0]
    v[:, 1:] = xis[1:] * np.exp(eta * y[:, :-1] - 0.5 * eta ** 2 * left[1:] ** (2 * hurst))
    dw = np.diff(np.concatenate([np.zeros((len(g), 1)), w], axis=1), axis=1)
    return np.sum(np.sqrt(v) * dw, axis=1), np.sum(v, axis=1) * (t / steps)


def mixing_calls(i_sum: np.ndarray, q: np.ndarray, rho: float, strikes) -> np.ndarray:
    """Call prices on a forward of 1 by the mixing formula: given the volatility driver, ln S_T is normal
    with mean rho I - Q / 2 and variance (1 - rho^2) Q, so the call is a Black price averaged over paths."""
    s1 = np.exp(rho * i_sum - 0.5 * rho * rho * q)
    sd = np.sqrt((1 - rho * rho) * q)
    out = []
    for k in strikes:
        d1 = (np.log(s1 / k) + 0.5 * sd * sd) / sd
        out.append(float(np.mean(s1 * ncdf(d1) - k * ncdf(d1 - sd))))
    return np.array(out)


def rbergomi_smile(xi0, hurst: float, eta: float, rho: float, t: float, ks, steps: int = 100,
                   n_paths: int = 100_000, seed: int = 12) -> np.ndarray:
    """Implied volatilities at log-moneyness ks for expiry t."""
    i_sum, q = rbergomi_integrals(xi0, hurst, eta, t, steps, n_paths, seed)
    prices = mixing_calls(i_sum, q, rho, np.exp(ks))
    return np.array([implied_vol(p, 1.0, math.exp(k), t, 1.0, "C") for p, k in zip(prices, ks, strict=True)])


def atm_skew(smile_fn, t: float, h: float | None = None) -> float:
    """d sigma / dk at k = 0 by central difference; smile_fn(ks, t) returns implied volatilities."""
    h = 0.05 * math.sqrt(t) if h is None else h
    lo, hi = smile_fn(np.array([-h, h]), t)
    return float((hi - lo) / (2 * h))


def power_law_fit(ts, skews) -> tuple[float, float]:
    """Least-squares fit of |skew| = A T^alpha on log axes; returns (A, alpha)."""
    slope, icpt = np.polyfit(np.log(ts), np.log(np.abs(skews)), 1)
    return float(math.exp(icpt)), float(slope)


def rbergomi_vix(xi0: float, hurst: float, eta: float, t: float, n_paths: int = 100_000, seed: int = 13,
                 window: float = 30 / 365, n_u: int = 40) -> np.ndarray:
    """VIX at t (in volatility units) in rough Bergomi with a flat forward variance xi0:
    VIX_t^2 = (1 / window) int_t^{t + window} xi_t(u) du, with
    xi_t(u) = xi0 exp(eta Z_u - eta^2 (u^(2H) - (u - t)^(2H)) / 2), Z_u = sqrt(2H) int_0^t (u - s)^(H - 1/2) dW_s."""
    us = t + (np.arange(n_u) + 0.5) * window / n_u
    y, wts = np.polynomial.legendre.leggauss(400)
    y, wts = 0.5 * (y + 1.0), 0.5 * wts
    r, dr = t * y ** 4, 4 * t * y ** 3 * wts                         # r = t - s, crowded near r = 0
    k = (us[:, None] - t + r[None, :]) ** (hurst - 0.5)
    cov = 2 * hurst * (k * dr) @ k.T
    var = us ** (2 * hurst) - (us - t) ** (2 * hurst)
    rng = np.random.default_rng(seed)
    half = rng.standard_normal((n_paths // 2, n_u))
    z = np.vstack([half, -half]) @ _chol(cov).T
    xi_t = xi0 * np.exp(eta * z - 0.5 * eta ** 2 * var)
    return np.sqrt(xi_t.mean(axis=1))


# ---------------------------------------------------------------- roughness
def fbm(n: int, hurst: float, seed: int, dt: float = 1.0) -> np.ndarray:
    """Fractional Brownian motion at dt, 2dt, ..., n dt, exactly (Cholesky of its covariance)."""
    t = dt * np.arange(1, n + 1)
    c = 0.5 * (t[:, None] ** (2 * hurst) + t[None, :] ** (2 * hurst) - np.abs(t[:, None] - t[None, :]) ** (2 * hurst))
    return _chol(c) @ np.random.default_rng(seed).standard_normal(n)


def structure_function(x: np.ndarray, lags, q: float = 2.0) -> np.ndarray:
    """m(q, lag) = mean |x_{t + lag} - x_t|^q."""
    return np.array([np.mean(np.abs(x[lag:] - x[:-lag]) ** q) for lag in lags])


def roughness(x: np.ndarray, lags=range(1, 31), q: float = 2.0) -> float:
    """Estimate of H: the slope of log m(q, lag) on log lag, divided by q."""
    lags = np.asarray(list(lags), float)
    slope = np.polyfit(np.log(lags), np.log(structure_function(x, lags.astype(int), q)), 1)[0]
    return float(slope / q)
