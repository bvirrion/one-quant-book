"""firm.coint -- vector autoregressions and cointegration (One Quant Book 4, chapter 20).

VAR estimation by least squares with impulse responses and variance decompositions, Granger-causality F-tests,
the Engle-Granger residual test with MacKinnon (2010) critical values, and Johansen's reduced-rank analysis
(trace and maximum-eigenvalue statistics, constant restricted to the cointegrating space) with critical values
simulated by this module. NumPy only.

API (stable):
    var_fit(Y, p)                          dict(c, A (p, k, k), Sigma, resid, aic)
    var_stable(A)                          True if all companion eigenvalues lie inside the unit circle
    irf(A, Sigma, horizon, orth=True)      (horizon + 1, k, k) responses of variable i to shock j
    fevd(A, Sigma, horizon)                (k, k) share of variable i's h-step forecast variance due to shock j
    granger_test(Y, p, cause, effect)      (F, df1, df2, p-value)
    f_sf(F, d1, d2)                        upper tail of the F distribution (regularised incomplete beta)
    engle_granger(y, X, lags=0)            dict(tau, beta, crit) with MacKinnon critical values for N = 1 + X.shape[1]
    johansen(Y, lags)                      dict(eigvals, trace, maxeig, beta, alpha, crit_trace, crit_max)
    johansen_crit_sim(m, T, reps, seed)    simulated 90/95/99% quantiles of the trace and max statistics
"""
from __future__ import annotations

import math

import numpy as np

# MacKinnon (2010), Table 2, tau_c for N = 1..3 variables: (beta_inf, beta_1, beta_2, beta_3) at 1%, 5%, 10%.
MACKINNON_C = {
    1: [(-3.43035, -6.5393, -16.786, -79.433), (-2.86154, -2.8903, -4.234, -40.040), (-2.56677, -1.5384, -2.809, 0.0)],
    2: [(-3.89644, -10.9519, -22.527, 0.0), (-3.33613, -6.1101, -6.823, 0.0), (-3.04445, -4.2412, -2.720, 0.0)],
    3: [(-4.29374, -14.4354, -33.195, 47.433), (-3.74066, -8.5631, -10.852, 27.982), (-3.45218, -6.2143, -3.718, 0.0)],
}

# Trace and maximum-eigenvalue critical values (90%, 95%, 99%) for m = k - r common trends, constant restricted to
# the cointegrating space; simulated by johansen_crit_sim(m, T=2000, reps=20000, seed=20). The acceptance tests
# re-simulate them.
JOHANSEN_CRIT = {
    "trace": {1: (7.60, 9.23, 12.49), 2: (18.05, 20.36, 25.37), 3: (32.36, 35.23, 40.94)},
    "max": {1: (7.60, 9.23, 12.49), 2: (13.99, 15.98, 20.39), 3: (20.12, 22.32, 27.05)},
}


def _lags(Y, p):
    Y = np.asarray(Y, dtype=float)
    n = Y.shape[0]
    X = np.column_stack([np.ones(n - p)] + [Y[p - i - 1: n - i - 1] for i in range(p)])
    return Y[p:], X


def var_fit(Y, p: int) -> dict:
    Yt, X = _lags(Y, p)
    B, *_ = np.linalg.lstsq(X, Yt, rcond=None)
    E = Yt - X @ B
    k = Yt.shape[1]
    Sigma = E.T @ E / (Yt.shape[0] - X.shape[1])
    A = np.array([B[1 + i * k: 1 + (i + 1) * k].T for i in range(p)])
    s_ml = E.T @ E / Yt.shape[0]
    aic = math.log(np.linalg.det(s_ml)) + 2 * p * k * k / Yt.shape[0]
    return {"c": B[0], "A": A, "Sigma": Sigma, "resid": E, "aic": aic}


def _companion(A):
    p, k, _ = A.shape
    C = np.zeros((p * k, p * k))
    C[:k] = np.hstack(list(A))
    C[k:, :-k] = np.eye((p - 1) * k)
    return C


def var_stable(A) -> bool:
    return bool(np.max(np.abs(np.linalg.eigvals(_companion(np.asarray(A))))) < 1)


def irf(A, Sigma, horizon: int, orth: bool = True) -> np.ndarray:
    """Psi_h (MA coefficients) times the Cholesky factor of Sigma when orth: out[h, i, j] is the response of
    variable i, h periods after a one-standard-deviation orthogonalised shock to variable j."""
    A = np.asarray(A)
    p, k, _ = A.shape
    psi = [np.eye(k)]
    for h in range(1, horizon + 1):
        psi.append(sum(A[i] @ psi[h - 1 - i] for i in range(min(p, h))))
    L = np.linalg.cholesky(Sigma) if orth else np.eye(k)
    return np.array([m @ L for m in psi])


def fevd(A, Sigma, horizon: int) -> np.ndarray:
    th = irf(A, Sigma, horizon - 1)
    contrib = np.sum(th**2, axis=0)
    return contrib / contrib.sum(axis=1, keepdims=True)


def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the incomplete beta function (modified Lentz)."""
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 1000):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c if abs(1.0 + aa / c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c if abs(1.0 + aa / c) > tiny else tiny
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-15:
            break
    return h


def _betainc(a: float, b: float, x: float) -> float:
    """Regularised incomplete beta I_x(a, b)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lb = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x)
    if x < (a + 1) / (a + b + 2):
        return math.exp(lb) * _betacf(a, b, x) / a
    return 1.0 - math.exp(lb) * _betacf(b, a, 1 - x) / b


