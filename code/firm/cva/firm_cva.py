"""Credit and debit valuation adjustments (build of One Quant Book 6, chapter 18).

From discounted exposure profiles (chapter 17's `firm_exposure`) and hazard curves (chapter 13's
`firm_cdscurve`):
  CVA = (1 - R_C) sum_k DEE(t_k) [Q_C(t_{k-1}) - Q_C(t_k)],   DEE = E[D(0,t) max(V_t - C_t, 0)],
  DVA = (1 - R_B) sum_k DNE(t_k) [Q_B(t_{k-1}) - Q_B(t_k)],   DNE = E[D(0,t) max(C_t - V_t, 0)],
unilateral (each party alone can default) or first-to-default (bilateral: the counterparty's default counts
only if the bank has survived, weight Q_B(t_k), and vice versa), independence of exposure and credit.
Pathwise CVA with a stochastic hazard gives wrong-way risk. CS01 by bumping the quoted par spreads and
re-bootstrapping. Deflators from the Hull-White scenarios discount path by path.
"""
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parents[1]
for comp in ("cdscurve", "exposure"):
    sys.path.insert(0, str(HERE / comp))
from firm_cdscurve import HazardCurve, bootstrap  # noqa: E402


def deflators(sc) -> np.ndarray:
    """D(0, t_k) on every path: exp(-sum r dt) with r = f(0, t) + x_t on the scenario grid."""
    t = sc.times
    dt = np.diff(t)
    f0 = np.array([-np.log(sc.market.usd.df_t(t[j + 1]) / sc.market.usd.df_t(t[j])) / dt[j] for j in range(len(dt))])
    r = f0[None, :] + sc.x[:, :-1]
    return np.concatenate([np.ones((sc.x.shape[0], 1)), np.exp(-np.cumsum(r * dt[None, :], axis=1))], axis=1)


def discounted_profiles(E: np.ndarray, D: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(discounted EE, discounted negative exposure as a positive number) per grid date."""
    return (D * np.maximum(E, 0.0)).mean(axis=0), (D * np.maximum(-E, 0.0)).mean(axis=0)


def _default_probs(curve: HazardCurve, times: np.ndarray) -> np.ndarray:
    q = np.array([curve.survival(float(t)) for t in times])
    return q[:-1] - q[1:], q


def cva(dee: np.ndarray, times: np.ndarray, cpty: HazardCurve, recovery: float = 0.4,
        own: HazardCurve | None = None) -> float:
    """Unilateral CVA, or first-to-default CVA if the bank's own curve is given. EE at period midpoints."""
    dq, _ = _default_probs(cpty, times)
    mid = 0.5 * (dee[1:] + dee[:-1])
    w = np.ones_like(dq) if own is None else np.array([own.survival(float(t)) for t in times[1:]])
    return float((1.0 - recovery) * np.sum(mid * dq * w))


def dva(dne: np.ndarray, times: np.ndarray, own: HazardCurve, recovery: float = 0.4,
        cpty: HazardCurve | None = None) -> float:
    return cva(dne, times, own, recovery, cpty)


def cva_pathwise(E: np.ndarray, D: np.ndarray, times: np.ndarray, hazards: np.ndarray,
                 recovery: float = 0.4) -> float:
    """CVA with a hazard rate simulated on each path (paths x times), default time on the grid."""
    dt = np.diff(times)
    cum = np.concatenate([np.zeros((E.shape[0], 1)), np.cumsum(hazards[:, :-1] * dt[None, :], axis=1)], axis=1)
    q = np.exp(-cum)
    dq = q[:, :-1] - q[:, 1:]
    loss = D * np.maximum(E, 0.0)
    mid = 0.5 * (loss[:, 1:] + loss[:, :-1])
    return float((1.0 - recovery) * (mid * dq).sum(axis=1).mean())


def cs01_buckets(dee: np.ndarray, times: np.ndarray, disc, tenors, spreads, recovery: float = 0.4,
                 bump: float = 1e-4) -> list[float]:
    """Change in CVA for a one-basis-point rise in each quoted counterparty par spread (re-bootstrapped)."""
    base = cva(dee, times, bootstrap(disc, tenors, spreads, recovery), recovery)
    out = []
    for i in range(len(spreads)):
        s = [x + (bump if j == i else 0.0) for j, x in enumerate(spreads)]
        out.append(cva(dee, times, bootstrap(disc, tenors, s, recovery), recovery) - base)
    return out


def running_spread(adjustment: float, notional: float, risky_annuity: float) -> float:
    """An upfront adjustment as a running spread on a notional (per year)."""
    return adjustment / (notional * risky_annuity)
