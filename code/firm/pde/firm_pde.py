"""firm.pde -- finite-difference solvers of the miniature firm (One Quant Book 4, chapter 27).

One dimension: the backward equation u_tau = a(x) u_xx + b(x) u_x - c(x) u in time to maturity tau, on a uniform or
sinh-stretched grid, advanced by the theta scheme (explicit 0, Crank-Nicolson 1/2, implicit 1) with a Thomas solve per
step, Dirichlet or zero-gamma boundaries, optional upwinding of the first derivative, Rannacher start-up (implicit
half steps) and Richardson extrapolation. Two dimensions: the Douglas alternating-direction implicit scheme with an
explicit mixed derivative. The one-dimensional kernel (uniform grid, constant coefficients) is also in C++20
(cpp/firm_pde.hpp) and Rust (rust/src/lib.rs).

API (stable):
    uniform_grid(lo, hi, n) / sinh_grid(lo, hi, n, centre, alpha)       -> nodes x_0 < ... < x_n
    operator(x, a, b, c, upwind=False)                                  -> (lower, diag, upper) of L on interior nodes
    solve_1d(x, payoff, a, b, c, tau, n_steps, theta=0.5, rannacher=0,
             left=("dirichlet", g), right=("gamma0",), upwind=False)      -> values at tau on the grid
    thomas(lower, diag, upper, rhs)                                      -> tridiagonal solve
    richardson(coarse, fine, order)                                      -> extrapolated value
    amplification(theta, lam, xi)                                        -> von Neumann factor for u_t = u_xx
    douglas_adi_2d(...)                                                  -> two-factor solver with mixed derivative
"""
from __future__ import annotations

import math

import numpy as np


def uniform_grid(lo: float, hi: float, n: int) -> np.ndarray:
    return np.linspace(lo, hi, n + 1)


def sinh_grid(lo: float, hi: float, n: int, centre: float, alpha: float) -> np.ndarray:
    """Nodes concentrated around `centre`; alpha is the width of the fine region (large alpha: nearly uniform)."""
    a0, a1 = math.asinh((lo - centre) / alpha), math.asinh((hi - centre) / alpha)
    return centre + alpha * np.sinh(a0 + (a1 - a0) * np.linspace(0.0, 1.0, n + 1))


def thomas(lower, diag, upper, rhs) -> np.ndarray:
    """Tridiagonal solve: lower[i] multiplies x[i-1], upper[i] multiplies x[i+1] (lower[0], upper[-1] unused)."""
    n = len(diag)
    cp, dp = np.empty(n), np.empty(n)
    cp[0], dp[0] = upper[0] / diag[0], rhs[0] / diag[0]
    for i in range(1, n):
        m = diag[i] - lower[i] * cp[i - 1]
        cp[i] = upper[i] / m if i < n - 1 else 0.0
        dp[i] = (rhs[i] - lower[i] * dp[i - 1]) / m
    out = np.empty(n)
    out[-1] = dp[-1]
    for i in range(n - 2, -1, -1):
        out[i] = dp[i] - cp[i] * out[i + 1]
    return out


def operator(x: np.ndarray, a, b, c, upwind: bool = False) -> tuple:
    """Coefficients of L u = a u_xx + b u_x - c u at interior nodes 1..n-1 on a (possibly non-uniform) grid:
    (L u)_i = lo_i u_{i-1} + di_i u_i + up_i u_{i+1}. Central first differences are second order; `upwind` uses the
    one-sided difference in the direction of the drift where the central one would break the M-matrix sign pattern."""
    xi = x[1:-1]
    hm, hp = xi - x[:-2], x[2:] - xi
    av = np.broadcast_to(np.asarray(a(xi) if callable(a) else a, dtype=float), xi.shape)
    bv = np.broadcast_to(np.asarray(b(xi) if callable(b) else b, dtype=float), xi.shape)
    cv = np.broadcast_to(np.asarray(c(xi) if callable(c) else c, dtype=float), xi.shape)
    lo = 2 * av / (hm * (hm + hp))
    up = 2 * av / (hp * (hm + hp))
    di = -lo - up - cv
    central_lo, central_up = -bv * hp / (hm * (hm + hp)), bv * hm / (hp * (hm + hp))
    central_di = bv * (hp - hm) / (hm * hp)
    if upwind:
        bad = (lo + central_lo < 0) | (up + central_up < 0)
        fwd = bad & (bv > 0)
        bwd = bad & (bv < 0)
        central_lo = np.where(fwd, 0.0, np.where(bwd, -bv / hm, central_lo))
        central_up = np.where(fwd, bv / hp, np.where(bwd, 0.0, central_up))
        central_di = np.where(fwd, -bv / hp, np.where(bwd, bv / hm, central_di))
    return lo + central_lo, di + central_di, up + central_up


