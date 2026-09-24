"""Book 4, chapter 15: robust statistics and heavy tails (teaching module).

Daily EUR/USD returns from the ECB reference rates, 1999-2026: robust scale against one bad print, the
Hill estimator and a peaks-over-threshold fit, and the one-in-a-thousand-days loss under three models.
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "robust"))
sys.path.insert(0, str(ROOT / "code" / "firm" / "estim"))
from firm_estim import minimize  # noqa: E402
from firm_robust import (  # noqa: E402
    gpd_fit,
    gpd_quantile,
    hill,
    huber_location,
    kendall_tau,
    mad,
    qn_scale,
    spearman,
    tail_dependence,
)

DATA = ROOT / "data" / "methods" / "eur_fx_ecb_1999_2026.csv"
BAD_DATE = "2026-03-24"          # the day whose print is corrupted in the examples
BAD_PRINT = 1.5172               # true reference rate 1.1572, first two decimals swapped
P_TAIL = 0.999                   # one-in-a-thousand-days loss
U_SHARE = 0.05                   # peaks over the 95% quantile of losses


def load(bad: bool = False) -> dict:
    d = np.genfromtxt(DATA, delimiter=",", names=True, dtype=None, encoding=None)
    dates = np.array(d["date"], dtype=str)
    usd = np.array(d["usd_per_eur"], dtype=float)
    if bad:
        usd = usd.copy()
        usd[np.flatnonzero(dates == BAD_DATE)[0]] = BAD_PRINT
    jpy = np.array(d["jpy_per_eur"], dtype=float)
    gbp = np.array(d["gbp_per_eur"], dtype=float)
    return {"dates": dates, "usd": usd, "jpy": jpy, "gbp": gbp,
            "r_usd": 100 * np.diff(np.log(usd)), "r_jpy": 100 * np.diff(np.log(jpy)),
            "r_gbp": 100 * np.diff(np.log(gbp))}


def scale_table(bad: bool, window: int = 250) -> dict:
    """Standard deviation, MAD and Qn of the last `window` daily returns (percent)."""
    r = load(bad)["r_usd"][-window:]
    return {"sd": float(r.std(ddof=1)), "mad": mad(r), "qn": qn_scale(r), "mean": float(r.mean()),
            "huber": huber_location(r), "median": float(np.median(r))}


def sensitivity(errors=None, window: int = 250) -> list[tuple[float, float, float, float]]:
    """Scale estimates of the last `window` returns when the bad day's log price is shifted by e (as a fraction)."""
    errors = np.linspace(0.0, 0.3, 31) if errors is None else errors
    base = load(False)
    lp = np.log(base["usd"])
    k = int(np.flatnonzero(base["dates"] == BAD_DATE)[0])
    out = []
    for e in errors:
        q = lp.copy()
        q[k] += e
        r = 100 * np.diff(q)[-window:]
        out.append((float(e), float(r.std(ddof=1)), mad(r), qn_scale(r)))
    return out


# --- tail models for daily losses (percent) -----------------------------------------------------------

def student_t_fit(x) -> dict:
    """Location-scale Student t by maximum likelihood (log scale, log(df - 2) parameterisation)."""
    x = np.asarray(x, dtype=float)

    def nll(th):
        mu, ls, lnu = th
        s, nu = math.exp(ls), 2 + math.exp(lnu)
        z = (x - mu) / s
        c = math.lgamma((nu + 1) / 2) - math.lgamma(nu / 2) - 0.5 * math.log(nu * math.pi) - ls
        return -float(np.sum(c - (nu + 1) / 2 * np.log1p(z * z / nu)))
    th, _ = minimize(nll, [float(np.median(x)), math.log(mad(x)), math.log(2.0)])
    return {"mu": float(th[0]), "scale": math.exp(th[1]), "df": 2 + math.exp(th[2])}


def t_quantile(p: float, df: float, n: int = 400_000, seed: int = 11) -> float:
    """Quantile of the standard Student t by simulation (no closed form without special functions)."""
    return float(np.quantile(np.random.default_rng(seed).standard_t(df, n), p))


def _norm_ppf(p: float) -> float:
    lo, hi = -10.0, 10.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if 0.5 * math.erfc(-mid / math.sqrt(2)) < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def tail_quantiles(bad: bool = False, p: float = P_TAIL, u_share: float = U_SHARE) -> dict:
    """The p-quantile of daily losses (percent) under a normal, a Student t and a GPD-over-threshold fit."""
    r = load(bad)["r_usd"]
    loss = -r
    n = loss.size
    q_norm = float(loss.mean() + loss.std(ddof=1) * _norm_ppf(p))
    t = student_t_fit(loss)
    q_t = t["mu"] + t["scale"] * t_quantile(p, t["df"])
    u = float(np.quantile(loss, 1 - u_share))
    exc = loss[loss > u] - u
    xi, beta = gpd_fit(exc)
    q_gpd = gpd_quantile(u, xi, beta, exc.size / n, p)
    emp = float(np.quantile(loss, p))
    return {"normal": q_norm, "t": float(q_t), "gpd": q_gpd, "empirical": emp, "df": t["df"], "t_scale": t["scale"],
            "xi": xi, "beta": beta, "u": u, "n_exc": int(exc.size), "n": n, "sd": float(loss.std(ddof=1)),
            "n_beyond_normal": int(np.sum(loss > q_norm)), "n_beyond_gpd": int(np.sum(loss > q_gpd))}


def hill_curve(ks=range(20, 701, 10), bad: bool = False, side: str = "loss") -> list[tuple[int, float, float]]:
    r = load(bad)["r_usd"]
    x = -r if side == "loss" else r
    return [(k, *hill(x, k)) for k in ks]


def dependence() -> dict:
    d = load(False)
    a, b = d["r_usd"], d["r_gbp"]
    rho = float(np.corrcoef(a, b)[0, 1])
    return {"pearson": rho, "spearman": spearman(a, b), "kendall": kendall_tau(a, b),
            "spearman_gauss": 6 / math.pi * math.asin(rho / 2), "kendall_gauss": 2 / math.pi * math.asin(rho),
            "tail_05": tail_dependence(a, b, 0.05), "tail_01": tail_dependence(a, b, 0.01),
            "n": int(a.size)}


def gaussian_tail_dependence(rho: float, q: float, n: int = 2_000_000, seed: int = 4) -> float:
    rng = np.random.default_rng(seed)
    z1 = rng.standard_normal(n)
    z2 = rho * z1 + math.sqrt(1 - rho * rho) * rng.standard_normal(n)
    c = _norm_ppf(q)
    return float(np.sum((z1 <= c) & (z2 <= c)) / np.sum(z1 <= c))
