"""Book 4, chapter 28: transforms, interpolation, root finding and algorithmic differentiation (teaching module).

COS pricing from the Levy exponents of firm.levy; zero-curve interpolation of the Treasury curve of 3 July 2023 by
linear, natural cubic spline and monotone (Fritsch-Carlson) methods; implied volatility by bisection, secant, Newton and
Brent; the gradient of a 400-input book by bumping, forward mode and reverse mode with firm.aad; checkpointing.
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "levy"))
sys.path.insert(0, str(ROOT / "code" / "firm" / "aad"))
import firm_aad as ad  # noqa: E402
from firm_levy import psi_bm, psi_merton, psi_vg, simulate_vg  # noqa: E402

CURVE = ROOT / "data" / "methods" / "ust_curve_2023-07-03.csv"


def _n(z):
    return 0.5 * math.erfc(-z / math.sqrt(2))


def bs(S, K, r, sigma, T, kind="call"):
    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    c = S * _n(d1) - K * math.exp(-r * T) * _n(d2)
    return c if kind == "call" else c - S + K * math.exp(-r * T)


# --- Fourier: the COS method -------------------------------------------------------------------------

def cos_call(psi0, S0, K, r, T, N, L=10.0, cumulants=None):
    """European call by Fang and Oosterlee's COS method: the put is expanded in cosines on [a, b] and the call follows
    by parity. psi0 is the exponent of log(S_T / S0) without drift; the martingale drift is added here."""
    omega = -psi0(-1j).real

    def phi(u):
        return np.exp(T * (1j * u * (r + omega) + psi0(u)))

    c1, c2, c4 = cumulants if cumulants else _cumulants(phi)
    width = L * math.sqrt(c2 + math.sqrt(c4))
    a, b = c1 - width, c1 + width
    x = math.log(S0 / K)
    k = np.arange(N)
    w = k * math.pi / (b - a)
    # put payoff K (1 - e^y)^+ on y in [a, 0]
    chi = (np.cos(w * (0 - a)) - np.cos(w * (a - a)) * math.exp(a) + w * np.sin(w * (0 - a))
           - w * np.sin(w * (a - a)) * math.exp(a)) / (1 + w**2)
    psi_k = np.where(k == 0, -a, np.sin(w * (0 - a)) / np.where(k == 0, 1, w))
    Vk = 2 / (b - a) * K * (psi_k - chi)
    terms = (phi(w) * np.exp(1j * w * (x - a))).real * Vk
    terms[0] *= 0.5
    put = math.exp(-r * T) * terms.sum()
    return put + S0 - K * math.exp(-r * T)


def _cumulants(phi, h=1e-3):
    """First, second and fourth cumulants of log(S_T/S0) by finite differences of log phi(-i t) (real)."""
    def cgf(t):
        return math.log(phi(-1j * t).real)
    c1 = (cgf(h) - cgf(-h)) / (2 * h)
    c2 = (cgf(h) - 2 * cgf(0) + cgf(-h)) / h**2
    c4 = (cgf(2 * h) - 4 * cgf(h) + 6 * cgf(0) - 4 * cgf(-h) + cgf(-2 * h)) / h**4
    return c1, c2, abs(c4)


MERTON = {"sigma": 0.15, "lam": 0.5, "mu_j": -0.1, "sigma_j": 0.2}
VG = {"theta": -0.14, "sigma": 0.2, "nu": 0.2}


def merton_exact(S0, K, r, T, sigma, lam, mu_j, sigma_j, n_terms=80):
    kappa = math.exp(mu_j + 0.5 * sigma_j**2) - 1
    lp = lam * (1 + kappa)
    out = 0.0
    for n in range(n_terms):
        w = math.exp(-lp * T + n * math.log(lp * T) - math.lgamma(n + 1))
        s = math.sqrt(sigma**2 + n * sigma_j**2 / T)
        rn = r - lam * kappa + n * math.log(1 + kappa) / T
        out += w * bs(S0, K, rn, s, T)
    return out


def cos_convergence(Ns=(8, 16, 32, 64, 128, 256), S0=100.0, K=100.0, r=0.03, T=1.0) -> list[tuple]:
    m = MERTON
    ref_m = merton_exact(S0, K, r, T, **m)
    ref_b = bs(S0, K, r, 0.2, T)
    rows = []

    def psi_m(u):
        return psi_merton(u, 0.0, m["sigma"], m["lam"], m["mu_j"], m["sigma_j"])
    for N in Ns:
        em = abs(cos_call(psi_m, S0, K, r, T, N) - ref_m)
        eb = abs(cos_call(lambda u: psi_bm(u, 0.0, 0.2), S0, K, r, T, N) - ref_b)
        rows.append((N, max(eb, 1e-16), max(em, 1e-16)))
    return rows


def vg_check(S0=100.0, K=100.0, r=0.03, T=1.0, n_paths=400_000, seed=28) -> dict:
    v = VG
    cos = cos_call(lambda u: psi_vg(u, v["theta"], v["sigma"], v["nu"]), S0, K, r, T, 256)
    omega = -psi_vg(-1j, v["theta"], v["sigma"], v["nu"]).real
    X = simulate_vg(T, 1, n_paths, seed, v["theta"], v["sigma"], v["nu"])[:, -1]
    pay = math.exp(-r * T) * np.maximum(S0 * np.exp((r + omega) * T + X) - K, 0.0)
    return {"cos": cos, "mc": float(pay.mean()), "se": float(pay.std(ddof=1) / math.sqrt(n_paths))}


def gil_pelaez_digital(S0=100.0, K=110.0, r=0.03, T=1.0, U=200.0, n=20_000) -> dict:
    """P(S_T > K) under Merton by the Gil-Pelaez formula, against the Poisson mixture of lognormals."""
    m = MERTON
    kappa = math.exp(m["mu_j"] + 0.5 * m["sigma_j"] ** 2) - 1
    omega = -psi_merton(-1j, 0.0, m["sigma"], m["lam"], m["mu_j"], m["sigma_j"]).real
    k = math.log(K / S0)
    u = np.linspace(1e-8, U, n + 1)
    phi = np.exp(T * (1j * u * (r + omega) + psi_merton(u, 0.0, m["sigma"], m["lam"], m["mu_j"], m["sigma_j"])))
    f = (np.exp(-1j * u * k) * phi / (1j * u)).real
    integral = float(np.sum(0.5 * (f[1:] + f[:-1]) * np.diff(u)))
    gp = 0.5 + integral / math.pi
    lp = m["lam"]
    exact = 0.0
    for j in range(80):
        w = math.exp(-lp * T + j * math.log(lp * T) - math.lgamma(j + 1))
        mean = (r + omega) * T + j * m["mu_j"]
        sd = math.sqrt(m["sigma"] ** 2 * T + j * m["sigma_j"] ** 2)
        exact += w * _n((mean - k) / sd)
    return {"gil_pelaez": gp, "exact": exact, "kappa": kappa}


# --- interpolation ------------------------------------------------------------------------------------

def load_curve():
    rows = [line.split(",") for line in CURVE.read_text().splitlines()[1:]]
    return np.array([float(r[0]) for r in rows]), np.array([float(r[2]) / 100 for r in rows])


def natural_spline(x, y):
    """Second derivatives M of the natural cubic spline (M_0 = M_n = 0) by a tridiagonal solve."""
    n = len(x) - 1
    h = np.diff(x)
    lo, di, up, rhs = np.zeros(n - 1), np.zeros(n - 1), np.zeros(n - 1), np.zeros(n - 1)
    for i in range(1, n):
        lo[i - 1], di[i - 1], up[i - 1] = h[i - 1], 2 * (h[i - 1] + h[i]), h[i]
        rhs[i - 1] = 6 * ((y[i + 1] - y[i]) / h[i] - (y[i] - y[i - 1]) / h[i - 1])
    sys.path.insert(0, str(ROOT / "code" / "firm" / "pde"))
    from firm_pde import thomas
    M = np.zeros(n + 1)
    M[1:-1] = thomas(lo, di, up, rhs)
    return M


def spline_eval(x, y, M, t, deriv=0):
    i = np.clip(np.searchsorted(x, t) - 1, 0, len(x) - 2)
    h = x[i + 1] - x[i]
    A, B = (x[i + 1] - t) / h, (t - x[i]) / h
    if deriv == 0:
        return A * y[i] + B * y[i + 1] + ((A**3 - A) * M[i] + (B**3 - B) * M[i + 1]) * h**2 / 6
    return (y[i + 1] - y[i]) / h + (-(3 * A**2 - 1) * M[i] + (3 * B**2 - 1) * M[i + 1]) * h / 6


def fritsch_carlson(x, y):
    """Slopes of a monotone piecewise cubic Hermite interpolant: harmonic-mean interior slopes (zero at a local
    extremum), limited so that alpha^2 + beta^2 <= 9."""
    h, d = np.diff(x), np.diff(y) / np.diff(x)
    m = np.zeros(len(x))
    for i in range(1, len(x) - 1):
        if d[i - 1] * d[i] > 0:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    m[0], m[-1] = d[0], d[-1]
    for i in range(len(d)):
        if d[i] == 0:
            m[i] = m[i + 1] = 0.0
            continue
        a, b = m[i] / d[i], m[i + 1] / d[i]
        if a * a + b * b > 9:
            t = 3 / math.sqrt(a * a + b * b)
            m[i], m[i + 1] = t * a * d[i], t * b * d[i]
    return m


def hermite_eval(x, y, m, t, deriv=0):
    i = np.clip(np.searchsorted(x, t) - 1, 0, len(x) - 2)
    h = x[i + 1] - x[i]
    s = (t - x[i]) / h
    if deriv == 0:
        return ((2 * s**3 - 3 * s**2 + 1) * y[i] + (s**3 - 2 * s**2 + s) * h * m[i] + (-2 * s**3 + 3 * s**2) * y[i + 1]
                + (s**3 - s**2) * h * m[i + 1])
    return ((6 * s**2 - 6 * s) * y[i] / h + (3 * s**2 - 4 * s + 1) * m[i] + (-6 * s**2 + 6 * s) * y[i + 1] / h
            + (3 * s**2 - 2 * s) * m[i + 1])


def forward_curves(step: float = 0.01) -> dict:
    """Instantaneous forwards f(t) = d(r t)/dt from three interpolations of the zero curve (yields as zero rates)."""
    x, r = load_curve()
    t = np.arange(x[0], 30.0 + 1e-9, step)
    xr = x * r
    lin = np.interp(t, x, r)
    lin_f = np.gradient(lin * t, t)
    M = natural_spline(x, r)
    sp_r = spline_eval(x, r, M, t)
    sp_f = sp_r + t * spline_eval(x, r, M, t, deriv=1)
    m = fritsch_carlson(x, xr)
    mono_f = hermite_eval(x, xr, m, t, deriv=1)
    return {"t": t, "linear": lin_f, "spline": sp_f, "monotone": mono_f, "zero_spline": sp_r, "pillars": (x, r)}


def runge(n: int = 10) -> float:
    """Largest error of the degree-n polynomial through n + 1 equispaced samples of 1/(1 + 25 x^2) on [-1, 1]."""
    xs = np.linspace(-1, 1, n + 1)
    c = np.polyfit(xs, 1 / (1 + 25 * xs**2), n)
    t = np.linspace(-1, 1, 20001)
    return float(np.max(np.abs(np.polyval(c, t) - 1 / (1 + 25 * t**2))))


# --- root finding ----------------------------------------------------------------------------------------

def _vega(S, K, r, s, T):
    d1 = (math.log(S / K) + (r + 0.5 * s * s) * T) / (s * math.sqrt(T))
    return S * math.exp(-0.5 * d1 * d1) / math.sqrt(2 * math.pi) * math.sqrt(T)


def brent(f, a, b, tol=1e-12, max_iter=200):
    """Brent's method (inverse quadratic interpolation, secant and bisection with Brent's safeguards)."""
    fa, fb = f(a), f(b)
    if fa * fb > 0:
        raise ValueError("root not bracketed")
    if abs(fa) < abs(fb):
        a, b, fa, fb = b, a, fb, fa
    c, fc, d, mflag = a, fa, b - a, True
    for it in range(1, max_iter + 1):
        if fa != fc and fb != fc:
            s = (a * fb * fc / ((fa - fb) * (fa - fc)) + b * fa * fc / ((fb - fa) * (fb - fc))
                 + c * fa * fb / ((fc - fa) * (fc - fb)))
        else:
            s = b - fb * (b - a) / (fb - fa)
        cond = (not ((3 * a + b) / 4 < s < b or b < s < (3 * a + b) / 4)
                or (mflag and abs(s - b) >= abs(b - c) / 2) or (not mflag and abs(s - b) >= abs(c - d) / 2)
                or (mflag and abs(b - c) < tol) or (not mflag and abs(c - d) < tol))
        if cond:
            s, mflag = (a + b) / 2, True
        else:
            mflag = False
        fs = f(s)
        d, c, fc = c, b, fb
        if fa * fs < 0:
            b, fb = s, fs
        else:
            a, fa = s, fs
        if abs(fa) < abs(fb):
            a, b, fa, fb = b, a, fb, fa
        if fb == 0 or abs(b - a) < tol:
            return b, it
    return b, max_iter


def implied_vol_iterations(strikes=(50, 70, 100, 150, 250, 400), S=100.0, r=0.03, T=1.0, true_vol=0.25) -> dict:
    """Iterations to recover the volatility to 1e-10 from the call price: bisection on [0.001, 5], secant from
    (0.2, 0.3), Newton from 0.2, Brent on [0.001, 5]; None when a method fails (non-finite or 100 iterations)."""
    out = {}
    for K in strikes:
        target = bs(S, K, r, true_vol, T)

        def f(s, K=K, target=target):
            return bs(S, K, r, s, T) - target
        a, b, it = 0.001, 5.0, 0
        while b - a > 1e-10:
            m = 0.5 * (a + b)
            it += 1
            if f(a) * f(m) <= 0:
                b = m
            else:
                a = m
        res = {"bisection": it}
        x0, x1, it = 0.2, 0.3, 0
        try:
            while abs(x1 - x0) > 1e-10 and it < 100:
                x0, x1 = x1, x1 - f(x1) * (x1 - x0) / (f(x1) - f(x0))
                it += 1
            res["secant"] = it if abs(x1 - true_vol) < 1e-8 else None
        except (ZeroDivisionError, ValueError, OverflowError):
            res["secant"] = None
        x, it = 0.2, 0
        try:
            while it < 100:
                step = f(x) / _vega(S, K, r, x, T)
                x -= step
                it += 1
                if abs(step) < 1e-10:
                    break
            res["newton"] = it if abs(x - true_vol) < 1e-8 else None
        except (ZeroDivisionError, ValueError, OverflowError):
            res["newton"] = None
        root, it = brent(f, 0.001, 5.0, tol=1e-10)
        res["brent"] = it if abs(root - true_vol) < 1e-8 else None
        out[K] = res
    return out


# --- algorithmic differentiation ---------------------------------------------------------------------------

def book(n_pillars: int = 400, seed: int = 28) -> dict:
    """A toy rates book on a 30-year zero curve with n pillars: quarterly fixed cash flows and 119 caplets on the
    three-month forwards (Black's formula), all from the linearly interpolated zero curve."""
    rng = np.random.default_rng(seed)
    pillars = np.linspace(30 / n_pillars, 30.0, n_pillars)
    z0 = 0.035 + 0.01 * (1 - np.exp(-pillars / 5)) + 0.0001 * rng.standard_normal(n_pillars)
    dates = np.arange(1, 121) * 0.25
    amounts = rng.uniform(-2.0, 5.0, dates.size)
    strikes = 0.04 + 0.01 * rng.standard_normal(dates.size)
    notionals = rng.uniform(0.0, 100.0, dates.size)
    return {"pillars": pillars, "z0": z0, "dates": dates, "amounts": amounts, "strikes": strikes,
            "notionals": notionals, "vol": 0.2}


def book_value(z, bk) -> object:
    """Works for floats, firm_aad.Var and firm_aad.Dual: the interpolation weights are constants."""
    p = bk["pillars"]

    def zero(t):
        j = int(np.clip(np.searchsorted(p, t) - 1, 0, len(p) - 2))
        w = (t - p[j]) / (p[j + 1] - p[j])
        if t <= p[0]:
            return z[0]
        return z[j] * (1 - w) + z[j + 1] * w

    df = [ad.exp(-(zero(t) * t)) for t in bk["dates"]]
    total = 0.0
    for i, t in enumerate(bk["dates"]):
        total = total + bk["amounts"][i] * df[i]
        if i == 0:
            continue
        fwd = (df[i - 1] / df[i] - 1.0) / 0.25
        tf = t - 0.25
        sd = bk["vol"] * math.sqrt(tf)
        d1 = (ad.log(fwd / bk["strikes"][i]) + 0.5 * sd * sd) / sd
        caplet = (fwd * ad.ncdf(d1) - bk["strikes"][i] * ad.ncdf(d1 - sd)) * (0.25 * bk["notionals"][i])
        total = total + caplet * df[i]
    return total


def gradients(n_pillars: int = 400) -> dict:
    bk = book(n_pillars)
    z = list(bk["z0"])

    def f(v):
        return book_value(v, bk)
    val, g_rev, st = ad.gradient(f, z)
    g_bump = ad.bump_gradient(f, z, h=1e-7, central=True)
    g_fwd = ad.forward_gradient(f, z)
    E, P = st["ops"], st["partials"]
    return {"value": val, "rev": np.array(g_rev), "bump": np.array(g_bump), "fwd": np.array(g_fwd), "ops": E,
            "partials": P, "ratio_reverse": (E + 2 * P) / E, "ratio_bump": n_pillars + 1,
            "ratio_forward": n_pillars * (E + 2 * P) / E, "n": n_pillars}


def cost_curve(ns=(25, 50, 100, 200, 400)) -> list[tuple]:
    """Cost of the gradient in evaluations, by the operation count, against the number of inputs."""
    rows = []
    for n in ns:
        bk = book(n)
        _, _, st = ad.gradient(lambda v, bk=bk: book_value(v, bk), list(bk["z0"]))
        E, P = st["ops"], st["partials"]
        rows.append((n, n + 1, n * (E + 2 * P) / E, (E + 2 * P) / E))
    return rows


def checkpoint_demo(n_steps: int = 10_000, every: int = 100) -> dict:
    """x_{k+1} = x_k + h (theta - x_k) + 0.1 h sin(x_k), loss x_n^2: gradient with a full tape and with checkpoints."""
    h = 1e-3

    def step(x, th):
        s = ad._unary(x, math.sin, math.cos)
        return x + (th - x) * h + s * (0.1 * h)

    def loss(x):
        return x * x
    full_tape = ad.Tape()
    x0v, thv = full_tape.var(0.5), full_tape.var(1.5)
    y = x0v
    for _ in range(n_steps):
        y = step(y, thv)
    lv = loss(y)
    bar = full_tape.adjoints(lv)
    cp = ad.checkpointed_gradient(step, 0.5, 1.5, n_steps, loss, every)
    return {"full": (bar[x0v.idx], bar[thv.idx]), "check": (cp["d_x0"], cp["d_theta"]),
            "full_nodes": full_tape.stats()["nodes"], "peak_states": cp["peak_states"], "n_steps": n_steps}
