"""Bermudan swaptions and callable bonds (build of One Quant Book 6, chapter 9).

On chapter 7's Hull-White model (`firm_shortrate`, imported, never edited):
- backward induction on the trinomial tree for Bermudan swaptions and callable zero-coupon bonds;
- regression Monte Carlo (Longstaff-Schwartz) under the terminal forward measure, with the regression
  fitted on one set of paths and the exercise policy applied to an independent set (a lower bound);
- the switch option (Bermudan minus the most expensive co-terminal European).
Swaps have annual unit accruals in model time; the Bermudan receiver may be exercised at each
integer year e in `exercises` into the swap from e to `final`.
"""
import math
import pathlib
import sys
from collections.abc import Sequence

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "shortrate"))
from firm_shortrate import B, HullWhite, HWTree  # noqa: E402


def _swap_values_on_tree(tree: HWTree, it: int, final_step: int, per: int, K: float) -> np.ndarray:
    """Value at step it (per unit notional) of receiving K annually and paying floating until final_step."""
    n = (final_step - it) // per
    bonds = [tree.zero_bonds_at(it, it + per * i) for i in range(1, n + 1)]
    return K * sum(bonds) - (1.0 - bonds[-1])


def bermudan_tree(tree: HWTree, exercises: Sequence[int], final: int, K: float, receiver: bool = True) -> float:
    """Bermudan swaption by backward induction: exercise at year e into the swap from e to final."""
    per = int(round(1.0 / tree.dt))
    final_step = final * per
    ex_steps = {e * per: e for e in exercises}
    v = np.zeros(2 * tree.jmax + 1)
    for i in range(max(ex_steps), -1, -1):
        if i in ex_steps:
            sw = _swap_values_on_tree(tree, i, final_step, per, K)
            v = np.maximum(v, sw if receiver else -sw)
        if i > 0:
            v = tree.step_back(v, i - 1)
    return float(v[tree.jmax])


def exercise_boundary(tree: HWTree, exercises: Sequence[int], final: int, K: float) -> list[tuple[int, float]]:
    """Receiver Bermudan: at each exercise year, the highest short rate at which exercising beats holding."""
    per = int(round(1.0 / tree.dt))
    final_step = final * per
    ex_steps = {e * per: e for e in exercises}
    v = np.zeros(2 * tree.jmax + 1)
    out = []
    for i in range(max(ex_steps), -1, -1):
        if i in ex_steps:
            sw = _swap_values_on_tree(tree, i, final_step, per, K)
            live = np.abs(tree.js) <= tree.width[i]
            ex = live & (sw > v) & (sw > 0)
            if ex.any():
                out.append((ex_steps[i], float(tree.rates(i)[ex].max())))
            v = np.maximum(v, sw)
        if i > 0:
            v = tree.step_back(v, i - 1)
    return sorted(out)


def callable_zero_tree(tree: HWTree, maturity: int, accretion: float, calls: Sequence[int]) -> dict[str, float]:
    """A zero-coupon bond paying (1 + accretion)^maturity at maturity, callable by the issuer at year c
    at its accreted value (1 + accretion)^c. Returns straight, callable and the issuer's option (per unit)."""
    per = int(round(1.0 / tree.dt))
    n = maturity * per
    call_steps = {c * per: (1 + accretion) ** c for c in calls}
    v = np.full(2 * tree.jmax + 1, (1 + accretion) ** maturity)
    straight = v.copy()
    for i in range(n - 1, -1, -1):
        v, straight = tree.step_back(v, i), tree.step_back(straight, i)
        if i in call_steps:
            v = np.minimum(v, call_steps[i])
    return {"straight": float(straight[tree.jmax]), "callable": float(v[tree.jmax]),
            "option": float(straight[tree.jmax] - v[tree.jmax])}


# ---- regression Monte Carlo -----------------------------------------------------------------------------
def simulate_x(m: HullWhite, final: float, times: Sequence[float], paths: int, dt: float = 1 / 24, seed: int = 9):
    """x_t at the requested times under the terminal forward measure Q^{final} (Euler steps with antithetics):
    dx = (y(t) - kappa x - sigma(t)^2 B(t, final)) dt + sigma(t) dW."""
    rng = np.random.default_rng(seed)
    half = paths // 2
    x = np.zeros(2 * half)
    out, t, targets = {}, 0.0, sorted(times)
    k = 0
    while k < len(targets):
        h = min(dt, targets[k] - t)
        if h > 1e-12:
            s = m.sigmas[min(sum(1 for kn in m.knots if kn <= t), len(m.sigmas) - 1)]
            z = rng.standard_normal(half)
            z = np.concatenate([z, -z])
            x = x + (m.y(t) - m.kappa * x - s * s * B(m.kappa, final - t)) * h + s * math.sqrt(h) * z
            t += h
        if abs(t - targets[k]) < 1e-12:
            out[targets[k]] = x.copy()
            k += 1
    return out


def _swap_value_x(m: HullWhite, e: float, final: int, K: float, x: np.ndarray) -> np.ndarray:
    yt = m.y(e)
    bonds = [m.P0(e + i) / m.P0(e) * np.exp(-B(m.kappa, i) * x - 0.5 * B(m.kappa, i) ** 2 * yt)
             for i in range(1, int(final - e) + 1)]
    return K * sum(bonds) - (1.0 - bonds[-1])


def _numeraire_x(m: HullWhite, e: float, final: int, x: np.ndarray) -> np.ndarray:
    tau = final - e
    return m.P0(final) / m.P0(e) * np.exp(-B(m.kappa, tau) * x - 0.5 * B(m.kappa, tau) ** 2 * m.y(e))


def bermudan_lsm(m: HullWhite, exercises: Sequence[int], final: int, K: float, paths: int = 40000,
                 seed: int = 9) -> tuple[float, float]:
    """Longstaff-Schwartz lower bound: regression on one path set, pricing on an independent one.
    Returns (price, standard error). Basis: 1, swap value, swap value squared (in numeraire units)."""
    times = [float(e) for e in exercises]

    def run(seed_, coefs=None):
        xs = simulate_x(m, float(final), times, paths, seed=seed_)
        cf = np.zeros(paths)                                   # deflated cash flow of the policy
        fitted = {}
        for e in sorted(exercises, reverse=True):
            x = xs[float(e)]
            ex = _swap_value_x(m, e, final, K, x) / _numeraire_x(m, e, final, x)
            itm = ex > 0
            if e == max(exercises):
                cf = np.where(itm, ex, 0.0)
                continue
            basis = np.column_stack([np.ones(itm.sum()), ex[itm], ex[itm] ** 2])
            if coefs is None:
                beta, *_ = np.linalg.lstsq(basis, cf[itm], rcond=None)
                fitted[e] = beta
            else:
                beta = coefs[e]
            cont = basis @ beta
            exercise_now = np.zeros(paths, bool)
            exercise_now[np.flatnonzero(itm)[ex[itm] > cont]] = True
            cf = np.where(exercise_now, ex, cf)
        return cf, fitted
    _, coefs = run(seed)
    cf, _ = run(seed + 1, coefs)
    val = m.P0(final) * cf
    return float(val.mean()), float(val.std(ddof=1) / math.sqrt(paths))


def switch_option(bermudan: float, europeans: Sequence[float]) -> float:
    return bermudan - max(europeans)