def _theta_step(u, L, dt, theta, x, t_new, left, right) -> np.ndarray:
    """One step of (I - theta dt L) u^{n+1} = (I + (1 - theta) dt L) u^n on the interior, boundary values fixed."""
    lo, di, up = L
    ui = u[1:-1]
    rhs = ui + (1 - theta) * dt * (lo * u[:-2] + di * ui + up * u[2:])
    new = np.empty_like(u)
    for idx, cond in ((0, left), (-1, right)):
        if cond[0] == "dirichlet":
            new[idx] = cond[1](x[idx], t_new)
    A_lo, A_di, A_up = -theta * dt * lo, 1 - theta * dt * di, -theta * dt * up
    if left[0] == "dirichlet":
        rhs[0] -= A_lo[0] * new[0]
    else:                                       # zero gamma: u_0 = u_1 - (u_2 - u_1) h0 / h1 (linear extrapolation)
        h0, h1 = x[1] - x[0], x[2] - x[1]
        A_di[0] += A_lo[0] * (1 + h0 / h1)
        A_up[0] += A_lo[0] * (-h0 / h1)
    if right[0] == "dirichlet":
        rhs[-1] -= A_up[-1] * new[-1]
    else:
        h0, h1 = x[-1] - x[-2], x[-2] - x[-3]
        A_di[-1] += A_up[-1] * (1 + h0 / h1)
        A_lo[-1] += A_up[-1] * (-h0 / h1)
    if theta == 0.0 and left[0] == "dirichlet" and right[0] == "dirichlet":
        new[1:-1] = rhs
    else:
        new[1:-1] = thomas(A_lo, A_di, A_up, rhs)
    if left[0] != "dirichlet":
        h0, h1 = x[1] - x[0], x[2] - x[1]
        new[0] = new[1] - (new[2] - new[1]) * h0 / h1
    if right[0] != "dirichlet":
        h0, h1 = x[-1] - x[-2], x[-2] - x[-3]
        new[-1] = new[-2] + (new[-2] - new[-3]) * h0 / h1
    return new


