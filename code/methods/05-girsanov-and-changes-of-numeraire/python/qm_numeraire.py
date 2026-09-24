"""Chapter 5 of Book 4: Girsanov and changes of numeraire.

An Ornstein-Uhlenbeck short rate dr = kappa (rbar - r) dt + sigma dW under the risk-neutral measure;
zero-coupon bonds in closed form; a caplet priced three ways: Monte Carlo under Q with money-market
discounting, Monte Carlo under the payment-date forward measure, and the closed form the forward
measure yields (a put on a zero-coupon bond)."""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/numeraire"))
from firm_numeraire import change_of_numeraire_weights, girsanov_weights, reweighted_mean

R0, KAPPA, RBAR, SIGMA = 0.03, 0.5, 0.04, 0.01
T1, DELTA, STRIKE = 5.0, 0.25, 0.045               # caplet on the rate fixing at T1, paid at T1 + delta


def Phi(x: float) -> float:
    return 0.5 * math.erfc(-x / math.sqrt(2))


def B(tau: float) -> float:
    return (1 - math.exp(-KAPPA * tau)) / KAPPA


def A(tau: float) -> float:
    b = B(tau)
    return (RBAR - SIGMA**2 / (2 * KAPPA**2)) * (b - tau) - SIGMA**2 * b * b / (4 * KAPPA)


def zcb(r, tau: float):
    """P(t, t + tau) given r_t = r (Feynman-Kac, chapter 4)."""
    return np.exp(A(tau) - B(tau) * np.asarray(r, float))


def forward_rate(t: float) -> float:
    """Instantaneous forward f(0, t) = -d ln P(0, t) / dt, by a central difference."""
    h = 1e-5
    return -(math.log(zcb(R0, t + h)) - math.log(zcb(R0, t - h))) / (2 * h)


def expected_short_rate(t: float) -> float:
    return RBAR + (R0 - RBAR) * math.exp(-KAPPA * t)


def caplet_closed_form(T=T1, delta=DELTA, K=STRIKE) -> float:
    """(1 + delta K) times a put, struck at 1/(1 + delta K), expiring at T, on the bond maturing at
    T + delta: under the T-forward measure the bond price at T is lognormal (Jamshidian)."""
    x = 1 / (1 + delta * K)
    p1, p2 = float(zcb(R0, T)), float(zcb(R0, T + delta))
    sp = SIGMA * math.sqrt((1 - math.exp(-2 * KAPPA * T)) / (2 * KAPPA)) * B(delta)
    h = math.log(p2 / (p1 * x)) / sp + sp / 2
    put = x * p1 * Phi(-h + sp) - p2 * Phi(-h)
    return (1 + delta * K) * put


def caplet_payoff_at_fixing(r_T, delta=DELTA, K=STRIKE):
    """Value at the fixing date of the caplet's payment: (1 + delta K)(x - P(T, T + delta))^+."""
    x = 1 / (1 + delta * K)
    return (1 + delta * K) * np.maximum(x - zcb(r_T, delta), 0.0)


def mc_risk_neutral(n_paths: int, steps_per_year: int = 52, seed: int = 1, T=T1) -> dict:
    """Under Q: exact OU steps, trapezoid integral of r, discount by the money-market account."""
    rng = np.random.default_rng(seed)
    n = int(T * steps_per_year)
    dt = T / n
    a = math.exp(-KAPPA * dt)
    sd = SIGMA * math.sqrt((1 - a * a) / (2 * KAPPA))
    r = np.full(n_paths, R0)
    integral = np.zeros(n_paths)
    for _ in range(n):
        r_new = RBAR + (r - RBAR) * a + sd * rng.standard_normal(n_paths)
        integral += 0.5 * (r + r_new) * dt
        r = r_new
    y = np.exp(-integral) * caplet_payoff_at_fixing(r)
    return {"price": float(y.mean()), "se": float(y.std(ddof=1) / math.sqrt(n_paths)), "normals": n,
            "r_T": r, "bank": np.exp(integral), "payoff": caplet_payoff_at_fixing(r)}


