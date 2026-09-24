"""Book 4, chapter 20: multivariate series and cointegration (teaching module).

Daily 2-, 5- and 10-year Treasury yields (FRED DGS2, DGS5, DGS10, 1976-2026): a VAR of the changes, Granger
causality, the Engle-Granger and Johansen tests, and the butterfly that cointegration selects.
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "coint"))
from firm_coint import engle_granger, fevd, granger_test, irf, johansen, var_fit, var_stable  # noqa: E402

DATA = ROOT / "data" / "methods" / "ust_2y5y10y_daily_1976_2026.csv"
MAX_P = 10


def load() -> dict:
    d = np.genfromtxt(DATA, delimiter=",", names=True, dtype=None, encoding=None)
    Y = 100 * np.column_stack([d["dgs2"], d["dgs5"], d["dgs10"]]).astype(float)   # basis points
    return {"dates": np.array(d["date"], dtype=str), "Y": np.round(Y, 6)}


def ar1_half_life(x) -> tuple[float, float]:
    x = np.asarray(x, dtype=float)
    X = np.column_stack([np.ones(x.size - 1), x[:-1]])
    rho = float(np.linalg.lstsq(X, x[1:], rcond=None)[0][1])
    return rho, math.log(0.5) / math.log(rho)


def var_analysis() -> dict:
    dY = np.diff(load()["Y"], axis=0)
    aics = [(p, var_fit(dY, p)["aic"]) for p in range(1, MAX_P + 1)]
    p = min(aics, key=lambda t: t[1])[0]
    v = var_fit(dY, p)
    names = ("2y", "5y", "10y")
    gc = {f"{names[c]}->{names[e]}": granger_test(dY, p, c, e) for c in range(3) for e in range(3) if c != e}
    R = irf(v["A"], v["Sigma"], 10)
    return {"p": p, "stable": var_stable(v["A"]), "granger": gc, "fevd10": fevd(v["A"], v["Sigma"], 10),
            "irf": R, "cum_2y_shock": R[:, :, 0].sum(axis=0), "sd": np.sqrt(np.diag(v["Sigma"])),
            "corr": np.corrcoef(v["resid"].T)}


def fly_weights(beta: np.ndarray) -> np.ndarray:
    """Cointegrating vector on (2y, 5y, 10y, 1) normalised so the 5-year weight is -1."""
    return -beta[:3] / beta[1]


def cointegration(start: str = "1976-06-01", end: str = "2099-12-31") -> dict:
    d = load()
    m = (d["dates"] >= start) & (d["dates"] <= end)
    Y = d["Y"][m]
    aics = [(p, var_fit(Y, p)["aic"]) for p in range(1, MAX_P + 1)]
    p = min(aics, key=lambda t: t[1])[0]
    j = johansen(Y, lags=p - 1)
    w = fly_weights(j["beta"][:, 0])
    fly_j = -(Y @ w)
    fly_121 = 2 * Y[:, 1] - Y[:, 0] - Y[:, 2]
    eg = engle_granger(Y[:, 1], Y[:, [0, 2]])
    rank = int(np.sum([j["trace"][r] > j["crit_trace"][r][1] for r in range(3)]))
    return {"p": p, "trace": j["trace"], "maxeig": j["maxeig"], "crit_trace": j["crit_trace"], "rank": rank,
            "weights": w, "eg_tau": eg["tau"], "eg_beta": eg["beta"], "eg_crit": eg["crit"],
            "hl_johansen": ar1_half_life(fly_j), "hl_121": ar1_half_life(fly_121), "fly_j": fly_j, "fly_121": fly_121,
            "sd_fly_j": float(np.std(np.diff(fly_j))), "sd_fly_121": float(np.std(np.diff(fly_121))),
            "n": int(m.sum()), "dates": d["dates"][m]}


def rolling_weights(years: int = 5, step_years: int = 1) -> list[tuple[str, float, float, int]]:
    """Johansen fly weights (2y, 10y) on rolling windows of `years` years, with the rank found at 5%."""
    out = []
    for y0 in range(1977, 2027 - years + 1, step_years):
        c = cointegration(f"{y0}-01-01", f"{y0 + years - 1}-12-31")
        out.append((f"{y0}-{y0 + years - 1}", float(c["weights"][0]), float(c["weights"][2]), c["rank"]))
    return out


def eg_vs_df(T: int = 1000, reps: int = 4000, seed: int = 21) -> dict:
    """Null distributions: Dickey-Fuller tau of one random walk against the Engle-Granger tau of the residual of one
    random walk regressed on two others."""
    sys.path.insert(0, str(ROOT / "code" / "firm" / "tsa"))
    from firm_tsa import adf
    rng = np.random.default_rng(seed)
    df, eg = np.empty(reps), np.empty(reps)
    for i in range(reps):
        W = np.cumsum(rng.standard_normal((T, 3)), axis=0)
        df[i] = adf(W[:, 0], lags=0)["tau"]
        eg[i] = engle_granger(W[:, 0], W[:, 1:])["tau"]
    return {"df": df, "eg": eg, "df5": float(np.quantile(df, 0.05)), "eg5": float(np.quantile(eg, 0.05)),
            "df_reject_at_eg": float(np.mean(eg < np.quantile(df, 0.05)))}
