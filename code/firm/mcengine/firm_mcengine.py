"""firm.mcengine -- the Monte Carlo engine of the miniature firm (One Quant Book 4, chapters 2, 4, 26).

Stage 1 (chapter 2): Brownian paths by increments and by Brownian-bridge (dyadic) construction,
correlated multi-dimensional increments, and the bridge crossing probability used to monitor a
barrier between grid points.

A reference generator, SplitMix64 with Box-Muller normals, is implemented identically in Python,
C++20 (cpp/firm_mcengine.hpp) and Rust (rust/src/lib.rs): the three languages produce the same
normal stream from the same seed. Bulk Python paths use NumPy's PCG64 for speed.

API (stable):
    SplitMix64(seed).next_u64() / .uniform() ; NormalStream(seed).next()
    reference_path(n_steps, T, seed)                 -> pure-Python path from the reference stream
    brownian_paths(n_paths, n_steps, T, seed, corr=None) -> (n_paths, n_steps+1[, d]) from W_0 = 0
    bridge_paths(n_paths, levels, T, seed)           -> (n_paths, 2**levels + 1), dyadic construction
    bridge_crossing_probability(x0, x1, barrier, var) -> P(bridge from x0 to x1 touches barrier)

Stage 2 (chapter 4): Euler-Maruyama for scalar SDEs, exact Ornstein-Uhlenbeck and square-root
transitions, plain and full-truncation Euler for the square-root process, the Feller ratio.
"""
from __future__ import annotations

import math

import numpy as np

MASK = (1 << 64) - 1


class SplitMix64:
    """Vigna's SplitMix64; `uniform` maps the top 53 bits to the open interval (0, 1)."""

    def __init__(self, seed: int) -> None:
        self.state = seed & MASK

    def next_u64(self) -> int:
        self.state = (self.state + 0x9E3779B97F4A7C15) & MASK
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
        return z ^ (z >> 31)

    def uniform(self) -> float:
        return ((self.next_u64() >> 11) + 0.5) * 2.0**-53


class NormalStream:
    """Standard normals by the Box-Muller transform, two per pair of uniforms (cosine first)."""

    def __init__(self, seed: int) -> None:
        self.gen = SplitMix64(seed)
        self.spare: float | None = None

    def next(self) -> float:
        if self.spare is not None:
            z, self.spare = self.spare, None
            return z
        u1, u2 = self.gen.uniform(), self.gen.uniform()
        r = math.sqrt(-2.0 * math.log(u1))
        a = 2.0 * math.pi * u2
        self.spare = r * math.sin(a)
        return r * math.cos(a)


def reference_path(n_steps: int, T: float, seed: int) -> list[float]:
    """One Brownian path on a uniform grid from the reference stream (the cross-language check)."""
    s = NormalStream(seed)
    dt = T / n_steps
    w = [0.0]
    for _ in range(n_steps):
        w.append(w[-1] + math.sqrt(dt) * s.next())
    return w


def brownian_paths(n_paths: int, n_steps: int, T: float, seed: int, corr: np.ndarray | None = None) -> np.ndarray:
    """Brownian paths on a uniform grid, W_0 = 0. With `corr` (d x d correlation matrix) the paths
    are d-dimensional with d<W^i, W^j>_t = corr[i, j] dt; shape (n_paths, n_steps + 1, d)."""
    rng = np.random.default_rng(seed)
    dt = T / n_steps
    if corr is None:
        dw = rng.standard_normal((n_paths, n_steps)) * math.sqrt(dt)
        return np.hstack([np.zeros((n_paths, 1)), np.cumsum(dw, axis=1)])
    c = np.linalg.cholesky(np.asarray(corr, dtype=float))
    d = c.shape[0]
    dw = rng.standard_normal((n_paths, n_steps, d)) @ c.T * math.sqrt(dt)
    return np.concatenate([np.zeros((n_paths, 1, d)), np.cumsum(dw, axis=1)], axis=1)


def bridge_paths(n_paths: int, levels: int, T: float, seed: int) -> np.ndarray:
    """Brownian paths on 2**levels steps built coarse to fine: W_T first, then the midpoints of each
    interval from the Brownian-bridge law N((W_l + W_r)/2, h/4) on an interval of length h."""
    rng = np.random.default_rng(seed)
    n = 2**levels
    dt = T / n
    w = np.zeros((n_paths, n + 1))
    w[:, n] = math.sqrt(T) * rng.standard_normal(n_paths)
    step = n
    while step > 1:
        half = step // 2
        mids = np.arange(half, n, step)
        z = rng.standard_normal((n_paths, mids.size))
        w[:, mids] = 0.5 * (w[:, mids - half] + w[:, mids + half]) + math.sqrt(half * dt / 2) * z
        step = half
    return w


