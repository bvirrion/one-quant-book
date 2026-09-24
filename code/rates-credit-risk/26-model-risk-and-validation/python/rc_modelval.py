"""Chapter 26 of Book 6: model risk and validation. A validation of chapter 7's Hull-White trinomial tree
against the closed-form (Jamshidian) swaption price over a parameter grid, with tolerances and failures;
an inventory of the firm's Book 6 models with the tiering rule; and the averaging error of 2012 replayed
on an illustrative synthetic-credit book (a sold equity tranche hedged with index protection, large-pool
model), where the relative changes of the hazard rate and of the correlation are divided by the sum of
old and new values instead of their average."""
import functools
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for p in ("code/firm/modelval", "code/firm/shortrate", "code/firm/tranche", "code/firm/varmodel",
          "code/rates-credit-risk/01-curve-construction/python"):
    sys.path.insert(0, str(ROOT / p))
import rc_curves  # noqa: E402
from firm_modelval import (  # noqa: E402
    ModelRecord,
    benchmark,
    binomial_tail,
    inventory_summary,
    relative_change,
    summary,
)
from firm_shortrate import HullWhite, HWTree  # noqa: E402
from firm_tranche import expected_tranche_loss  # noqa: E402
from firm_varmodel import hs_var_es  # noqa: E402

CURVE = rc_curves.curves()["monotone_convex"].curve
GRID = {"kappa": [0.01, 0.05, 0.20], "sigma": [0.006, 0.012], "expiry": [1, 5, 10], "tenor": [5, 10],
        "moneyness": [-0.01, 0.0, 0.01], "dt": [0.25, 1 / 12]}
ABS_TOL, REL_TOL = 5e-5, 0.01             # half a basis point of notional, or 1%


@functools.cache
def _tree(kappa: float, sigma: float, horizon: int, dt: float) -> HWTree:
    return HWTree(CURVE, kappa, sigma, horizon, dt)


def strike(expiry: int, tenor: int, moneyness: float) -> float:
    ann = sum(CURVE.df_t(expiry + i) for i in range(1, tenor + 1))
    return (CURVE.df_t(expiry) - CURVE.df_t(expiry + tenor)) / ann + moneyness


def tree_price(kappa, sigma, expiry, tenor, moneyness, dt):
    return _tree(kappa, sigma, expiry + tenor, dt).european_swaption(expiry, tenor, strike(expiry, tenor, moneyness))


def closed_price(kappa, sigma, expiry, tenor, moneyness, dt):
    return HullWhite(CURVE, kappa, [sigma]).swaption(expiry, tenor, strike(expiry, tenor, moneyness))


@functools.lru_cache(maxsize=1)
def validation() -> dict:
    res = benchmark(tree_price, closed_price, GRID, ABS_TOL, REL_TOL)
    s = summary(res)
    by_dt = {dt: summary([r for r in res if r.params["dt"] == dt]) for dt in GRID["dt"]}
    return {"results": res, "summary": s, "by_dt": by_dt}


def inventory() -> list[ModelRecord]:
    return [ModelRecord("B6-01", "curve construction", "rates quant", "pricing, risk, capital", 3, 2, 1),
            ModelRecord("B6-05", "SABR swaption cube", "rates quant", "pricing, reserves", 3, 3, 2,
                        limitations=["shifted lognormal wings unreliable far out of the money"]),
            ModelRecord("B6-09", "Bermudan tree and regression", "rates quant", "pricing", 2, 3, 2),
            ModelRecord("B6-12", "mortgage prepayment and OAS", "MBS desk", "pricing, hedging", 2, 3, 3,
                        limitations=["behavioural parameters calibrated on one rate cycle"]),
            ModelRecord("B6-17", "exposure simulation", "XVA quant", "CVA, limits, capital", 3, 3, 2),
            ModelRecord("B6-21", "VaR model", "market risk", "limits, capital", 3, 2, 2),
            ModelRecord("B6-24", "deposit behaviour", "treasury", "IRRBB, FTP", 3, 2, 3,
                        limitations=["betas estimated in low-rate years"]),
            ModelRecord("B6-25", "initial-margin forecast", "treasury", "liquidity planning", 1, 2, 2)]


# ---- the averaging error ---------------------------------------------------------------------------------
LAM0, RHO0, REC, N_EQ = 0.010, 0.20, 0.40, 1e9


def history(days: int = 260, seed: int = 12):
    """Illustrative daily history of an index hazard rate and a tranche correlation (lognormal moves)."""
    rng = np.random.default_rng(seed)
    lam = LAM0 * np.exp(np.cumsum(0.04 * rng.standard_normal(days)))
    rho = RHO0 * np.exp(np.cumsum(0.03 * rng.standard_normal(days)))
    return lam, np.clip(rho, 0.02, 0.95)


def el(lam: float, rho: float, a: float, d: float) -> float:
    return expected_tranche_loss(a, d, 1.0 - math.exp(-5.0 * lam), rho, REC, n=401)


def hedge_ratio() -> float:
    """Index notional (bought protection) per unit of sold equity-tranche notional, from the hazard delta."""
    h = 1e-5
    de = (el(LAM0 + h, RHO0, 0.0, 0.03) - el(LAM0 - h, RHO0, 0.0, 0.03)) / (2 * h)
    di = (el(LAM0 + h, RHO0, 0.0, 1.0) - el(LAM0 - h, RHO0, 0.0, 1.0)) / (2 * h)
    return de / di


def book_pnl(lam: float, rho: float) -> float:
    """Seller of EUR 1bn equity protection, buyer of index protection at the hedge ratio: P&L of a move."""
    k = hedge_ratio()
    eq = -N_EQ * (el(lam, rho, 0.0, 0.03) - el(LAM0, RHO0, 0.0, 0.03))
    ix = k * N_EQ * (el(lam, rho, 0.0, 1.0) - el(LAM0, RHO0, 0.0, 1.0))
    return eq + ix


@functools.lru_cache(maxsize=1)
def averaging_error() -> dict:
    lam, rho = history()
    out = {}
    for label, err in (("intended", False), ("error", True)):
        rl = np.array([relative_change(lam[t], lam[t - 1], err) for t in range(1, len(lam))])
        rr = np.array([relative_change(rho[t], rho[t - 1], err) for t in range(1, len(rho))])
        pnl = np.array([book_pnl(LAM0 * (1 + a), RHO0 * (1 + b)) for a, b in zip(rl, rr, strict=True)])
        out[label] = {"var": hs_var_es(pnl, 0.99)[0], "vol_l": float(rl.std()), "vol_r": float(rr.std()),
                      "pnl": pnl}
    out["ratio"] = out["error"]["var"] / out["intended"]["var"]
    out["hedge"] = hedge_ratio()
    return out


def exceptions_pvalue(n: int = 250, k: int = 8) -> float:
    return binomial_tail(n, k, 0.01)


def tiers() -> dict:
    return inventory_summary(inventory())


def errors_by_expiry():
    v = validation()["results"]
    rows = []
    for e in GRID["expiry"]:
        row = [e]
        for dt in GRID["dt"]:
            sel = [r for r in v if r.params["expiry"] == e and r.params["dt"] == dt]
            row += [1e4 * max(r.abs_err for r in sel), sum(not r.passed for r in sel)]
        rows.append(tuple(row))
    return rows


def one_year_fine(dt: float = 1 / 24) -> dict:
    grid = {k: v for k, v in GRID.items()}
    grid["expiry"], grid["dt"] = [1], [dt]
    return summary(benchmark(tree_price, closed_price, grid, ABS_TOL, REL_TOL))
