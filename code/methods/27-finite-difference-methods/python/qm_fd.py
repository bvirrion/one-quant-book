"""Book 4, chapter 27: finite-difference methods (teaching module).

The Black-Scholes backward equation in log-price, u_tau = (sigma^2/2) u_xx + (r - sigma^2/2) u_x - r u, solved with
explicit, implicit and Crank-Nicolson steps; the explicit stability limit; the Crank-Nicolson sawtooth in gamma and
its removal by Rannacher start-up; convergence orders; stretched grids; Richardson extrapolation; upwinding; and a
two-asset exchange option by Douglas ADI against Margrabe's formula.
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "pde"))
from firm_pde import (  # noqa: E402
    amplification,
    douglas_adi_2d,
    interp,
    richardson,
    sinh_grid,
    solve_1d,
    uniform_grid,
)

K, R, SIGMA, T = 100.0, 0.03, 0.2, 0.25
A, B, C = 0.5 * SIGMA**2, R - 0.5 * SIGMA**2, R
LO, HI = math.log(K) - 5 * SIGMA * math.sqrt(T), math.log(K) + 5 * SIGMA * math.sqrt(T)


def _n(z):
    return 0.5 * math.erfc(-z / math.sqrt(2))


def bs(S: float, kind: str = "call") -> float:
    d1 = (math.log(S / K) + (R + 0.5 * SIGMA**2) * T) / (SIGMA * math.sqrt(T))
    d2 = d1 - SIGMA * math.sqrt(T)
    if kind == "call":
        return S * _n(d1) - K * math.exp(-R * T) * _n(d2)
    return math.exp(-R * T) * _n(d2)                       # digital: pays 1 if S_T > K


def bs_gamma(S):
    S = np.asarray(S, dtype=float)
    d1 = (np.log(S / K) + (R + 0.5 * SIGMA**2) * T) / (SIGMA * math.sqrt(T))
    return np.exp(-0.5 * d1**2) / math.sqrt(2 * math.pi) / (S * SIGMA * math.sqrt(T))


def call(x):
    return np.maximum(np.exp(x) - K, 0.0)


def digital(x):
    return np.where(np.exp(x) > K, 1.0, np.where(np.isclose(np.exp(x), K), 0.5, 0.0))


def gamma_on_grid(x, u):
    """Gamma in the price variable from the log-grid: (u_xx - u_x) / S^2 by central differences."""
    h = x[1] - x[0]
    ux = (u[2:] - u[:-2]) / (2 * h)
    uxx = (u[2:] - 2 * u[1:-1] + u[:-2]) / h**2
    S = np.exp(x[1:-1])
    return S, (uxx - ux) / S**2


def lam(n_space: int, n_time: int) -> float:
    """a dt / dx^2, the explicit scheme's stability number (stable iff at most 1/2)."""
    return A * (T / n_time) / ((HI - LO) / n_space) ** 2


def explicit_blowup(n_space: int = 200, lams=(0.49, 0.51)) -> dict:
    """Largest |u| after marching the explicit scheme at a stability number just below and just above 1/2."""
    x = uniform_grid(LO, HI, n_space)
    dx2 = (x[1] - x[0]) ** 2
    out = {}
    for lm in lams:
        m = math.ceil(A * T / (lm * dx2))
        m_lam = A * (T / m) / dx2
        u = solve_1d(x, call, A, B, C, T, m, theta=0.0)
        out[lm] = {"steps": m, "lam": m_lam, "max": float(np.max(np.abs(u))), "price": interp(x, u, math.log(K))}
    return out


def sawtooth(n_space: int = 400, n_time: int = 25, rannacher=(0, 2, 4, 8)) -> dict:
    """Gamma near the strike from Crank-Nicolson with k implicit half steps at the start."""
    x = uniform_grid(LO, HI, n_space)
    res = {}
    for k in rannacher:
        u = solve_1d(x, call, A, B, C, T, n_time, theta=0.5, rannacher=k)
        S, g = gamma_on_grid(x, u)
        m = (S > 90) & (S < 110)
        res[k] = {"S": S[m], "gamma": g[m], "err": float(np.max(np.abs(g[m] - bs_gamma(S[m])))),
                  "price_err": abs(interp(x, u, math.log(K)) - bs(K))}
    return res


