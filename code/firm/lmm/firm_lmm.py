"""The market model of forward rates (build of One Quant Book 6, chapter 8).

Annual tenor structure T_k = k (k = 0..N), forwards F_k for [T_k, T_{k+1}], lognormal:
  dF_k = mu_k dt + sigma_k(t) F_k dW_k,  d<W_i, W_j> = rho_ij dt,
  sigma_k(t) = phi_k g(T_k - t),  g(tau) = (a + b tau) exp(-c tau) + d  (Rebonato's abcd function),
  rho_ij = exp(-beta |T_i - T_j|).
phi_k scales each forward so that its caplet reprices at a target Black volatility. Simulation under
the spot measure (numeraire: the discretely rebalanced bank account) with a predictor-corrector drift;
Rebonato's frozen-weights formula for swaption volatilities; the HJM drift of a Gaussian forward
curve. numpy only; deterministic seeds.
"""
import math
from dataclasses import dataclass

import numpy as np


def abcd(tau, a: float, b: float, c: float, d: float):
    return (a + b * tau) * np.exp(-c * tau) + d


def hjm_drift_gaussian(t: float, T: float, sigma: float, kappa: float) -> float:
    """HJM drift alpha(t, T) = sigma_f(t, T) int_t^T sigma_f(t, u) du for sigma_f = sigma exp(-kappa (T - t))."""
    x = T - t
    return sigma * math.exp(-kappa * x) * sigma * (1 - math.exp(-kappa * x)) / kappa


@dataclass
class LMM:
    f0: np.ndarray                       # initial forwards F_k(0), k = 0..N-1 (annual periods)
    phi: np.ndarray                      # scalings
    abcd: tuple = (0.05, 0.10, 0.60, 0.15)
    beta: float = 0.10
    delta: float = 1.0

    @property
    def n(self) -> int:
        return len(self.f0)

    def vol(self, k: int, t):
        return self.phi[k] * abcd(np.maximum(k - t, 0.0), *self.abcd)

    def corr(self) -> np.ndarray:
        idx = np.arange(self.n)
        return np.exp(-self.beta * np.abs(idx[:, None] - idx[None, :]))

    def integrated_cov(self, i: int, j: int, t_end: float, steps: int = 400) -> float:
        """int_0^t_end sigma_i(t) sigma_j(t) dt (trapezoid)."""
        ts = np.linspace(0.0, t_end, steps + 1)
        return float(np.trapezoid(self.vol(i, ts) * self.vol(j, ts), ts))

    def discount_factors(self) -> np.ndarray:
        """P(0, T_k), k = 0..N, from the forwards (T_0 = 0)."""
        return np.concatenate([[1.0], np.cumprod(1.0 / (1.0 + self.delta * self.f0))])

    def swap(self, a: int, b: int) -> tuple[float, float, np.ndarray]:
        """Par rate of the swap [T_a, T_b], its annuity and the frozen weights w_i = delta P(0,T_{i+1}) / A."""
        p = self.discount_factors()
        ann = self.delta * p[a + 1:b + 1].sum()
        s = (p[a] - p[b]) / ann
        return s, ann, self.delta * p[a + 1:b + 1] / ann


def calibrate_to_caplets(f0: np.ndarray, black_vols: np.ndarray, abcd_params=(0.05, 0.10, 0.60, 0.15),
                         beta: float = 0.10) -> LMM:
    """phi_k such that phi_k^2 int_0^{T_k} g(T_k - t)^2 dt = sigma_k^2 T_k for k >= 1 (F_0 is already fixed)."""
    m = LMM(np.asarray(f0, float), np.ones(len(f0)), abcd_params, beta)
    phi = np.ones(len(f0))
    for k in range(1, len(f0)):
        phi[k] = black_vols[k] * math.sqrt(k / m.integrated_cov(k, k, float(k)))
    phi[0] = phi[1]
    return LMM(np.asarray(f0, float), phi, abcd_params, beta)


def rebonato_vol(m: LMM, a: int, b: int) -> float:
    """Black volatility of the swaption expiring at T_a on the swap [T_a, T_b], by Rebonato's formula."""
    s, _, w = m.swap(a, b)
    rho = m.corr()
    tot = 0.0
    for i in range(a, b):
        for j in range(a, b):
            tot += w[i - a] * w[j - a] * m.f0[i] * m.f0[j] * rho[i, j] * m.integrated_cov(i, j, float(a))
    return math.sqrt(tot / (s * s * a))