def bridge_crossing_probability(x0, x1, barrier, var):
    """Probability that a Brownian bridge from x0 to x1 with total variance `var` (sigma^2 dt) touches
    `barrier`: exp(-2 (x0 - b)(x1 - b) / var) when both ends are on the same side, else one."""
    x0, x1 = np.asarray(x0, dtype=float), np.asarray(x1, dtype=float)
    prod = (x0 - barrier) * (x1 - barrier)
    return np.where(prod > 0, np.exp(-2.0 * np.maximum(prod, 0.0) / var), 1.0)


# ---------------------------------------------------------------------------------------------
# Stage 2 (chapter 4): stepping stochastic differential equations.
#   euler_maruyama(mu, sigma, x0, T, n_steps, n_paths, seed)        generic scalar SDE
#   ou_exact(x0, kappa, xbar, sigma, T, n_steps, n_paths, seed)      Gaussian transition
#   sqrt_exact(v0, kappa, vbar, eta, T, n_steps, n_paths, seed)      noncentral chi-square transition
#   sqrt_euler(v0, kappa, vbar, eta, T, n_steps, n_paths, seed, scheme="plain"|"full_truncation")
# ---------------------------------------------------------------------------------------------
def euler_maruyama(mu, sigma, x0: float, T: float, n_steps: int, n_paths: int, seed: int) -> np.ndarray:
    """X_{k+1} = X_k + mu(t_k, X_k) dt + sigma(t_k, X_k) sqrt(dt) Z_k, vectorised over paths."""
    rng = np.random.default_rng(seed)
    dt = T / n_steps
    x = np.empty((n_paths, n_steps + 1))
    x[:, 0] = x0
    for k in range(n_steps):
        t = k * dt
        z = rng.standard_normal(n_paths)
        x[:, k + 1] = x[:, k] + mu(t, x[:, k]) * dt + sigma(t, x[:, k]) * math.sqrt(dt) * z
    return x


def ou_exact(x0: float, kappa: float, xbar: float, sigma: float, T: float, n_steps: int, n_paths: int,
             seed: int) -> np.ndarray:
    """dX = kappa (xbar - X) dt + sigma dW sampled exactly: X_{k+1} ~ N(xbar + (X_k - xbar) e^{-kappa dt},
    sigma^2 (1 - e^{-2 kappa dt}) / (2 kappa))."""
    rng = np.random.default_rng(seed)
    dt = T / n_steps
    a = math.exp(-kappa * dt)
    sd = sigma * math.sqrt((1 - a * a) / (2 * kappa))
    x = np.empty((n_paths, n_steps + 1))
    x[:, 0] = x0
    for k in range(n_steps):
        x[:, k + 1] = xbar + (x[:, k] - xbar) * a + sd * rng.standard_normal(n_paths)
    return x


def sqrt_exact(v0: float, kappa: float, vbar: float, eta: float, T: float, n_steps: int, n_paths: int,
               seed: int) -> np.ndarray:
    """dv = kappa (vbar - v) dt + eta sqrt(v) dW sampled exactly: v_{k+1} = c chi'^2_d(lambda) with
    c = eta^2 (1 - e^{-kappa dt}) / (4 kappa), d = 4 kappa vbar / eta^2, lambda = v_k e^{-kappa dt} / c."""
    rng = np.random.default_rng(seed)
    dt = T / n_steps
    c = eta**2 * (1 - math.exp(-kappa * dt)) / (4 * kappa)
    d = 4 * kappa * vbar / eta**2
    v = np.empty((n_paths, n_steps + 1))
    v[:, 0] = v0
    for k in range(n_steps):
        lam = v[:, k] * math.exp(-kappa * dt) / c
        v[:, k + 1] = c * rng.noncentral_chisquare(d, np.maximum(lam, 1e-300))
    return v


def sqrt_euler(v0: float, kappa: float, vbar: float, eta: float, T: float, n_steps: int, n_paths: int,
               seed: int, scheme: str = "plain") -> np.ndarray:
    """Euler steps of the square-root process. 'plain' takes sqrt(v) and yields NaN after a negative
    value; 'full_truncation' (Lord, Koekkoek and van Dijk) uses v^+ in drift and diffusion and
    reports v^+."""
    rng = np.random.default_rng(seed)
    dt = T / n_steps
    v = np.empty((n_paths, n_steps + 1))
    v[:, 0] = v0
    for k in range(n_steps):
        z = rng.standard_normal(n_paths)
        vk = v[:, k] if scheme == "plain" else np.maximum(v[:, k], 0.0)
        with np.errstate(invalid="ignore"):
            v[:, k + 1] = v[:, k] + kappa * (vbar - vk) * dt + eta * np.sqrt(vk) * math.sqrt(dt) * z
    return v if scheme == "plain" else np.maximum(v, 0.0)


