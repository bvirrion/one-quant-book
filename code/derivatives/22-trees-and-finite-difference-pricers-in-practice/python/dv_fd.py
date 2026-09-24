"""Trees and finite-difference pricers in practice (Book 5, Chapter 22): the American put on trees and grids,
accuracy against work, Rannacher start-up and payoff smoothing, a discrete dividend by the jump condition, and
barrier alignment. S = K = 100, one year, r = 5%, q = 0, volatility 20% unless stated."""
import functools
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for comp in ("bs", "binomial", "barrier", "fdpricer"):
    sys.path.insert(0, str(ROOT / f"code/firm/{comp}"))
from firm_barrier import barrier  # noqa: E402
from firm_binomial import price as tree_price  # noqa: E402
from firm_bs import bs  # noqa: E402
from firm_fdpricer import american_put, solve, stretched_grid, trinomial, uniform_grid, value_at  # noqa: E402

S, K, T, R, Q, VOL = 100.0, 100.0, 1.0, 0.05, 0.0, 0.20
TOL = 0.001


def crr(n: int) -> float:
    return tree_price(S, K, T, R, VOL, n, "P", True, Q, "crr")


@functools.cache
def fd(m: int, rannacher: int = 2, smoothing: bool = True) -> float:
    return american_put(S, K, T, R, Q, VOL, m, m, rannacher=rannacher, smoothing=smoothing)


@functools.cache
def reference() -> float:
    """Richardson extrapolation of the grid at 800 and 1600 nodes (and steps), second order."""
    a, b = fd(800), fd(1600)
    return b + (b - a) / 3


def hook() -> dict:
    return {"n200": crr(200), "n201": crr(201), "ref": reference()}


def oscillation(ns=range(100, 401, 1)) -> list[tuple[int, float]]:
    return [(n, crr(n)) for n in ns]


def first_within(errors: dict[int, float], tol: float = TOL, stay: int = 2) -> int:
    """Smallest size from which the error stays within tol for `stay` consecutive sizes of the scan."""
    keys = sorted(errors)
    for i, k in enumerate(keys):
        window = keys[i:i + stay]
        if len(window) == stay and all(abs(errors[j]) <= tol for j in window):
            return k
    return -1


@functools.cache
def accuracy_study() -> dict:
    ref = reference()
    crr_err = {n: crr(n) - ref for n in list(range(100, 3001, 50)) + [n + 1 for n in range(100, 3001, 50)]}
    tri_err = {n: trinomial(S, K, T, R, Q, VOL, n) - ref for n in (100, 200, 400, 800, 1600, 3200)}
    fd_sizes = (25, 50, 75, 100, 150, 200, 300, 400)
    fd_err = {m: fd(m) - ref for m in fd_sizes}
    raw_err = {m: fd(m, 0, False) - ref for m in fd_sizes}
    # the tree must hold for n and n + 1 (its odd-even oscillation)
    n_crr = next(n for n in range(100, 3001, 50) if abs(crr_err[n]) <= TOL and abs(crr_err[n + 1]) <= TOL)
    m_fd = next(m for m in fd_sizes if abs(fd_err[m]) <= TOL)
    work_crr = n_crr * (n_crr + 1) / 2
    work_fd = m_fd * (m_fd + 1) + 2 * m_fd                 # nodes x steps, plus the Rannacher half steps
    return {"ref": ref, "crr_err": crr_err, "tri_err": tri_err, "fd_err": fd_err, "raw_err": raw_err,
            "n_crr": n_crr, "m_fd": m_fd, "work_crr": work_crr, "work_fd": work_fd, "speedup": work_crr / work_fd}


# ---------------------------------------------------------------- Rannacher and smoothing near expiry
def gamma_profile(t: float = 0.02, m: int = 200, n_t: int = 10) -> dict:
    """Gamma of a European put with little time left, from Crank-Nicolson with and without Rannacher start-up,
    against Black-Scholes."""
    x = uniform_grid(S, VOL, t, m, width=8.0)
    out = {}
    for name, ran in (("cn", 0), ("rannacher", 2)):
        v = solve(lambda s: np.maximum(K - s, 0.0), x, t, R, Q, VOL, n_t, rannacher=ran,
                  lower=lambda tau, s: K * math.exp(-R * tau) - s, upper=lambda tau, s: 0.0)
        s = np.exp(x)
        g = np.gradient(np.gradient(v, s), s)
        out[name] = (s, g)
    d1 = lambda s: (np.log(s / K) + (R + 0.5 * VOL * VOL) * t) / (VOL * math.sqrt(t))  # noqa: E731
    s = out["cn"][0]
    out["exact"] = (s, np.exp(-0.5 * d1(s) ** 2) / (s * VOL * math.sqrt(2 * math.pi * t)))
    return out


