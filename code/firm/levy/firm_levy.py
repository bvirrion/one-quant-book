"""firm.levy -- Levy processes: characteristic exponents, cumulants, simulation (One Quant Book 4, ch. 6).

A Levy process X has E[exp(i u X_t)] = exp(t psi(u)) with psi given by the Levy-Khintchine formula.
The exponents below are those of the models the series uses; cumulants follow from derivatives of
psi at zero; paths are simulated by compound Poisson sums or by subordinating a Brownian motion to
a random clock.

API (stable):
    psi_bm(u, mu, sigma)                          Brownian motion with drift
    psi_merton(u, mu, sigma, lam, mu_j, sigma_j)  plus Gaussian jumps at rate lam
    psi_kou(u, mu, sigma, lam, p, eta1, eta2)     plus double-exponential jumps
    psi_vg(u, theta, sigma, nu)                   variance gamma (Brownian motion on a gamma clock)
    psi_nig(u, alpha, beta, delta)                normal inverse Gaussian
    cumulants(psi, n_max=4, h=1e-3)               kappa_1..kappa_n of X_1 by complex-step differences
    merton_cumulants(mu, sigma, lam, mu_j, sigma_j) closed form
    exp_martingale_drift(psi_without_drift)       drift that makes exp(X_t) a martingale: -psi(-i)
    simulate_merton(T, n_steps, n_paths, seed, ...), simulate_vg(...), simulate_nig(...)
"""
from __future__ import annotations

import math

import numpy as np


def psi_bm(u, mu: float, sigma: float):
    u = np.asarray(u, dtype=complex)
    return 1j * mu * u - 0.5 * sigma**2 * u**2


def psi_merton(u, mu: float, sigma: float, lam: float, mu_j: float, sigma_j: float):
    u = np.asarray(u, dtype=complex)
    return psi_bm(u, mu, sigma) + lam * (np.exp(1j * u * mu_j - 0.5 * sigma_j**2 * u**2) - 1)


def psi_kou(u, mu: float, sigma: float, lam: float, p: float, eta1: float, eta2: float):
    u = np.asarray(u, dtype=complex)
    return psi_bm(u, mu, sigma) + lam * (p * eta1 / (eta1 - 1j * u) + (1 - p) * eta2 / (eta2 + 1j * u) - 1)


def psi_vg(u, theta: float, sigma: float, nu: float):
    u = np.asarray(u, dtype=complex)
    return -np.log(1 - 1j * u * theta * nu + 0.5 * sigma**2 * nu * u**2) / nu


def psi_nig(u, alpha: float, beta: float, delta: float):
    u = np.asarray(u, dtype=complex)
    return delta * (np.sqrt(alpha**2 - beta**2) - np.sqrt(alpha**2 - (beta + 1j * u) ** 2))


def cumulants(psi, n_max: int = 4, h: float = 1e-2) -> list[float]:
    """kappa_n = (-i)^n psi^(n)(0), from psi evaluated on the imaginary axis (the cumulant generating
    function K(s) = psi(-i s)) by central finite differences of K at s = 0."""
    K = lambda s: float(np.real(psi(-1j * s)))   # noqa: E731
    pts = {k: K(k * h) for k in range(-3, 4)}
    d1 = (pts[1] - pts[-1]) / (2 * h)
    d2 = (pts[1] - 2 * pts[0] + pts[-1]) / h**2
    d3 = (pts[2] - 2 * pts[1] + 2 * pts[-1] - pts[-2]) / (2 * h**3)
    d4 = (pts[2] - 4 * pts[1] + 6 * pts[0] - 4 * pts[-1] + pts[-2]) / h**4
    return [d1, d2, d3, d4][:n_max]


def merton_cumulants(mu: float, sigma: float, lam: float, mu_j: float, sigma_j: float) -> list[float]:
    """Cumulants of X_1 for Brownian motion with drift plus compound Poisson N(mu_j, sigma_j^2) jumps:
    kappa_n = (diffusion part) + lam E[Y^n]."""
    m2 = mu_j**2 + sigma_j**2
    m3 = mu_j**3 + 3 * mu_j * sigma_j**2
    m4 = mu_j**4 + 6 * mu_j**2 * sigma_j**2 + 3 * sigma_j**4
    return [mu + lam * mu_j, sigma**2 + lam * m2, lam * m3, lam * m4]


def exp_martingale_drift(psi_without_drift) -> float:
    """For X_t = b t + L_t with L a Levy process of exponent psi_L, exp(X_t) is a martingale iff
    b = -psi_L(-i) = -log E[exp(L_1)]."""
    return float(-np.real(psi_without_drift(-1j)))


def simulate_merton(T: float, n_steps: int, n_paths: int, seed: int, mu: float, sigma: float, lam: float,
                    mu_j: float, sigma_j: float) -> np.ndarray:
    """Paths (n_paths, n_steps + 1) of mu t + sigma W_t + sum of N_t Gaussian jumps, exact on the grid."""
    rng = np.random.default_rng(seed)
    dt = T / n_steps
    n_jumps = rng.poisson(lam * dt, (n_paths, n_steps))
    jumps = mu_j * n_jumps + sigma_j * np.sqrt(n_jumps) * rng.standard_normal((n_paths, n_steps))
    inc = mu * dt + sigma * math.sqrt(dt) * rng.standard_normal((n_paths, n_steps)) + jumps
    return np.hstack([np.zeros((n_paths, 1)), np.cumsum(inc, axis=1)])


def simulate_vg(T: float, n_steps: int, n_paths: int, seed: int, theta: float, sigma: float, nu: float) -> np.ndarray:
    """Variance gamma: theta G_t + sigma W_{G_t} with G a gamma subordinator of mean t, variance nu t."""
    rng = np.random.default_rng(seed)
    dt = T / n_steps
    g = rng.gamma(dt / nu, nu, (n_paths, n_steps))
    inc = theta * g + sigma * np.sqrt(g) * rng.standard_normal((n_paths, n_steps))
    return np.hstack([np.zeros((n_paths, 1)), np.cumsum(inc, axis=1)])


def simulate_nig(T: float, n_steps: int, n_paths: int, seed: int, alpha: float, beta: float,
                 delta: float) -> np.ndarray:
    """Normal inverse Gaussian: beta Z_t + W_{Z_t} with Z an inverse-Gaussian subordinator of mean
    delta t / gamma and shape (delta t)^2, gamma = sqrt(alpha^2 - beta^2)."""
    rng = np.random.default_rng(seed)
    dt = T / n_steps
    gam = math.sqrt(alpha**2 - beta**2)
    z = rng.wald(delta * dt / gam, (delta * dt) ** 2, (n_paths, n_steps))
    inc = beta * z + np.sqrt(z) * rng.standard_normal((n_paths, n_steps))
    return np.hstack([np.zeros((n_paths, 1)), np.cumsum(inc, axis=1)])
