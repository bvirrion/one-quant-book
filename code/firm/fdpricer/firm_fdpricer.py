"""One-dimensional finite-difference pricing engine (build of Book 5, Chapter 22), with a trinomial tree for
comparison. Twins in C++20 (cpp/firm_fdpricer.hpp) and Rust (rust/src/lib.rs) implement the uniform-grid
American put with the same algorithm and are tested against this module's numbers.

The Black-Scholes equation in x = ln S, tau = time to expiry:
    V_tau = (1/2) sigma^2 V_xx + (r - q - sigma^2 / 2) V_x - r V,
on a grid that may be non-uniform (sinh-stretched around the strike), theta-scheme in time (Crank-Nicolson
with Rannacher start-up: fully implicit half steps first), American exercise by the Brennan-Schwartz
algorithm, discrete dividends by the jump condition V(t-, S) = V(t+, S - D), barriers by boundary nodes.
"""
import math

import numpy as np


# ---------------------------------------------------------------- grids
def uniform_grid(s0: float, vol: float, t: float, m: int, width: float = 5.0) -> np.ndarray:
    """m + 1 log-spot nodes, width standard deviations either side of ln s0."""
    half = width * vol * math.sqrt(t)
    return np.linspace(math.log(s0) - half, math.log(s0) + half, m + 1)


def stretched_grid(s0: float, k: float, vol: float, t: float, m: int, width: float = 5.0,
                   concentration: float = 3.0, lower: float | None = None) -> np.ndarray:
    """Nodes denser near ln k: x = ln k + c sinh(xi), xi uniform, with ln k exactly a node (m even), covering
    width standard deviations around ln s0 (or starting at `lower`, a barrier, which is then exactly a node)."""
    half = width * vol * math.sqrt(t)
    lo = math.log(s0) - half if lower is None else lower
    hi = math.log(s0) + half
    c = half / concentration
    xk = math.log(k)
    a, b = math.asinh((lo - xk) / c), math.asinh((hi - xk) / c)
    if lower is None:
        xi = np.linspace(a, b, m + 1)
        j = int(round(-a / (b - a) * m))                       # shift so that xi = 0 (the strike) is a node
        xi = xi - xi[j]
        return xk + c * np.sinh(xi)
    return xk + c * np.sinh(np.linspace(a, b, m + 1))


# ---------------------------------------------------------------- the solver
def _operator(x: np.ndarray, r: float, q: float, vol: float):
    """Tridiagonal coefficients (lower, diagonal, upper) of L V at interior nodes on a non-uniform grid."""
    hm, hp = np.diff(x)[:-1], np.diff(x)[1:]
    nu = r - q - 0.5 * vol * vol
    d2 = vol * vol
    lo = d2 / (hm * (hm + hp)) - nu * hp / (hm * (hm + hp))
    di = -d2 / (hm * hp) + nu * (hp - hm) / (hm * hp) - r
    up = d2 / (hp * (hm + hp)) + nu * hm / (hp * (hm + hp))
    return lo, di, up


def _thomas(a, b, c, d):
    n = len(d)
    cp, dp = [0.0] * n, [0.0] * n
    cp[0], dp[0] = c[0] / b[0], d[0] / b[0]
    for i in range(1, n):
        m = b[i] - a[i] * cp[i - 1]
        cp[i] = c[i] / m
        dp[i] = (d[i] - a[i] * dp[i - 1]) / m
    out = [0.0] * n
    out[-1] = dp[-1]
    for i in range(n - 2, -1, -1):
        out[i] = dp[i] - cp[i] * out[i + 1]
    return out


def _brennan_schwartz(a, b, c, d, g):
    """Solve the tridiagonal system with the constraint V >= g for a put-like exercise region at low spots:
    eliminate from the top of the grid down, then back-substitute upwards projecting onto V >= g."""
    n = len(d)
    bp, dp = [0.0] * n, [0.0] * n
    bp[-1], dp[-1] = b[-1], d[-1]
    for i in range(n - 2, -1, -1):
        f = c[i] / bp[i + 1]
        bp[i] = b[i] - f * a[i + 1]
        dp[i] = d[i] - f * dp[i + 1]
    out = [0.0] * n
    out[0] = max(dp[0] / bp[0], g[0])
    for i in range(1, n):
        out[i] = max((dp[i] - a[i] * out[i - 1]) / bp[i], g[i])
    return out


def smoothed_payoff(payoff, x: np.ndarray, pieces: int = 16) -> np.ndarray:
    """Payoff smoothing: each node carries the average of the payoff over its cell (midpoints to its neighbours)."""
    mids = np.concatenate([[x[0]], 0.5 * (x[1:] + x[:-1]), [x[-1]]])
    out = np.empty_like(x)
    for i in range(len(x)):
        xs = np.linspace(mids[i], mids[i + 1], pieces)
        out[i] = float(np.mean(payoff(np.exp(xs)))) if mids[i + 1] > mids[i] else float(payoff(np.exp(x[i])))
    return out


