"""Extensions of the inventory framework (One Quant Book 11, chapter 4).

In the chapter 3 model (A = 140, k = 1.5, sigma = 2 per unit time; firm.invmm): (1) the long-horizon depths from the
Perron eigenvector against the Gaussian closed form; (2) two assets whose mids are correlated 0.8, quoted with a joint
penalty phi q' cov q or asset by asset (the correlation ignored), over a range of phi, on common random numbers;
(3) a known drift of the mid, quoted with and without the drift in the control problem; (4) a permanent move of the
mid against the market maker after each of its fills, quoted without adjustment, with half the move added to each depth
(the optimum of the penalised problem) and with the whole move.
"""
from __future__ import annotations

import functools
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
for dep in ("invmm", "multimm"):
    sys.path.insert(0, str(ROOT / "firm" / dep))
import firm_invmm as inv  # noqa: E402
import firm_multimm as mm  # noqa: E402

A, K, SIGMA = 140.0, 1.5, 2.0
QMAX = 20


def closed_form_error(phis=(0.5, 5.0, 50.0), show: int = 10) -> dict:
    """Largest absolute gap between the closed-form and the exact stationary bid depths for |q| <= show."""
    qs = np.arange(-QMAX, QMAX + 1)
    sel = np.abs(qs) <= show
    out = {}
    for phi in phis:
        b, _ = mm.stationary(A, K, phi, QMAX)
        cb, _ = mm.asymptotic(A, K, phi, qs)
        ok = sel & np.isfinite(b)
        out[phi] = float(np.max(np.abs(cb[ok] - b[ok])))
    return out


def depth_rows(phi: float = 0.5, qs=(0, 1, 2, 3)) -> dict:
    """Bid depths at a few inventories: exact stationary, closed form, and the finite-horizon solution at t = 0 for a
    horizon of 1 and of 20."""
    b, _ = mm.stationary(A, K, phi, QMAX)
    cb, _ = mm.asymptotic(A, K, phi, np.array(qs))
    s1 = inv.CJSolution(A, K, phi, 0.0, QMAX, 1.0, 200)
    s20 = inv.CJSolution(A, K, phi, 0.0, QMAX, 20.0, 400)
    return {q: {"stationary": float(b[q + QMAX]), "closed": float(cb[i]), "T1": float(s1.bid[0, q + QMAX]),
                "T20": float(s20.bid[0, q + QMAX])} for i, q in enumerate(qs)}


# --- two correlated assets --------------------------------------------------------------------------------------
RHO = 0.8
COV = SIGMA**2 * np.array([[1.0, RHO], [RHO, 1.0]])
Q2 = 8
PHIS2 = (0.01, 0.02, 0.05, 0.1, 0.2, 0.5)
SIM = {"T": 5.0, "dt": 0.005, "paths": 1000, "seed": 11}


@functools.cache
def two_assets(phi: float, joint: bool) -> dict:
    cov = COV if joint else np.diag(np.diag(COV))
    sol = mm.MultiStationary(A, K, phi, cov, Q2)
    r = mm.simulate_multi(sol.depths, SIM["T"], SIM["dt"], COV, A, K, SIM["paths"], SIM["seed"], Q2)
    return {"mean": float(r["pnl"].mean()), "sd": float(r["pnl"].std()), "risk": float(r["risk"].mean()),
            "fills": float(r["fills"].mean())}


def frontier2() -> dict:
    return {kind: {phi: two_assets(phi, kind == "joint") for phi in PHIS2} for kind in ("joint", "separate")}


def equal_capture() -> dict:
    """At each joint point, the separate policy with the same mean P&L (linear interpolation along the separate
    frontier) and its inventory risk, the time-average of q' cov q."""
    fr = frontier2()
    sm = np.array([fr["separate"][p]["mean"] for p in PHIS2])
    sr = np.array([fr["separate"][p]["risk"] for p in PHIS2])
    o = np.argsort(sm)
    out = {}
    for phi in PHIS2:
        m, rj = fr["joint"][phi]["mean"], fr["joint"][phi]["risk"]
        if sm.min() <= m <= sm.max():
            rs = float(np.interp(m, sm[o], sr[o]))
            out[phi] = {"mean": m, "risk_joint": rj, "risk_separate": rs, "reduction": 1 - rj / rs}
    return out


def cross_skew(phi: float = 0.1, q2s=(-4, 0, 4)) -> dict:
    """Joint policy: asset 1's bid depth against its own inventory, for several inventories of asset 2."""
    sol = mm.MultiStationary(A, K, phi, COV, Q2)
    q1 = np.arange(-6, 7)
    return {"q1": q1, **{q2: sol.depths(np.column_stack([q1, np.full(len(q1), q2)]))[0][:, 0] for q2 in q2s}}


# --- drift and adverse selection -----------------------------------------------------------------------------------
PHI1 = 0.5
MU = 2.0
EPS = 0.3


@functools.cache
def drift_case(adjust: bool) -> dict:
    b, a = mm.stationary(A, K, PHI1, QMAX, mu=MU if adjust else 0.0)

    def policy(t, q):
        j = np.clip(q, -QMAX, QMAX) + QMAX
        return b[j], a[j]

    kw = dict(T=SIM["T"], dt=SIM["dt"], sigma=SIGMA, A=A, k=K, paths=SIM["paths"], seed=SIM["seed"], qmax=QMAX)
    r = _drift_sim(policy, MU, **kw)
    return {"mean": float(r["pnl"].mean()), "sd": float(r["pnl"].std()), "q": float(r["q_mean"].mean())}


def _drift_sim(policy, mu, T, dt, sigma, A, k, paths, seed, qmax):
    """firm.invmm.simulate with a constant drift mu of the mid (same random numbers)."""
    rng = np.random.default_rng(seed)
    n = int(round(T / dt))
    s, x, q, qm = np.zeros(paths), np.zeros(paths), np.zeros(paths, int), np.zeros(paths)
    for i in range(n):
        db, da = policy(i * dt, q)
        ub, ua, z = rng.random(paths), rng.random(paths), rng.standard_normal(paths)
        buy = np.isfinite(db) & (ub < A * np.exp(-k * np.nan_to_num(db)) * dt) & (q < qmax)
        sell = np.isfinite(da) & (ua < A * np.exp(-k * np.nan_to_num(da)) * dt) & (q > -qmax)
        x += np.where(buy, -(s - np.nan_to_num(db)), 0.0) + np.where(sell, s + np.nan_to_num(da), 0.0)
        q += buy.astype(int) - sell.astype(int)
        s += mu * dt + sigma * np.sqrt(dt) * z
        qm += q * dt
    return {"pnl": x + q * s, "q_mean": qm / T}


ADJUSTS = (0.0, EPS / 2, EPS)


@functools.cache
def adverse_case(adjust: float, dt: float = SIM["dt"] / 4) -> dict:
    """Mid moves EPS against the market maker after each of its fills; the policy adds `adjust` to each depth.
    Scored on P&L and on the penalised objective P&L - PHI1 * integral of q^2."""
    b, a = mm.stationary(A, K, PHI1, QMAX, eps=adjust)

    def policy(t, q):
        j = np.clip(q, -QMAX, QMAX) + QMAX
        return b[j], a[j]

    r = inv.simulate(policy, SIM["T"], dt, SIGMA, A, K, SIM["paths"], SIM["seed"], QMAX, jump=EPS)
    return {"mean": float(r["pnl"].mean()), "objective": float((r["pnl"] - PHI1 * r["q2_int"]).mean()),
            "sd": float(r["pnl"].std()), "fills": float(r["fills"].mean())}