def spot_drift(fv: np.ndarray, sig: np.ndarray, rho: np.ndarray, nxt: int, delta: float) -> np.ndarray:
    """Drift of each ln F_k under the spot measure (Ito term excluded):
    sigma_k sum_{j=nxt}^{k} delta rho_kj sigma_j F_j / (1 + delta F_j)."""
    x = delta * sig * fv / (1 + delta * fv)                        # paths x n
    mu = np.zeros_like(fv)
    for k in range(nxt, fv.shape[1]):
        mu[:, k] = sig[k] * (x[:, nxt:k + 1] @ rho[k, nxt:k + 1])
    return mu


def simulate(m: LMM, horizon: int, paths: int, sub: int = 4, seed: int = 7):
    """Forwards on the reset grid under the spot measure: returns (F at each reset date 0..horizon,
    numeraire B_d at each reset date). F[t][p, k] is F_k at T_t on path p."""
    rng = np.random.default_rng(seed)
    n, dt, rho = m.n, 1.0 / sub, m.corr()
    chol = np.linalg.cholesky(rho)
    logf = np.tile(np.log(m.f0), (paths, 1))
    out, numer = [np.exp(logf).copy()], [np.ones(paths)]
    bd = np.ones(paths)
    for step in range(horizon * sub):
        t = step * dt
        nxt = int(math.floor(t + 1e-12)) + 1                      # first forward still alive after t
        z = rng.standard_normal((paths, n)) @ chol.T
        sig = np.array([m.vol(k, t) for k in range(n)])
        mu0 = spot_drift(np.exp(logf), sig, rho, nxt, m.delta)          # predictor
        pred = logf + (mu0 - 0.5 * sig**2) * dt + sig * math.sqrt(dt) * z
        mu1 = spot_drift(np.exp(pred), sig, rho, nxt, m.delta)          # corrector
        alive = np.arange(n) >= nxt
        logf = np.where(alive, logf + (0.5 * (mu0 + mu1) - 0.5 * sig**2) * dt + sig * math.sqrt(dt) * z, logf)
        if (step + 1) % sub == 0:
            reset = (step + 1) // sub
            bd = bd * (1 + m.delta * out[-1][:, reset - 1])        # roll the account over the period just ended
            out.append(np.exp(logf).copy())
            numer.append(bd.copy())
    return out, numer


def mc_caplet(m: LMM, k: int, strike: float, paths: int = 20000, seed: int = 7) -> tuple[float, float]:
    """Caplet on F_k (fixing T_k, paid T_{k+1}) under the spot measure; (price, standard error)."""
    fs, bd = simulate(m, k + 1, paths, seed=seed)
    pay = m.delta * np.maximum(fs[k][:, k] - strike, 0.0)
    disc = pay / bd[k + 1]
    return float(disc.mean()), float(disc.std(ddof=1) / math.sqrt(paths))


def mc_swaption(m: LMM, a: int, b: int, strike: float, paths: int = 20000, seed: int = 7) -> tuple[float, float]:
    """Payer swaption expiring at T_a on [T_a, T_b], spot measure; (price, standard error)."""
    fs, bd = simulate(m, a, paths, seed=seed)
    f = fs[a][:, a:b]
    p = np.cumprod(1.0 / (1.0 + m.delta * f), axis=1)             # P(T_a, T_{a+1..b})
    ann = m.delta * p.sum(axis=1)
    swap = 1.0 - p[:, -1] - strike * ann
    disc = np.maximum(swap, 0.0) / bd[a]
    return float(disc.mean()), float(disc.std(ddof=1) / math.sqrt(paths))


def black(f: float, k: float, t: float, vol: float, annuity: float = 1.0) -> float:
    s = vol * math.sqrt(t)
    d1 = math.log(f / k) / s + 0.5 * s
    n = lambda x: 0.5 * math.erfc(-x / math.sqrt(2))  # noqa: E731
    return annuity * (f * n(d1) - k * n(d1 - s))


def implied_black(price: float, f: float, k: float, t: float, annuity: float) -> float:
    lo, hi = 1e-4, 3.0
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if black(f, k, t, mid, annuity) < price else (lo, mid)
    return 0.5 * (lo + hi)