def solve_1d(x, payoff, a, b, c, tau: float, n_steps: int, theta: float = 0.5, rannacher: int = 0,
             left=("gamma0",), right=("gamma0",), upwind: bool = False, history: bool = False):
    """March u from the payoff at tau = 0 to `tau` in n_steps equal steps. With rannacher = k > 0 the first k/2 steps
    are replaced by k implicit Euler half steps. Returns the values on the grid (and every step with history)."""
    x = np.asarray(x, dtype=float)
    u = np.asarray(payoff(x), dtype=float).copy()
    L = operator(x, a, b, c, upwind)
    dt = tau / n_steps
    t = 0.0
    path = [u.copy()]
    for _ in range(rannacher):
        t += dt / 2
        u = _theta_step(u, L, dt / 2, 1.0, x, t, left, right)
        path.append(u.copy())
    for _ in range(n_steps - rannacher // 2):
        t += dt
        u = _theta_step(u, L, dt, theta, x, t, left, right)
        path.append(u.copy())
    return (u, path) if history else u


def richardson(coarse: float, fine: float, order: float) -> float:
    """Extrapolate two estimates with step h and h/2 whose error is C h^order."""
    return fine + (fine - coarse) / (2**order - 1)


def amplification(theta: float, lam: float, xi) -> np.ndarray:
    """Von Neumann factor of the theta scheme for u_t = u_xx with lam = dt / dx^2 at frequency xi dx:
    g = (1 - 4 (1 - theta) lam s) / (1 + 4 theta lam s), s = sin^2(xi / 2)."""
    s = np.sin(np.asarray(xi, dtype=float) / 2) ** 2
    return (1 - 4 * (1 - theta) * lam * s) / (1 + 4 * theta * lam * s)


def interp(x: np.ndarray, u: np.ndarray, x0: float) -> float:
    """Value at x0 by cubic Lagrange interpolation on the four nearest nodes."""
    i = int(np.clip(np.searchsorted(x, x0) - 2, 0, len(x) - 4))
    xs, us = x[i:i + 4], u[i:i + 4]
    out = 0.0
    for j in range(4):
        w = 1.0
        for k in range(4):
            if k != j:
                w *= (x0 - xs[k]) / (xs[j] - xs[k])
        out += w * us[j]
    return out


# ---- two dimensions: Douglas ADI ---------------------------------------------------------------------------

def douglas_adi_2d(x, y, payoff, ax, bx, ay, by, axy, c, tau: float, n_steps: int, theta: float = 0.5):
    """u_tau = ax u_xx + bx u_x + ay u_yy + by u_y + axy u_xy - c u with constant coefficients on a uniform grid,
    zero-gamma (linear) boundaries in each direction. Douglas scheme: Y0 = u + dt F(u); Yj = Y_{j-1} + theta dt
    (A_j Yj - A_j u), j = 1, 2, with A_0 the mixed derivative (explicit) and A_1, A_2 the x and y parts
    (the reaction term split evenly)."""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    hx, hy = x[1] - x[0], y[1] - y[0]
    u = np.asarray(payoff(x[:, None], y[None, :]), dtype=float).copy()
    dt = tau / n_steps

    def lin(v):                                 # linear extrapolation to the four edges
        v[0, :], v[-1, :] = 2 * v[1, :] - v[2, :], 2 * v[-2, :] - v[-3, :]
        v[:, 0], v[:, -1] = 2 * v[:, 1] - v[:, 2], 2 * v[:, -2] - v[:, -3]
        return v

    def A1(v):
        out = np.zeros_like(v)
        out[1:-1, :] = (ax * (v[2:, :] - 2 * v[1:-1, :] + v[:-2, :]) / hx**2 + bx * (v[2:, :] - v[:-2, :]) / (2 * hx)
                        - 0.5 * c * v[1:-1, :])
        return out

    def A2(v):
        out = np.zeros_like(v)
        out[:, 1:-1] = (ay * (v[:, 2:] - 2 * v[:, 1:-1] + v[:, :-2]) / hy**2 + by * (v[:, 2:] - v[:, :-2]) / (2 * hy)
                        - 0.5 * c * v[:, 1:-1])
        return out

    def A0(v):
        out = np.zeros_like(v)
        out[1:-1, 1:-1] = axy * (v[2:, 2:] - v[2:, :-2] - v[:-2, 2:] + v[:-2, :-2]) / (4 * hx * hy)
        return out

    def implicit(rhs, along_x: bool):
        coef_a, coef_b, h = (ax, bx, hx) if along_x else (ay, by, hy)
        lo = -theta * dt * (coef_a / h**2 - coef_b / (2 * h))
        up = -theta * dt * (coef_a / h**2 + coef_b / (2 * h))
        di = 1 + theta * dt * (2 * coef_a / h**2 + 0.5 * c)
        r = rhs if along_x else rhs.T
        out = r.copy()
        m = r.shape[0] - 2
        L, D, U = np.full(m, lo), np.full(m, di), np.full(m, up)
        D[0] += 2 * lo
        U[0] -= lo
        D[-1] += 2 * up
        L[-1] -= up
        for j in range(1, r.shape[1] - 1):
            out[1:-1, j] = thomas(L, D, U, r[1:-1, j])
        return out if along_x else out.T

    for _ in range(n_steps):
        a1, a2 = A1(u), A2(u)
        Y0 = u + dt * (A0(u) + a1 + a2)
        Y1 = lin(implicit(Y0 - theta * dt * a1, True))
        Y2 = lin(implicit(Y1 - theta * dt * a2, False))
        u = Y2
    return u