def forward_measure_moments(T=T1) -> tuple[float, float]:
    """Mean and variance of r_T under the T-forward measure: the drift loses sigma^2 B(T - t)."""
    shift = SIGMA**2 / KAPPA * ((1 - math.exp(-KAPPA * T)) / KAPPA - (1 - math.exp(-2 * KAPPA * T)) / (2 * KAPPA))
    var = SIGMA**2 * (1 - math.exp(-2 * KAPPA * T)) / (2 * KAPPA)
    return expected_short_rate(T) - shift, var


def mc_forward(n_paths: int, seed: int = 2, T=T1) -> dict:
    """Under Q^T: one Gaussian draw of r_T per path; price = P(0, T) E^T[payoff]."""
    rng = np.random.default_rng(seed)
    m, v = forward_measure_moments(T)
    r = m + math.sqrt(v) * rng.standard_normal(n_paths)
    y = float(zcb(R0, T)) * caplet_payoff_at_fixing(r)
    return {"price": float(y.mean()), "se": float(y.std(ddof=1) / math.sqrt(n_paths)), "normals": 1}


def convergence_table(sizes=(250, 500, 1000, 2000, 4000, 8000, 16000, 32000, 64000)) -> list[tuple]:
    rows = []
    for i, n in enumerate(sizes):
        q = mc_risk_neutral(n, seed=100 + i)
        f = mc_forward(n, seed=200 + i)
        rows.append((n, q["price"], q["se"], f["price"], f["se"]))
    return rows


def reweighting_check(n_paths: int = 100_000, seed: int = 3) -> dict:
    """Samples under Q reweighted by dQ^T/dQ = (P(T,T)/P(0,T)) / (B_T/B_0) reproduce E^T[r_T]."""
    q = mc_risk_neutral(n_paths, seed=seed)
    w = change_of_numeraire_weights(1.0, float(zcb(R0, T1)), q["bank"], 1.0)
    est, se = reweighted_mean(q["r_T"], w)
    return {"est": est, "se": se, "theory": forward_measure_moments()[0], "mean_w": float(w.mean())}


def girsanov_histogram(gamma: float = 1.0, n: int = 200_000, seed: int = 4) -> dict:
    """W_1 ~ N(0, 1) under P; reweighted by exp(gamma W_1 - gamma^2 / 2) it is N(gamma, 1)."""
    rng = np.random.default_rng(seed)
    w = rng.standard_normal(n)
    z = girsanov_weights(w[:, None], gamma, 1.0)
    edges = np.linspace(-4, 5, 37)
    hp = np.histogram(w, bins=edges)[0] / (n * np.diff(edges))
    hq = np.histogram(w, bins=edges, weights=z)[0] / (n * np.diff(edges))
    mids = 0.5 * (edges[1:] + edges[:-1])
    return {"mids": mids, "p": hp, "q": hq, "mean_q": float(np.mean(z * w)), "mean_z": float(z.mean())}


def first_passage_with_drift(b: float, mu: float, sigma: float, T: float) -> float:
    """P(min_{t<=T} (mu t + sigma W_t) <= b), b < 0, derived by removing the drift (exercise)."""
    s = sigma * math.sqrt(T)
    return Phi((b - mu * T) / s) + math.exp(2 * mu * b / sigma**2) * Phi((b + mu * T) / s)


def problem() -> dict:
    cf = caplet_closed_form()
    q = mc_risk_neutral(20_000, seed=11)
    f = mc_forward(20_000, seed=12)
    ratio = q["se"] / f["se"]
    fine = mc_risk_neutral(20_000, steps_per_year=208, seed=11)
    m, v = forward_measure_moments()
    fwd_rate = (float(zcb(R0, T1)) / float(zcb(R0, T1 + DELTA)) - 1) / DELTA
    return {"p1": float(zcb(R0, T1)), "p2": float(zcb(R0, T1 + DELTA)), "fwd": fwd_rate, "closed": cf,
            "q_price": q["price"], "q_se": q["se"], "f_price": f["price"], "f_se": f["se"], "se_ratio": ratio,
            "paths_equiv": ratio**2, "normals_q": q["normals"], "fine_price": fine["price"], "fine_se": fine["se"],
            "m_Q": expected_short_rate(T1), "m_T": m, "sd_T": math.sqrt(v),
            "f0T": forward_rate(T1), "convexity_30y": expected_short_rate(30) - forward_rate(30)}
