"""Monte Carlo engine (build of Book 5, Chapter 23): multi-asset lognormal paths, Heston by full-truncation
Euler and by Andersen's quadratic-exponential scheme, Longstaff-Schwartz with a pluggable regression basis,
the Andersen-Broadie dual upper bound by nested simulation, pathwise and likelihood-ratio Greeks, an
adjoint (reverse-mode) pass for bucketed vegas, Halton points and the Brownian bridge.
"""
import math

import numpy as np


# ---------------------------------------------------------------- paths
def gbm_paths(s0, vols, corr, times, r: float, q, n: int, seed: int) -> np.ndarray:
    """(n, len(times) + 1, m) exact lognormal paths, antithetic pairs; column 0 is today."""
    s0 = np.atleast_1d(np.asarray(s0, float))
    m = len(s0)
    vols = np.broadcast_to(np.asarray(vols, float), (m,))
    q = np.broadcast_to(np.asarray(q, float), (m,))
    low = np.linalg.cholesky(np.asarray(corr, float)) if m > 1 else np.ones((1, 1))
    dt = np.diff(np.concatenate([[0.0], np.asarray(times, float)]))
    rng = np.random.default_rng(seed)
    z = rng.standard_normal((n // 2, len(dt), m)) @ low.T
    z = np.concatenate([z, -z])
    inc = (r - q - 0.5 * vols * vols) * dt[None, :, None] + vols * np.sqrt(dt)[None, :, None] * z
    logs = np.log(s0) + np.cumsum(inc, axis=1)
    return np.concatenate([np.tile(s0, (len(z), 1, 1)), np.exp(logs)], axis=1)


def heston_terminal(v0, kappa, vbar, eta, rho, s0: float, t: float, steps: int, n: int, seed: int, r: float = 0.0,
                    scheme: str = "qe") -> np.ndarray:
    """Terminal spot under Heston: full-truncation Euler ('euler') or Andersen's quadratic-exponential scheme
    ('qe') for the variance with his central discretisation of the log-spot (gamma1 = gamma2 = 1/2)."""
    rng = np.random.default_rng(seed)
    dt = t / steps
    x = np.full(n, math.log(s0))
    v = np.full(n, float(v0))
    if scheme == "euler":
        c = math.sqrt(1 - rho * rho)
        for _ in range(steps):
            z1, z2 = rng.standard_normal(n), rng.standard_normal(n)
            vp = np.maximum(v, 0.0)
            x += (r - 0.5 * vp) * dt + np.sqrt(vp * dt) * z1
            v += kappa * (vbar - vp) * dt + eta * np.sqrt(vp * dt) * (rho * z1 + c * z2)
        return np.exp(x)
    e = math.exp(-kappa * dt)
    k0 = -rho * kappa * vbar / eta * dt
    k1 = 0.5 * dt * (kappa * rho / eta - 0.5) - rho / eta
    k2 = 0.5 * dt * (kappa * rho / eta - 0.5) + rho / eta
    k3 = k4 = 0.5 * dt * (1 - rho * rho)
    for _ in range(steps):
        m = vbar + (v - vbar) * e
        s2 = v * eta * eta * e / kappa * (1 - e) + vbar * eta * eta / (2 * kappa) * (1 - e) ** 2
        psi = s2 / (m * m)
        u = rng.uniform(size=n)
        zv = rng.standard_normal(n)
        v_new = np.empty(n)
        quad = psi <= 1.5
        b2 = np.where(quad, 2 / np.maximum(psi, 1e-12) - 1 + np.sqrt(2 / np.maximum(psi, 1e-12)) *
                      np.sqrt(np.maximum(2 / np.maximum(psi, 1e-12) - 1, 0.0)), 0.0)
        a = m / (1 + b2)
        v_new[quad] = (a * (np.sqrt(b2) + zv) ** 2)[quad]
        p = (psi - 1) / (psi + 1)
        beta = (1 - p) / m
        exp_part = np.where(u <= p, 0.0, np.log(np.maximum((1 - p) / np.maximum(1 - u, 1e-300), 1e-300)) / beta)
        v_new[~quad] = exp_part[~quad]
        z = rng.standard_normal(n)
        x = x + r * dt + k0 + k1 * v + k2 * v_new + np.sqrt(np.maximum(k3 * v + k4 * v_new, 0.0)) * z
        v = v_new
    return np.exp(x)


# ---------------------------------------------------------------- Longstaff-Schwartz and the dual bound
def max_call_basis(s: np.ndarray, k: float) -> np.ndarray:
    """Regression basis for a max-call: polynomials in the sorted assets and the intrinsic value."""
    srt = np.sort(s, axis=1)[:, ::-1] / k
    b1, b2 = srt[:, 0], srt[:, 1]
    return np.column_stack([np.ones(len(s)), b1, b2, b1 * b1, b2 * b2, b1 * b2, b1 ** 3,
                            np.maximum(b1 - 1, 0.0), srt.prod(axis=1)])


def small_basis(s: np.ndarray, k: float) -> np.ndarray:
    b1 = s.max(axis=1) / k
    return np.column_stack([np.ones(len(s)), b1, b1 * b1])


def lsm_fit(paths: np.ndarray, ex_idx, payoff, basis, k: float, disc: float) -> list:
    """Backward regression of realised continuation values on the basis, in-the-money paths only; returns one
    coefficient vector per exercise date (the last date has none)."""
    cash = payoff(paths[:, ex_idx[-1], :])
    coefs = [None] * len(ex_idx)
    for j in range(len(ex_idx) - 2, -1, -1):
        cash = cash * disc
        s = paths[:, ex_idx[j], :]
        h = payoff(s)
        itm = h > 0
        if itm.sum() > 20:
            x = basis(s[itm], k)
            beta = np.linalg.lstsq(x, cash[itm], rcond=None)[0]
            coefs[j] = beta
            cont = x @ beta
            ex = h[itm] > cont
            idx = np.where(itm)[0][ex]
            cash[idx] = h[itm][ex]
    return coefs


def exercise_now(s: np.ndarray, j: int, coefs, payoff, basis, k: float) -> np.ndarray:
    h = payoff(s)
    if coefs[j] is None:
        return h > 0
    return (h > 0) & (h > basis(s, k) @ coefs[j])


def lsm_price(paths: np.ndarray, ex_idx, coefs, payoff, basis, k: float, disc: float) -> tuple[float, float]:
    """Lower bound: follow the fitted policy on independent paths. Returns (price, standard error)."""
    n = len(paths)
    value = np.zeros(n)
    alive = np.ones(n, bool)
    for j, i in enumerate(ex_idx):
        s = paths[:, i, :]
        ex = alive & (exercise_now(s, j, coefs, payoff, basis, k) if j < len(ex_idx) - 1 else payoff(s) > 0)
        value[ex] = payoff(s[ex]) * disc ** (j + 1)
        alive &= ~ex
    return float(value.mean()), float(value.std() / math.sqrt(n))


def dual_upper(outer: np.ndarray, ex_idx, coefs, payoff, basis, k: float, disc: float, step_sim, n_inner: int,
               seed: int) -> tuple[float, float]:
    """Andersen-Broadie upper bound. For every outer path and exercise date the policy's continuation value
    Q_j is estimated by n_inner inner paths that follow the policy from date j + 1; with L_j = h_j where the
    policy exercises and Q_j where it continues, the martingale increments are L_j - Q_(j-1), and the bound
    is E[max_j (h_j - M_j)] (all discounted to today). step_sim(s, n_steps, rng) simulates n_steps periods."""
    rng = np.random.default_rng(seed)
    n, n_ex = len(outer), len(ex_idx)
    q = np.zeros((n, n_ex + 1))                     # q[:, j] = continuation value at date j (index 0 = today)
    for j in range(n_ex):                           # j = 0 is today, j = 1..n_ex the exercise dates
        start = outer[:, 0 if j == 0 else ex_idx[j - 1], :]
        s = np.repeat(start, n_inner, axis=0)
        alive = np.ones(len(s), bool)
        val = np.zeros(len(s))
        for jj in range(j, n_ex):
            s = step_sim(s, 1, rng)
            h = payoff(s)
            ex = alive & (exercise_now(s, jj, coefs, payoff, basis, k) if jj < n_ex - 1 else h > 0)
            val[ex] = h[ex] * disc ** (jj + 1 - j)
            alive &= ~ex
        q[:, j] = val.reshape(n, n_inner).mean(axis=1) * disc ** j
    m = np.zeros(n)
    best = np.full(n, -np.inf)
    for j in range(1, n_ex + 1):
        s = outer[:, ex_idx[j - 1], :]
        h = payoff(s) * disc ** j
        ex = exercise_now(s, j - 1, coefs, payoff, basis, k) if j < n_ex else payoff(s) > 0
        cont = q[:, j] if j < n_ex else np.zeros(n)
        big_l = np.where(ex, h, cont)
        m = m + big_l - q[:, j - 1]
        best = np.maximum(best, h - m)
    return float(best.mean()), float(best.std() / math.sqrt(n))


# ---------------------------------------------------------------- Greeks
def call_greeks(s0, k, t, r, vol, n: int, seed: int, digital: bool = False, smooth: float = 0.0) -> dict:
    """Delta and vega of a call (or a digital, with an optional call-spread smoothing of half-width `smooth`) by
    the pathwise and the likelihood-ratio methods, with their standard errors, on one set of draws."""
    z = np.random.default_rng(seed).standard_normal(n)
    sq = math.sqrt(t)
    st = s0 * np.exp((r - 0.5 * vol * vol) * t + vol * sq * z)
    d = math.exp(-r * t)
    if digital:
        pay = (st > k).astype(float)
        if smooth > 0:
            dpay = ((st > k - smooth) & (st < k + smooth)) / (2 * smooth)
        else:
            dpay = np.zeros(n)                               # the pathwise derivative of an indicator is zero
    else:
        pay = np.maximum(st - k, 0.0)
        dpay = (st > k).astype(float)
    dst_ds0 = st / s0
    dst_dvol = st * (-vol * t + sq * z)
    est = {"pw_delta": d * dpay * dst_ds0, "lr_delta": d * pay * z / (s0 * vol * sq),
           "pw_vega": d * dpay * dst_dvol, "lr_vega": d * pay * ((z * z - 1) / vol - sq * z)}
    return {name: (float(x.mean()), float(x.std() / math.sqrt(n))) for name, x in est.items()}


def asian_adjoint(s0: float, k: float, t: float, r: float, vol: float, steps: int, buckets: int, n: int,
                  seed: int) -> dict:
    """Arithmetic Asian call under a volatility with one multiplier per time bucket: the price, the delta and the
    vega of every bucket from one forward and one reverse (adjoint) pass along each path."""
    dt = t / steps
    z = np.random.default_rng(seed).standard_normal((n, steps))
    sig = np.full(steps, vol)
    s = np.empty((n, steps + 1))
    s[:, 0] = s0
    for i in range(steps):                                              # forward pass, stored
        s[:, i + 1] = s[:, i] * np.exp((r - 0.5 * sig[i] ** 2) * dt + sig[i] * math.sqrt(dt) * z[:, i])
    avg = s[:, 1:].mean(axis=1)
    disc = math.exp(-r * t)
    price = disc * np.maximum(avg - k, 0.0)
    sbar = np.zeros((n, steps + 1))
    sbar[:, 1:] = (disc * (avg > k))[:, None] / steps                   # dPayoff/dS_i from the average
    sigbar = np.zeros((n, steps))
    for i in range(steps - 1, -1, -1):                                  # reverse pass
        sigbar[:, i] = sbar[:, i + 1] * s[:, i + 1] * (-sig[i] * dt + math.sqrt(dt) * z[:, i])
        sbar[:, i] += sbar[:, i + 1] * s[:, i + 1] / s[:, i]
    per = steps // buckets
    vegas = np.array([sigbar[:, b * per:(b + 1) * per].sum(axis=1).mean() for b in range(buckets)])
    return {"price": float(price.mean()), "delta": float(sbar[:, 0].mean()), "bucket_vega": vegas}


# ---------------------------------------------------------------- quasi-random numbers and the bridge
def halton(n: int, dim: int, shift=None) -> np.ndarray:
    """First n points of the Halton sequence in `dim` dimensions (bases: the first primes), skipping the origin,
    optionally shifted modulo one (a random shift gives independent randomised replications)."""
    primes, p = [], 2
    while len(primes) < dim:
        if all(p % q for q in primes):
            primes.append(p)
        p += 1
    idx = np.arange(1, n + 1)
    out = np.zeros((n, dim))
    for d, b in enumerate(primes):
        f, i = 1.0, idx.copy()
        x = np.zeros(n)
        while np.any(i > 0):
            f /= b
            x += f * (i % b)
            i //= b
        out[:, d] = x
    return out if shift is None else (out + shift) % 1.0


def brownian_bridge(z: np.ndarray, t: float) -> np.ndarray:
    """Map standard normals (n, steps), steps a power of two, to Brownian increments by the bridge: the first
    coordinate sets W_T, the next the midpoint, and so on, so the leading coordinates carry most variance."""
    n, steps = z.shape
    w = np.zeros((n, steps + 1))
    w[:, steps] = math.sqrt(t) * z[:, 0]
    col, gap = 1, steps
    while gap > 1:
        half = gap // 2
        for left in range(0, steps, gap):
            mid, right = left + half, left + gap
            mean = 0.5 * (w[:, left] + w[:, right])
            sd = math.sqrt(half * t / steps / 2)
            w[:, mid] = mean + sd * z[:, col]
            col += 1
        gap = half
    return np.diff(w, axis=1)


def norm_inv(u: np.ndarray) -> np.ndarray:
    """Inverse standard normal cdf by Newton's method on math.erf (no tabulated constants)."""
    u = np.asarray(u, float)
    x = np.zeros_like(u)
    erf = np.frompyfunc(math.erf, 1, 1)
    for _ in range(50):
        cdf = 0.5 * (1 + erf(x / math.sqrt(2)).astype(float))
        pdf = np.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)
        x = np.clip(x - (cdf - u) / np.maximum(pdf, 1e-300), -9.0, 9.0)
    return x