def feller_ratio(kappa: float, vbar: float, eta: float) -> float:
    """2 kappa vbar / eta^2: zero is unattainable for the square-root process iff it is at least 1."""
    return 2 * kappa * vbar / eta**2


# ---------------------------------------------------------------------------------------------
# Stage 3 (chapter 26): generators, low discrepancy and variance reduction.
#   philox4x64(counter, key)                  Philox4x64-10 block (Salmon et al. 2011), pure Python
#   philox_uniforms(n_paths, dim, seed, stream=0)  counter-based uniforms: path j, block b -> counter (b, j, stream, 0)
#   sobol_directions(dim) / sobol_points(n, dim)    Joe-Kuo (new-joe-kuo-6.21201) directions, Gray-code order
#   owen_scramble(X, seed) -> uniforms          nested uniform (Owen) scrambling by hashing tree nodes
#   norm_ppf(u)                                inverse normal (Acklam, relative error below 1.2e-9)
#   bridge_from_normals(Z, T)                  Brownian bridge construction from given normals
#   asian_payoffs(W, S0, K, r, sigma, T)       discounted arithmetic and geometric average-price payoffs
#   geometric_asian_price(S0, K, r, sigma, T, n)    closed form of the control variate
#   control_variate(y, c, c_mean)              optimal-coefficient control-variate estimate
#   mlmc(sampler, eps, ...)                    Giles's multilevel driver
# ---------------------------------------------------------------------------------------------
M32 = 0xFFFFFFFF
PHILOX_M = (0xD2E7470EE14C6C93, 0xCA5A826395121157)
PHILOX_W = (0x9E3779B97F4A7C15, 0xBB67AE8584CAA73B)


def philox4x64(counter, key, rounds: int = 10) -> tuple:
    """One Philox4x64 block: ten rounds of two 64 x 64 -> 128-bit multiplications and a key schedule."""
    c0, c1, c2, c3 = counter
    k0, k1 = key
    for _ in range(rounds):
        p0, p1 = PHILOX_M[0] * c0, PHILOX_M[1] * c2
        c0, c1, c2, c3 = (p1 >> 64) ^ c1 ^ k0, p1 & MASK, (p0 >> 64) ^ c3 ^ k1, p0 & MASK
        k0, k1 = (k0 + PHILOX_W[0]) & MASK, (k1 + PHILOX_W[1]) & MASK
    return c0, c1, c2, c3


def _mulhilo(a: np.ndarray, b: int) -> tuple:
    """High and low 64-bit halves of a * b for uint64 arrays, from 32-bit limbs."""
    b = np.uint64(b)
    m = np.uint64(M32)
    s = np.uint64(32)
    a_lo, a_hi, b_lo, b_hi = a & m, a >> s, b & m, b >> s
    p0, p1, p2, p3 = a_lo * b_lo, a_lo * b_hi, a_hi * b_lo, a_hi * b_hi
    mid = (p0 >> s) + (p1 & m) + (p2 & m)
    return p3 + (p1 >> s) + (p2 >> s) + (mid >> s), a * b


