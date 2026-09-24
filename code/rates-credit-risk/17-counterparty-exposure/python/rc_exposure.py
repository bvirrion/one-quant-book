"""Chapter 17 of Book 6: counterparty exposure. Chapter 1's SOFR curve (USD, Hull-White kappa 3%,
sigma 90 bp) and chapter 2's ESTR curve (EUR, deterministic), EURUSD at 1.10 with 8% volatility; a ten-year
USD swap and a ten-year EUR/USD cross-currency swap with one counterparty, simulated fortnightly (one
step = ten business days = the margin period of risk); profiles uncollateralised and under a CSA;
wrong-way risk through a counterparty whose hazard rises when the euro falls; and a corporate's
swap-plus-forward netting set before and after it signs a CSA."""
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for p in ("code/firm/exposure", "code/rates-credit-risk/01-curve-construction/python",
          "code/rates-credit-risk/02-multi-curve-and-collateral-discounting/python"):
    sys.path.insert(0, str(ROOT / p))
import rc_curves  # noqa: E402
import rc_multicurve  # noqa: E402
from firm_exposure import (  # noqa: E402
    FxForward,
    Market,
    Swap,
    XccySwap,
    aggregate,
    conditional_ee,
    epe,
    exposure,
    profiles,
    simulate,
    usd_par_rate,
)

USD = rc_curves.curves()["monotone_convex"].curve
EUR = rc_multicurve.discount()
MKT = Market(USD, EUR, kappa=0.03, sigma=0.0090, fx0=1.10, fx_vol=0.08)
STEPS, PATHS, HORIZON = 26, 4000, 10.0


def eur_par_rate(maturity: int) -> float:
    return (1.0 - EUR.df_t(maturity)) / sum(EUR.df_t(float(T)) for T in range(1, maturity + 1))


_SC = {}


def scenarios(horizon: float = HORIZON):
    if horizon not in _SC:
        _SC[horizon] = simulate(MKT, horizon, STEPS, PATHS, seed=21)
    return _SC[horizon]


def trades():
    k_usd, k_eur = usd_par_rate(USD, 10), eur_par_rate(10)
    swap = Swap(100e6, k_usd, 10, receive_fixed=True)
    xccy = XccySwap(110e6, 100e6, k_usd, k_eur, 10)
    return swap, xccy


_V = {}


def values():
    if not _V:
        sc = scenarios()
        swap, xccy = trades()
        _V["swap"], _V["xccy"] = swap.values(sc), xccy.values(sc)
    return _V


def summary(p: dict, times) -> dict:
    return {"peak_pfe": float(p["pfe"].max()), "peak_ee": float(p["ee"].max()),
            "t_peak_pfe": float(times[int(p["pfe"].argmax())]), "epe_life": epe(p["ee"], times, float(times[-1])),
            "epe_1y": epe(p["ee"], times, 1.0)}


def _live(p: dict) -> dict:
    """Drop the final grid date: every trade has matured and the collateral is returned."""
    return {k: v[:-1] for k, v in p.items()}


def profile_set() -> dict:
    v, t = values(), scenarios().times[:-1]
    out = {"swap": aggregate([v["swap"]]), "xccy": aggregate([v["xccy"]]),
           "net": aggregate([v["swap"], v["xccy"]]),
           "csa10": aggregate([v["swap"], v["xccy"]], threshold=0.0, mta=0.5e6, lag=1),
           "csa20": aggregate([v["swap"], v["xccy"]], threshold=0.0, mta=0.5e6, lag=2),
           "csa_th": aggregate([v["swap"], v["xccy"]], threshold=10e6, mta=0.5e6, lag=1)}
    return {k: (_live(p), summary(_live(p), t)) for k, p in out.items()}


def wrong_way(b: float = 5.0, lam0: float = 0.02) -> dict:
    """Hazard lam0 (X_t / F_X(0,t))^(-b): the counterparty weakens when the euro falls, which is when the
    cross-currency swap (receive USD, pay EUR) is in the money to the bank."""
    sc, v = scenarios(), values()
    t = sc.times
    fwd = MKT.fx0 * np.array([EUR.df_t(x) / USD.df_t(x) for x in t])
    lam = lam0 * (sc.fx / fwd) ** (-b)
    dt = t[1] - t[0]
    cum = np.cumsum(lam * dt, axis=1) - lam * dt
    dens = lam * np.exp(-cum)
    E = exposure(v["xccy"])
    ee = profiles(E)["ee"]
    cee = conditional_ee(E, dens)
    k = int(np.argmax(ee))
    return {"ee": ee, "cee": cee, "t": t, "ratio_peak": float(cee[k] / ee[k]), "t_peak": float(t[k]),
            "ratio_avg": float(cee[1:].mean() / ee[1:].mean())}


def corporate(csa: str = "none") -> dict:
    """Five-year USD 50m swap (bank receives fixed) plus a one-year forward: the bank sells EUR 20m."""
    sc = scenarios(5.0)
    swap = Swap(50e6, usd_par_rate(USD, 5), 5, receive_fixed=True)
    k_fx = MKT.fx0 * EUR.df_t(1.0) / USD.df_t(1.0)
    fwd = FxForward(20e6, k_fx, 1.0)
    vals = [swap.values(sc), -fwd.values(sc)]
    kw = {"none": {}, "zero": {"threshold": 0.0, "mta": 0.25e6, "lag": 1},
          "th5": {"threshold": 5e6, "mta": 0.25e6, "lag": 1}}[csa]
    p = _live(aggregate(vals, **kw))
    t = sc.times[:-1]
    return {"profile": p, **summary(p, t), "epe_life": epe(p["ee"], t, 5.0), "k_fx": k_fx,
            "k_swap": usd_par_rate(USD, 5)}


def par_rates():
    return usd_par_rate(USD, 10), eur_par_rate(10), usd_par_rate(USD, 5)


def time0_values():
    v = values()
    return float(v["swap"][:, 0].mean()), float(v["xccy"][:, 0].mean())


def fx_martingale(k: int = 130) -> float:
    sc = scenarios()
    t = sc.times[k]
    return float(sc.fx[:, k].mean() / (MKT.fx0 * EUR.df_t(t) / USD.df_t(t)))


def mpor_sqrt_rule() -> float:
    return math.sqrt(2.0)