def solve(payoff, x: np.ndarray, t: float, r: float, q: float, vol: float, n_t: int, american: bool = False,
          rannacher: int = 2, dividends=(), smoothing: bool = False, lower=None, upper=None) -> np.ndarray:
    """Values today on the grid x. payoff(S) at expiry; lower(tau, S) and upper(tau, S) are Dirichlet values at
    the ends (default: the payoff, discounted appropriately is the caller's choice); dividends is a sequence
    of (time, cash amount); rannacher = number of fully implicit half steps after expiry and each dividend."""
    s = np.exp(x)
    v = smoothed_payoff(payoff, x) if smoothing else payoff(s)
    g = payoff(s)
    lo, di, up = _operator(x, r, q, vol)
    dt = t / n_t
    div_steps = {round((t - td) / dt): dcash for td, dcash in dividends}      # in steps of tau
    tau, step, implicit_half = 0.0, 0, 2 * rannacher
    while step < n_t:
        if implicit_half > 0:
            h, theta = 0.5 * dt, 1.0
            implicit_half -= 1
        else:
            h, theta = dt, 0.5
        tau += h
        rhs = v[1:-1] + (1 - theta) * h * (lo * v[:-2] + di * v[1:-1] + up * v[2:])
        a = list(-theta * h * lo)
        b = list(1 - theta * h * di)
        c = list(-theta * h * up)
        vl = lower(tau, s[0]) if lower else float(v[0])
        vu = upper(tau, s[-1]) if upper else float(v[-1])
        rhs = list(rhs)
        rhs[0] -= a[0] * vl
        rhs[-1] -= c[-1] * vu
        a[0], c[-1] = 0.0, 0.0
        inner = _brennan_schwartz(a, b, c, rhs, list(g[1:-1])) if american else _thomas(a, b, c, rhs)
        v = np.concatenate([[vl], inner, [vu]])
        if american:
            v = np.maximum(v, g)
        if abs(tau - (step + 1) * dt) < 1e-12 * max(1.0, t):
            step += 1
            if step in div_steps:                               # crossing a dividend date backwards
                dcash = div_steps[step]
                v = np.interp(np.maximum(s - dcash, s[0]), s, v)
                if american:
                    v = np.maximum(v, g)
                implicit_half = 2 * rannacher
    return v


def value_at(x: np.ndarray, v: np.ndarray, s0: float) -> tuple[float, float, float]:
    """Value, delta and gamma at s0 by quadratic interpolation on the three nodes around it."""
    x0 = math.log(s0)
    i = int(np.clip(np.searchsorted(x, x0), 1, len(x) - 2))
    xs, vs = x[i - 1:i + 2], v[i - 1:i + 2]
    coef = np.polyfit(xs - x0, vs, 2)
    val = coef[2]
    dvdx, d2vdx2 = coef[1], 2 * coef[0]
    delta = dvdx / s0
    gamma = (d2vdx2 - dvdx) / (s0 * s0)
    return float(val), float(delta), float(gamma)


def american_put(s0: float, k: float, t: float, r: float, q: float, vol: float, m: int, n_t: int,
                 grid: str = "stretched", rannacher: int = 2, smoothing: bool = True, dividends=()) -> float:
    x = stretched_grid(s0, k, vol, t, m) if grid == "stretched" else uniform_grid(s0, vol, t, m)
    v = solve(lambda s: np.maximum(k - s, 0.0), x, t, r, q, vol, n_t, american=True, rannacher=rannacher,
              smoothing=smoothing, dividends=dividends, lower=lambda tau, s: k - s, upper=lambda tau, s: 0.0)
    return value_at(x, v, s0)[0]


# ---------------------------------------------------------------- the trinomial tree
def trinomial(s0: float, k: float, t: float, r: float, q: float, vol: float, n: int, right: str = "P",
              american: bool = True) -> float:
    """Trinomial tree in log-spot with spacing sigma sqrt(3 dt) (Boyle): up, middle and down moves with the
    probabilities that match the mean and variance of the log-return over each step."""
    dt = t / n
    dx = vol * math.sqrt(3 * dt)
    nu = r - q - 0.5 * vol * vol
    pu = 0.5 * ((vol * vol * dt + nu * nu * dt * dt) / (dx * dx) + nu * dt / dx)
    pd = 0.5 * ((vol * vol * dt + nu * nu * dt * dt) / (dx * dx) - nu * dt / dx)
    pm = 1 - pu - pd
    disc = math.exp(-r * dt)
    j = np.arange(-n, n + 1)
    s = s0 * np.exp(j * dx)
    sign = 1.0 if right == "C" else -1.0
    v = np.maximum(sign * (s - k), 0.0)
    for i in range(n - 1, -1, -1):
        v = disc * (pu * v[2:] + pm * v[1:-1] + pd * v[:-2])
        if american:
            si = s0 * np.exp(np.arange(-i, i + 1) * dx)
            v = np.maximum(v, sign * (si - k))
    return float(v[0])
