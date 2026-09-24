"""The Heston model: characteristic function, Fourier pricing, calibration, simulation
(build of Book 5, Chapter 10).

    dS = (r - q) S dt + sqrt(v) S dW1,  dv = kappa (vbar - v) dt + eta sqrt(v) dW2,  d<W1, W2> = rho dt.

The characteristic function of x = ln(S_T / F_T) is written in the form that stays on the principal
branch of the complex logarithm for all u (Albrecher, Mayer, Schoutens, Tistaert, 'the little Heston
trap'). Calls are priced with a single Fourier integral in forward terms (Lewis):
    C = P(0,T) [ F - sqrt(F K)/pi * int_0^inf Re( e^{-i u k} phi(u - i/2) ) / (u^2 + 1/4) du ],  k = ln(K/F).
"""
import math
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "bs"))
from firm_bs import black, implied_vol  # noqa: E402,F401

U = np.linspace(1e-8, 200.0, 4001)             # integration grid for the Fourier integral


@dataclass(frozen=True)
class Heston:
    v0: float
    kappa: float
    vbar: float
    eta: float
    rho: float

    def cf(self, u, t: float):
        """E[exp(i u x_T)], x_T = ln(S_T / F_T), for real or complex u (numpy arrays accepted)."""
        u = np.asarray(u, complex)
        xi = self.kappa - self.rho * self.eta * 1j * u
        d = np.sqrt(xi * xi + self.eta ** 2 * (1j * u + u * u))
        g = (xi - d) / (xi + d)
        e = np.exp(-d * t)
        c = self.kappa * self.vbar / self.eta ** 2 * ((xi - d) * t - 2.0 * np.log((1 - g * e) / (1 - g)))
        dd = (xi - d) / self.eta ** 2 * (1 - e) / (1 - g * e)
        return np.exp(c + dd * self.v0)

    def feller(self) -> float:
        """2 kappa vbar - eta^2: non-negative when the variance cannot reach zero."""
        return 2 * self.kappa * self.vbar - self.eta ** 2


def call_prices(model: Heston, fwd: float, strikes, t: float, df: float = 1.0) -> np.ndarray:
    """European calls for many strikes of one expiry (one characteristic-function evaluation)."""
    ks = np.log(np.asarray(strikes, float) / fwd)
    phi = model.cf(U - 0.5j, t)
    integrand = np.real(np.exp(-1j * np.outer(ks, U)) * phi[None, :]) / (U * U + 0.25)
    integral = np.trapezoid(integrand, U, axis=1)
    return df * (fwd - np.sqrt(fwd * np.asarray(strikes, float)) / math.pi * integral)


def implied_vols(model: Heston, fwd: float, strikes, t: float) -> np.ndarray:
    out = []
    for k, c in zip(strikes, call_prices(model, fwd, strikes, t), strict=True):
        right = "C" if k >= fwd else "P"
        p = c if right == "C" else c - (fwd - k)            # put by parity (df = 1)
        out.append(implied_vol(p, fwd, k, t, 1.0, right))
    return np.array(out)


def _to_model(z) -> Heston:
    return Heston(math.exp(z[0]), math.exp(z[1]), math.exp(z[2]), math.exp(z[3]), math.tanh(z[4]))


def _from_model(m: Heston) -> np.ndarray:
    return np.array([math.log(m.v0), math.log(m.kappa), math.log(m.vbar), math.log(m.eta), math.atanh(m.rho)])


def calibrate(quotes: list[tuple[float, np.ndarray, np.ndarray]], fwd: float, start: Heston,
              max_iter: int = 60, lam: float = 1e-2) -> tuple[Heston, float]:
    """Levenberg-Marquardt on implied-volatility residuals; quotes are (t, strikes, vols). Parameters are
    transformed (logs, artanh) so that every step stays admissible. Returns the model and the RMSE."""
    def residuals(z):
        m = _to_model(z)
        return np.concatenate([implied_vols(m, fwd, ks, t) - vols for t, ks, vols in quotes])
    z = _from_model(start)
    r = residuals(z)
    cost = float(r @ r)
    for _ in range(max_iter):
        h = 1e-5
        jac = np.column_stack([(residuals(z + h * e) - r) / h for e in np.eye(5)])
        a, g = jac.T @ jac, jac.T @ r
        while True:
            step = np.linalg.solve(a + lam * np.diag(np.diag(a) + 1e-12), -g)
            z_new = z + step
            try:
                r_new = residuals(z_new)
                c_new = float(r_new @ r_new)
            except (ValueError, FloatingPointError, OverflowError):
                c_new = math.inf
            if c_new < cost:
                z, r, cost, lam = z_new, r_new, c_new, max(lam / 3, 1e-9)
                break
            lam *= 4
            if lam > 1e8:
                return _to_model(z), math.sqrt(cost / len(r))
        if float(np.max(np.abs(step))) < 1e-7:
            break
    return _to_model(z), math.sqrt(cost / len(r))


def simulate(model: Heston, s0: float, t: float, steps: int, n_paths: int, seed: int) -> np.ndarray:
    """Full-truncation Euler scheme (a reference; chapter 23 uses the quadratic-exponential scheme)."""
    rng = np.random.default_rng(seed)
    dt = t / steps
    x = np.zeros(n_paths)
    v = np.full(n_paths, model.v0)
    c = math.sqrt(1 - model.rho ** 2)
    for _ in range(steps):
        z1, z2 = rng.standard_normal(n_paths), rng.standard_normal(n_paths)
        vp = np.maximum(v, 0.0)
        x += -0.5 * vp * dt + np.sqrt(vp * dt) * z1
        v += model.kappa * (model.vbar - vp) * dt + model.eta * np.sqrt(vp * dt) * (model.rho * z1 + c * z2)
    return s0 * np.exp(x)


def black_limit_vol(model: Heston, t: float) -> float:
    """Implied volatility when eta -> 0: the root-mean of the deterministic variance path."""
    k = model.kappa
    w = model.vbar * t + (model.v0 - model.vbar) * (1 - math.exp(-k * t)) / k
    return math.sqrt(w / t)




def simulate_paths(model: Heston, s0: float, times, steps_per_year: int, n_paths: int, seed: int) -> np.ndarray:
    """Spot at the given dates (column 0 = s0), full-truncation Euler with antithetic pairs (added for Book 5,
    Chapter 16's path-dependent payoffs)."""
    times = np.asarray(times, float)
    rng = np.random.default_rng(seed)
    half = n_paths // 2
    x = np.zeros(2 * half)
    v = np.full(2 * half, model.v0)
    c = math.sqrt(1 - model.rho ** 2)
    out = [np.full(2 * half, s0)]
    now = 0.0
    for target in times:
        steps = max(1, round((target - now) * steps_per_year))
        dt = (target - now) / steps
        for _ in range(steps):
            z1 = rng.standard_normal(half)
            z2 = rng.standard_normal(half)
            z1, z2 = np.concatenate([z1, -z1]), np.concatenate([z2, -z2])
            vp = np.maximum(v, 0.0)
            x += -0.5 * vp * dt + np.sqrt(vp * dt) * z1
            v += model.kappa * (model.vbar - vp) * dt + model.eta * np.sqrt(vp * dt) * (model.rho * z1 + c * z2)
        out.append(s0 * np.exp(x))
        now = target
    return np.column_stack(out)