def f_sf(F: float, d1: int, d2: int) -> float:
    """P(F_{d1, d2} > F) = I_{d2 / (d2 + d1 F)}(d2 / 2, d1 / 2)."""
    return _betainc(d2 / 2, d1 / 2, d2 / (d2 + d1 * F))


def granger_test(Y, p: int, cause: int, effect: int) -> tuple[float, int, int, float]:
    """F-test that the p lags of variable `cause` have zero coefficients in the equation of `effect`."""
    Yt, X = _lags(Y, p)
    k = np.asarray(Y).shape[1]
    y = Yt[:, effect]
    drop = [1 + i * k + cause for i in range(p)]
    keep = [j for j in range(X.shape[1]) if j not in drop]
    e_u = y - X @ np.linalg.lstsq(X, y, rcond=None)[0]
    e_r = y - X[:, keep] @ np.linalg.lstsq(X[:, keep], y, rcond=None)[0]
    df1, df2 = p, y.size - X.shape[1]
    F = ((e_r @ e_r - e_u @ e_u) / df1) / (e_u @ e_u / df2)
    return float(F), df1, df2, f_sf(float(F), df1, df2)


def engle_granger(y, X, lags: int = 0) -> dict:
    """Regress y on (1, X), then a Dickey-Fuller regression (no constant) on the residuals; critical values for N =
    1 + number of regressors from MacKinnon's response surfaces."""
    y, X = np.asarray(y, float), np.atleast_2d(np.asarray(X, float).T).T
    D = np.column_stack([np.ones(y.size), X])
    beta, *_ = np.linalg.lstsq(D, y, rcond=None)
    u = y - D @ beta
    du = np.diff(u)
    n = du.size - lags
    cols = [u[lags:-1]] + [du[lags - j: du.size - j] for j in range(1, lags + 1)]
    Z = np.column_stack(cols)
    g, *_ = np.linalg.lstsq(Z, du[lags:], rcond=None)
    e = du[lags:] - Z @ g
    se = math.sqrt(float(e @ e) / (n - Z.shape[1]) * np.linalg.inv(Z.T @ Z)[0, 0])
    N = 1 + X.shape[1]
    crit = tuple(b0 + b1 / n + b2 / n**2 + b3 / n**3 for b0, b1, b2, b3 in MACKINNON_C[N])
    return {"tau": float(g[0]) / se, "beta": beta, "resid": u, "crit": crit, "n": n}


def _johansen_core(Y, lags):
    Y = np.asarray(Y, dtype=float)
    dY = np.diff(Y, axis=0)
    T = dY.shape[0] - lags
    Z0 = dY[lags:]
    Z1 = np.column_stack([Y[lags:-1], np.ones(T)])                 # constant restricted to the cointegrating space
    if lags:
        Z2 = np.column_stack([dY[lags - j: dY.shape[0] - j] for j in range(1, lags + 1)])
        R0 = Z0 - Z2 @ np.linalg.lstsq(Z2, Z0, rcond=None)[0]
        R1 = Z1 - Z2 @ np.linalg.lstsq(Z2, Z1, rcond=None)[0]
    else:
        R0, R1 = Z0, Z1
    S00, S11, S01 = R0.T @ R0 / T, R1.T @ R1 / T, R0.T @ R1 / T
    Lc = np.linalg.cholesky(S11)
    Li = np.linalg.inv(Lc)
    M = Li @ S01.T @ np.linalg.solve(S00, S01) @ Li.T
    lam, V = np.linalg.eigh(M)
    order = np.argsort(lam)[::-1]
    lam, V = lam[order], V[:, order]
    B = Li.T @ V                                                          # beta' S11 beta = I
    return lam, B, S01, T


def johansen(Y, lags: int = 1) -> dict:
    Y = np.asarray(Y, dtype=float)
    k = Y.shape[1]
    lam, B, S01, T = _johansen_core(Y, lags)
    lam = np.clip(lam[:k], 0, 1 - 1e-15)
    trace = np.array([-T * np.sum(np.log(1 - lam[r:])) for r in range(k)])
    maxeig = -T * np.log(1 - lam)
    alpha = S01 @ B[:, :k]
    return {"eigvals": lam, "trace": trace, "maxeig": maxeig, "beta": B[:, :k], "alpha": alpha, "T": T,
            "crit_trace": [JOHANSEN_CRIT["trace"][k - r] for r in range(k)],
            "crit_max": [JOHANSEN_CRIT["max"][k - r] for r in range(k)]}


def johansen_crit_sim(m: int, T: int = 2000, reps: int = 20_000, seed: int = 20) -> dict:
    """Quantiles of the trace and maximum-eigenvalue statistics for r = 0 when all m series are independent random
    walks (no lags, constant restricted)."""
    rng = np.random.default_rng(seed)
    tr, mx = np.empty(reps), np.empty(reps)
    for i in range(reps):
        Y = np.cumsum(rng.standard_normal((T + 1, m)), axis=0)
        lam = np.clip(_johansen_core(Y, 0)[0][:m], 0, 1 - 1e-15)
        tr[i] = -T * np.sum(np.log(1 - lam))
        mx[i] = -T * np.log(1 - lam[0])
    q = [0.90, 0.95, 0.99]
    return {"trace": tuple(float(v) for v in np.quantile(tr, q)), "max": tuple(float(v) for v in np.quantile(mx, q))}