def convergence(levels=(200, 400, 800, 1600), ratio: int = 16) -> dict:
    """Price and gamma errors when space and time are refined together (n_time = n_space / ratio)."""
    rows = {}
    schemes = {"implicit": (1.0, 0), "cn": (0.5, 0), "cn+2": (0.5, 2), "cn+4": (0.5, 4)}
    for name, (th, k) in schemes.items():
        rows[name] = []
        for n in levels:
            x = uniform_grid(LO, HI, n)
            u = solve_1d(x, call, A, B, C, T, n // ratio, theta=th, rannacher=k)
            S, g = gamma_on_grid(x, u)
            m = (S > 90) & (S < 110)
            ud = solve_1d(x, digital, A, B, C, T, n // ratio, theta=th, rannacher=k)
            rows[name].append((n, abs(interp(x, u, math.log(K)) - bs(K)), float(np.max(np.abs(g[m] - bs_gamma(S[m])))),
                               abs(interp(x, ud, math.log(K)) - bs(K, "digital"))))
    return rows


def stretched(ns=(50, 100, 200, 400), alpha: float = 0.05) -> list[tuple]:
    """Call price error at the strike on a uniform and a sinh grid concentrated at the strike (same node count),
    Crank-Nicolson with four Rannacher half steps and n_time = n_space / 4."""
    rows = []
    for n in ns:
        out = []
        for x in (uniform_grid(LO, HI, n), sinh_grid(LO, HI, n, math.log(K), alpha)):
            u = solve_1d(x, call, A, B, C, T, max(n // 4, 4), theta=0.5, rannacher=4)
            out.append(abs(interp(x, u, math.log(K)) - bs(K)))
        rows.append((n, out[0], out[1]))
    return rows


def richardson_demo(n: int = 200) -> dict:
    x1, x2 = uniform_grid(LO, HI, n), uniform_grid(LO, HI, 2 * n)
    v1 = interp(x1, solve_1d(x1, call, A, B, C, T, n // 8, theta=0.5, rannacher=4), math.log(K))
    v2 = interp(x2, solve_1d(x2, call, A, B, C, T, n // 4, theta=0.5, rannacher=4), math.log(K))
    ex = bs(K)
    return {"coarse": abs(v1 - ex), "fine": abs(v2 - ex), "extrapolated": abs(richardson(v1, v2, 2) - ex)}


def upwind_demo(sigma: float = 0.02, r: float = 0.05, n: int = 100) -> dict:
    """A low-volatility, high-rate digital on a coarse grid: central first differences break the M-matrix sign
    pattern (b dx / (2a) > 1) and the solution overshoots (worth more than the discounted payout, and not monotone
    in the price); upwinding restores both."""
    a, b = 0.5 * sigma**2, r - 0.5 * sigma**2
    x = uniform_grid(math.log(K) - 1.0, math.log(K) + 1.0, n)
    out = {"peclet": b * (x[1] - x[0]) / (2 * a), "bound": math.exp(-r)}
    for up in (False, True):
        u = solve_1d(x, lambda z: np.where(np.exp(z) > K, 1.0, 0.0), a, b, r, 1.0, 20, theta=1.0, upwind=up)
        out["upwind" if up else "central"] = {"max": float(u.max()), "tv": float(np.abs(np.diff(u)).sum())}
    return out


def digital_placement(levels=(200, 400, 800, 1600), ratio: int = 16) -> list[tuple]:
    """Digital price error with the strike on a node (payoff 1/2 there) and midway between two nodes (the same as
    averaging the payoff over each node's cell), Crank-Nicolson with four Rannacher half steps."""
    rows = []
    for n in levels:
        x = uniform_grid(LO, HI, n)
        on = solve_1d(x, digital, A, B, C, T, n // ratio, theta=0.5, rannacher=4)
        xs = x + 0.5 * (x[1] - x[0])
        mid = solve_1d(xs, digital, A, B, C, T, n // ratio, theta=0.5, rannacher=4)
        ex = bs(K, "digital")
        rows.append((n, abs(interp(x, on, math.log(K)) - ex), abs(interp(xs, mid, math.log(K)) - ex)))
    return rows


def boundary_compare(n: int = 400) -> float:
    """Price at the strike with zero-gamma ends against Dirichlet ends (0 below, S - K e^{-r tau} above)."""
    x = uniform_grid(LO, HI, n)
    g0 = solve_1d(x, call, A, B, C, T, n // 16, theta=0.5, rannacher=4)
    d = solve_1d(x, call, A, B, C, T, n // 16, theta=0.5, rannacher=4, left=("dirichlet", lambda z, t: 0.0),
                 right=("dirichlet", lambda z, t: math.exp(z) - K * math.exp(-R * t)))
    return abs(interp(x, g0, math.log(K)) - interp(x, d, math.log(K)))


def amplification_curves(lam_cn: float = 32.0) -> dict:
    xi = np.linspace(0.0, math.pi, 181)
    return {"xi": xi, "explicit_049": amplification(0.0, 0.49, xi), "explicit_051": amplification(0.0, 0.51, xi),
            "implicit": amplification(1.0, lam_cn, xi), "cn": amplification(0.5, lam_cn, xi)}


# --- two assets: exchange option -----------------------------------------------------------------------

S1, S2, SIG1, SIG2, RHO, TX = 100.0, 100.0, 0.3, 0.2, 0.5, 1.0


def margrabe() -> float:
    s = math.sqrt(SIG1**2 + SIG2**2 - 2 * RHO * SIG1 * SIG2)
    d1 = (math.log(S1 / S2) + 0.5 * s * s * TX) / (s * math.sqrt(TX))
    return S1 * _n(d1) - S2 * _n(d1 - s * math.sqrt(TX))


def adi_exchange(n: int = 80, steps: int = 40, width: float = 4.0) -> dict:
    """max(S1 - S2, 0) in log-prices (r cancels from the exchange option; use r = 0), Douglas scheme theta = 1/2."""
    x = np.linspace(math.log(S1) - width * SIG1, math.log(S1) + width * SIG1, n + 1)
    y = np.linspace(math.log(S2) - width * SIG2, math.log(S2) + width * SIG2, n + 1)
    u = douglas_adi_2d(x, y, lambda a, b: np.maximum(np.exp(a) - np.exp(b), 0.0), 0.5 * SIG1**2, -0.5 * SIG1**2,
                       0.5 * SIG2**2, -0.5 * SIG2**2, RHO * SIG1 * SIG2, 0.0, TX, steps, theta=0.5)
    i, j = n // 2, n // 2
    return {"value": float(u[i, j]), "exact": margrabe(), "err": abs(float(u[i, j]) - margrabe())}