# ---------------------------------------------------------------- a discrete dividend
def dividend_example(d: float = 3.0, td: float = 0.5) -> dict:
    """European and American puts with a cash dividend of d at td: the grid with the jump condition, against the
    escrowed-dividend approximation (Black-Scholes on the spot less the dividend's present value)."""
    x = stretched_grid(S, K, VOL, T, 400)
    euro = solve(lambda s: np.maximum(K - s, 0.0), x, T, R, Q, VOL, 400, dividends=[(td, d)], smoothing=True,
                 lower=lambda tau, s: K * math.exp(-R * tau) - s, upper=lambda tau, s: 0.0)
    amer = american_put(S, K, T, R, Q, VOL, 400, 400, dividends=[(td, d)])
    esc = bs(S - d * math.exp(-R * td), K, T, R, Q, VOL, "P")
    no_div_am = fd(400)
    return {"euro": value_at(x, euro, S)[0], "escrowed": esc, "american": amer, "american_no_div": no_div_am}


# ---------------------------------------------------------------- barrier alignment
def barrier_alignment(h: float = 90.0, sizes=(40, 60, 80, 100, 120, 160, 200, 300)) -> dict:
    """Down-and-out call (strike 100, barrier 90, one year): grids with the barrier exactly on a node (the grid
    starts at ln 90) against uniform grids on which the barrier falls between nodes (value set to zero below it)."""
    exact = barrier(S, K, h, T, R, Q, VOL, "down-out", "C")
    aligned, misaligned = {}, {}
    for m in sizes:
        xa = stretched_grid(S, K, VOL, T, m, lower=math.log(h))
        va = solve(lambda s: np.maximum(s - K, 0.0), xa, T, R, Q, VOL, m, smoothing=True,
                   lower=lambda tau, s: 0.0, upper=lambda tau, s: s - K * math.exp(-R * tau))
        aligned[m] = value_at(xa, va, S)[0] - exact
        xu = uniform_grid(S, VOL, T, m, width=5.0)
        xu = xu[xu >= math.log(h) - (xu[1] - xu[0]) * 0.999]    # the first node at or just below the barrier
        vu = solve(lambda s: np.maximum(s - K, 0.0), xu, T, R, Q, VOL, m, smoothing=True,
                   lower=lambda tau, s: 0.0, upper=lambda tau, s: s - K * math.exp(-R * tau))
        misaligned[m] = value_at(xu, vu, S)[0] - exact
    return {"exact": exact, "aligned": aligned, "misaligned": misaligned}


def project_after_solve(m: int) -> float:
    """American put by Crank-Nicolson solve, then max with the exercise value (no Brennan-Schwartz)."""
    import firm_fdpricer as eng
    x = stretched_grid(S, K, VOL, T, m)
    saved = eng._brennan_schwartz
    eng._brennan_schwartz = lambda a, b, c, d, g: eng._thomas(a, b, c, d)
    try:
        v = solve(lambda s: np.maximum(K - s, 0.0), x, T, R, Q, VOL, m, american=True, smoothing=True,
                  lower=lambda tau, s: K - s, upper=lambda tau, s: 0.0)
    finally:
        eng._brennan_schwartz = saved
    return value_at(x, v, S)[0]


def exercise_boundary(taus=None, m: int = 400) -> list[tuple[float, float]]:
    """Early-exercise boundary of the American put from the grid: for each time to expiry tau (no dividends, so a
    tau-year option's boundary today is the one-year option's boundary tau before expiry), the highest node below
    the strike where the value equals the exercise value, refined linearly to where V - g crosses 1e-6."""
    taus = np.linspace(0.02, 1.0, 25) if taus is None else taus
    out = []
    for tau in taus:
        x = stretched_grid(S, K, VOL, tau, m, width=6.0)
        v = solve(lambda s: np.maximum(K - s, 0.0), x, tau, R, Q, VOL, m, american=True, smoothing=True,
                  lower=lambda t, s: K - s, upper=lambda t, s: 0.0)
        s = np.exp(x)
        gap = v - np.maximum(K - s, 0.0)
        ex = np.where((gap < 1e-6) & (s < K))[0]
        i = int(ex.max())
        s_star = s[i] + (s[i + 1] - s[i]) * (1e-6 - gap[i]) / (gap[i + 1] - gap[i])
        out.append((float(tau), float(s_star)))
    return out


def tree_boundary() -> list[tuple[float, float]]:
    sys.path.insert(0, str(ROOT / "code/firm/american"))
    from firm_american import put_boundary
    return put_boundary(K, T, R, Q, VOL, 2000)
