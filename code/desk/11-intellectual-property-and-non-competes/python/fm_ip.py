"""One Quant Book 16, chapter 11: what garden leave protects (illustrative, $ millions a year).

A strategy earns 20 a year. A departing researcher could take one of three things to a competitor: the model's
structure (a competitor using it would take 30 per cent of the remaining profits; the edge it describes decays with a
half-life of 24 months), its parameters (60 per cent, half-life 6 months) or its data pipeline (20 per cent, 12
months). The half-lives are estimated from noisy monthly edge series with firm.decay. Garden leave costs 1.5 a year
(salary and benefits); discount rate 8 per cent.
"""
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/gardenleave"))
import firm_gardenleave as gl  # noqa: E402

P, R, S = 20.0, 0.08, 1.5
CASES = {"structure": (0.30, 24.0), "parameters": (0.60, 6.0), "data": (0.20, 12.0)}
LENGTHS = (0.25, 0.5, 1.0)


def edge_series(true_hl_months, seed, months=48):
    rng = np.random.default_rng(seed)
    m = np.arange(1, months + 1)
    return m, 0.5 ** (m / true_hl_months) + 0.05 * rng.standard_normal(months)


def estimates(seed=11):
    out = {}
    for k, (L, hl) in CASES.items():
        m, e = edge_series(hl, seed + int(hl))
        est, _ = gl.half_life_from_series(m, e)
        out[k] = {"L": L, "hl_true": hl, "hl_est": est, "lam": math.log(2) / (est / 12)}
    return out


def table(seed=11):
    rows = {}
    for k, e in estimates(seed).items():
        rows[k] = {"hl_est": e["hl_est"], "best_years": gl.best_length(P, e["L"], e["lam"], S),
                   "protected": {T: gl.protected(P, e["L"], e["lam"], R, T) for T in LENGTHS},
                   "net": {T: gl.net(P, e["L"], e["lam"], R, S, T) for T in LENGTHS},
                   "loss_no_leave": gl.loss_if_start(P, e["L"], e["lam"], R, 0.0)}
    return rows


def curves(seed=11, tmax=3.0):
    t = np.round(np.arange(0.0, tmax + 1e-9, 0.125), 3)
    est = estimates(seed)
    return t, {k: np.array([gl.protected(P, e["L"], e["lam"], R, x) for x in t]) for k, e in est.items()}, \
        np.array([gl.leave_cost(S, R, x) for x in t])