def philox_uniforms(n_paths: int, dim: int, seed: int, stream: int = 0, first_path: int = 0) -> np.ndarray:
    """Uniforms on (0, 1), shape (n_paths, dim). Path j's numbers depend only on (seed, stream, j): any
    split of the paths across machines reproduces them."""
    nb = -(-dim // 4)
    j = np.arange(first_path, first_path + n_paths, dtype=np.uint64)
    out = np.empty((n_paths, 4 * nb), dtype=np.uint64)
    for blk in range(nb):
        c0 = np.full(n_paths, blk, dtype=np.uint64)
        c1, c2, c3 = j.copy(), np.full(n_paths, stream, dtype=np.uint64), np.zeros(n_paths, dtype=np.uint64)
        k0, k1 = seed & MASK, 0
        for _ in range(10):
            h0, l0 = _mulhilo(c0, PHILOX_M[0])
            h1, l1 = _mulhilo(c2, PHILOX_M[1])
            c0, c1, c2, c3 = h1 ^ c1 ^ np.uint64(k0), l1, h0 ^ c3 ^ np.uint64(k1), l0
            k0, k1 = (k0 + PHILOX_W[0]) & MASK, (k1 + PHILOX_W[1]) & MASK
        out[:, 4 * blk:4 * blk + 4] = np.stack([c0, c1, c2, c3], axis=1)
    return ((out[:, :dim] >> np.uint64(11)).astype(float) + 0.5) * 2.0**-53


def sobol_directions(dim: int) -> np.ndarray:
    """32 direction integers per dimension (dimension 1 is the van der Corput sequence in base 2), from the
    first 64 dimensions of Joe and Kuo's new-joe-kuo-6.21201 (BSD-style licence in data/)."""
    from pathlib import Path
    jk = Path(__file__).resolve().parent / "data" / "new-joe-kuo-6.21201.first64"
    rows = [line.split() for line in jk.read_text().splitlines()[1:dim]]
    V = np.zeros((dim, 32), dtype=np.uint64)
    V[0] = [1 << (31 - k) for k in range(32)]
    for d, row in enumerate(rows, start=1):
        s, a, m = int(row[1]), int(row[2]), [int(x) for x in row[3:]]
        v = [m[k] << (31 - k) for k in range(s)]
        for i in range(s, 32):
            x = v[i - s] ^ (v[i - s] >> s)
            for k in range(1, s):
                if (a >> (s - 1 - k)) & 1:
                    x ^= v[i - k]
            v.append(x)
        V[d] = v
    return V


def sobol_points(n: int, dim: int) -> np.ndarray:
    """The first n Sobol points as 32-bit integers, shape (n, dim), in Gray-code order (point 0 is 0)."""
    V = sobol_directions(dim)
    i = np.arange(n, dtype=np.uint64)
    g = i ^ (i >> np.uint64(1))
    X = np.zeros((n, dim), dtype=np.uint64)
    for b in range(max(1, int(n - 1).bit_length())):
        on = ((g >> np.uint64(b)) & np.uint64(1)).astype(bool)
        X[on] ^= V[:, b]
    return X


def _mix64(z):
    z = (z ^ (z >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
    z = (z ^ (z >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
    return z ^ (z >> np.uint64(31))


def owen_scramble(X: np.ndarray, seed: int) -> np.ndarray:
    """Nested uniform scrambling: digit l of coordinate d is flipped by a random bit attached to the node
    (d, l, first l digits) of the binary tree, drawn by hashing. Returns uniforms (y + 1/2) 2^-32."""
    Y = X.copy()
    for d in range(X.shape[1]):
        x = X[:, d]
        for lev in range(32):
            prefix = x >> np.uint64(32 - lev) if lev else np.zeros_like(x)
            node = np.uint64(d << 40) ^ np.uint64(lev << 32) ^ prefix
            bit = _mix64(np.uint64(seed & MASK) ^ _mix64(node)) >> np.uint64(63)
            Y[:, d] ^= bit << np.uint64(31 - lev)
    return (Y.astype(float) + 0.5) * 2.0**-32


_ACK_A = (-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02, 1.383577518672690e+02,
          -3.066479806614716e+01, 2.506628277459239e+00)
_ACK_B = (-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02, 6.680131188771972e+01,
          -1.328068155288572e+01)
_ACK_C = (-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00, -2.549732539343734e+00,
          4.374664141464968e+00, 2.938163982698783e+00)
_ACK_D = (7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00)


def norm_ppf(u) -> np.ndarray:
    """Inverse standard normal distribution function (Acklam's rational approximation)."""
    u = np.asarray(u, dtype=float)
    a, b, c, d = _ACK_A, _ACK_B, _ACK_C, _ACK_D
    out = np.empty_like(u)
    lo, hi = u < 0.02425, u > 1 - 0.02425
    mid = ~(lo | hi)
    q = u[mid] - 0.5
    r = q * q
    out[mid] = ((((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q
                / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1))
    for mask, sign, v in ((lo, 1.0, u[lo]), (hi, -1.0, 1 - u[hi])):
        q = np.sqrt(-2 * np.log(v))
        out[mask] = sign * ((((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
                            / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1))
    return out


def bridge_from_normals(Z: np.ndarray, T: float) -> np.ndarray:
    """Brownian paths on 2**L steps from normals Z (n, 2**L) in bridge order: column 0 gives W_T, the next
    columns the midpoints level by level, left to right; the most important directions come first."""
    n_paths, n = Z.shape
    dt = T / n
    w = np.zeros((n_paths, n + 1))
    w[:, n] = math.sqrt(T) * Z[:, 0]
    col, step = 1, n
    while step > 1:
        half = step // 2
        mids = np.arange(half, n, step)
        z = Z[:, col:col + mids.size]
        w[:, mids] = 0.5 * (w[:, mids - half] + w[:, mids + half]) + math.sqrt(half * dt / 2) * z
        col, step = col + mids.size, half
    return w


def increment_from_normals(Z: np.ndarray, T: float) -> np.ndarray:
    """Brownian paths from normals Z (n, m) taken as the successive increments."""
    dt = T / Z.shape[1]
    return np.hstack([np.zeros((Z.shape[0], 1)), np.cumsum(Z * math.sqrt(dt), axis=1)])


def asian_payoffs(W: np.ndarray, S0: float, K: float, r: float, sigma: float, T: float) -> tuple:
    """Discounted arithmetic- and geometric-average call payoffs on the fixings t_k = kT/n, k = 1..n."""
    n = W.shape[1] - 1
    t = np.arange(1, n + 1) * T / n
    logS = math.log(S0) + (r - 0.5 * sigma**2) * t + sigma * W[:, 1:]
    disc = math.exp(-r * T)
    arith = disc * np.maximum(np.exp(logS).mean(axis=1) - K, 0.0)
    geo = disc * np.maximum(np.exp(logS.mean(axis=1)) - K, 0.0)
    return arith, geo


def _ncdf(x: float) -> float:
    return 0.5 * math.erfc(-x / math.sqrt(2))


def geometric_asian_price(S0: float, K: float, r: float, sigma: float, T: float, n: int) -> float:
    """Closed-form price of the discretely monitored geometric-average call: log G is normal."""
    t = np.arange(1, n + 1) * T / n
    m = math.log(S0) + (r - 0.5 * sigma**2) * t.mean()
    v = sigma**2 * float(np.minimum.outer(t, t).sum()) / n**2
    d2 = (m - math.log(K)) / math.sqrt(v)
    return math.exp(-r * T) * (math.exp(m + v / 2) * _ncdf(d2 + math.sqrt(v)) - K * _ncdf(d2))


def control_variate(y: np.ndarray, c: np.ndarray, c_mean: float) -> dict:
    """Estimate E[y] by mean(y - beta (c - E c)) with beta = Cov(y, c) / Var(c); variance factor 1 - rho^2."""
    cov = np.cov(y, c)
    beta = cov[0, 1] / cov[1, 1]
    z = y - beta * (c - c_mean)
    rho = cov[0, 1] / math.sqrt(cov[0, 0] * cov[1, 1])
    return {"est": float(z.mean()), "se": float(z.std(ddof=1) / math.sqrt(y.size)), "beta": float(beta),
            "rho": float(rho), "z": z}


def mlmc(sampler, eps: float, L0: int = 2, N0: int = 10_000, alpha: float = 1.0, max_level: int = 12) -> dict:
    """Giles's multilevel Monte Carlo. sampler(l, n) returns n samples of Y_l = P_l - P_{l-1} (P_0 at l = 0)
    and the cost of one sample; the sample sizes minimise cost for variance eps^2/2, and levels are added
    until the estimated bias |E Y_L| / (2^alpha - 1) is below eps / sqrt(2)."""
    L = L0
    s1, s2, N, C = [0.0] * (L + 1), [0.0] * (L + 1), [0] * (L + 1), [0.0] * (L + 1)
    dN = [N0] * (L + 1)
    while True:
        for lev in range(L + 1):
            if dN[lev] > 0:
                y, c = sampler(lev, dN[lev])
                s1[lev] += float(y.sum())
                s2[lev] += float((y * y).sum())
                N[lev] += dN[lev]
                C[lev] = c
        m = [s1[k] / N[k] for k in range(L + 1)]
        V = [max(s2[k] / N[k] - m[k] ** 2, 1e-300) for k in range(L + 1)]
        tot = sum(math.sqrt(V[k] * C[k]) for k in range(L + 1))
        Nopt = [math.ceil(2 / eps**2 * math.sqrt(V[k] / C[k]) * tot) for k in range(L + 1)]
        dN = [max(0, Nopt[k] - N[k]) for k in range(L + 1)]
        if any(dN):
            continue
        bias = max(abs(m[L]), abs(m[L - 1]) / 2**alpha) / (2**alpha - 1)
        if bias < eps / math.sqrt(2) or L == max_level:
            return {"est": sum(m), "N": N, "V": V, "mean": m, "C": C, "L": L,
                    "cost": sum(N[k] * C[k] for k in range(L + 1))}
        L += 1
        s1.append(0.0), s2.append(0.0), N.append(0), C.append(0.0)
        dN = [0] * L + [N0]
