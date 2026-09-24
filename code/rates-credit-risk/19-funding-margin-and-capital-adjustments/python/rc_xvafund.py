"""Chapter 19 of Book 6: funding, margin and capital adjustments of chapter 17's ten-year USD 100m swap
(the bank receives fixed) with chapter 18's BBB counterparty and single-A bank. Funding at 80 bp over the
overnight rate; SA-CCR exposure at default and the reduced basic CVA capital along the swap's life (an
illustrative 100% risk weight and an 8% capital ratio for counterparty credit capital, 3% CVA risk weight for
an investment-grade industrial, 10% hurdle rate); initial margin by Book 2's sensitivity model."""
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for p in ("code/firm/xvafund", "code/firm/cva", "code/firm/exposure",
          "code/rates-credit-risk/18-credit-and-debit-valuation-adjustments/python"):
    sys.path.insert(0, str(ROOT / p))
import rc_cva as cv  # noqa: E402
from firm_cva import cva, discounted_profiles, dva  # noqa: E402
from firm_exposure import collateral, exposure  # noqa: E402
from firm_xvafund import (  # noqa: E402
    IrTrade,
    ba_cva_capital,
    effective_maturity,
    fba,
    fca,
    im_profile,
    ir_addon,
    kva,
    mva,
    sa_ccr_ead,
    scva,
    supervisory_duration,
)

S_F = 0.0080            # bank's funding spread over the overnight rate
RW_CCR, CAP_RATIO, RW_CVA, HURDLE = 1.00, 0.08, 0.03, 0.10
NOTIONAL = 100e6
R = cv.R


def _setup(csa: bool = False, lag: int = 1):
    """Exposure of the swap: for default (collateral one margin period of risk old, lag 1) or for funding
    (collateral as of today, lag 0)."""
    d = cv.data()
    V = cv.ex.values()["swap"]
    E = exposure(V, collateral(V, 0.0, 0.5e6), lag) if csa else exposure(V)
    E, D, t = E[:, :-1], d["D"][:, :-1], d["t"][:-1]
    dee, dne = discounted_profiles(E, D)
    ee = np.maximum(E, 0.0).mean(axis=0)
    surv = np.array([d["cpty"].survival(float(x)) * d["own"].survival(float(x)) for x in t])
    return d, t, dee, dne, ee, surv


def swap_rate() -> float:
    return cv.ex.trades()[0].fixed


def annuity() -> float:
    return sum(cv.DISC.df_t(float(k)) for k in range(1, 11))


def adjustments(csa: bool = False, with_im: bool = False) -> dict:
    d, t, dee, dne, ee, surv = _setup(csa)
    _, _, fee, fne, _, _ = _setup(csa, lag=0)
    out = {"cva": cva(dee, t, d["cpty"], R, own=d["own"]), "dva": dva(dne, t, d["own"], R, cpty=d["cpty"]),
           "fca": fca(fee, t, S_F, surv), "fba": fba(fne, t, S_F, surv)}
    out["fva"] = out["fca"] - out["fba"]
    out["mva"] = mva(NOTIONAL, 10, swap_rate(), S_F) if with_im else 0.0
    cap = capital_profile(csa)
    disc = np.array([cv.DISC.df_t(float(x)) for x in cap["t"]])
    s = np.array([d["cpty"].survival(float(x)) * d["own"].survival(float(x)) for x in cap["t"]])
    out["kva"] = kva(cap["total"], cap["t"], HURDLE, disc, s)
    out["total"] = out["cva"] - out["dva"] + out["fva"] + out["mva"] + out["kva"]
    out["bp"] = 1e4 * out["total"] / (NOTIONAL * annuity())
    return out


def capital_profile(csa: bool = False, step: float = 0.25) -> dict:
    """Counterparty credit capital and CVA capital at each date, with RC = EE(t) (expected replacement cost)."""
    _, t, _, _, ee, _ = _setup(csa)
    ts = np.arange(0.0, 10.0, step)
    rows = {"t": ts, "ead": [], "ccr": [], "cva": []}
    for x in ts:
        k = int(np.searchsorted(t, x - 1e-9))
        m = 10.0 - x
        trade = IrTrade("USD", NOTIONAL, 0.0, m, -1.0, m)
        addon = ir_addon([trade], 10 if csa else None)
        e = sa_ccr_ead(float(ee[k]), addon, th=0.0 if csa else None, mta=0.5e6 if csa else 0.0)
        rows["ead"].append(e)
        rows["ccr"].append(CAP_RATIO * RW_CCR * e)
        rows["cva"].append(ba_cva_capital([scva(RW_CVA, effective_maturity(m), e)]))
    for k in ("ead", "ccr", "cva"):
        rows[k] = np.array(rows[k])
    rows["total"] = rows["ccr"] + rows["cva"]
    return rows


def ead_today() -> dict:
    trade = IrTrade("USD", NOTIONAL, 0.0, 10.0, -1.0, 10.0)
    a = ir_addon([trade])
    return {"sd": supervisory_duration(0.0, 10.0), "addon": a, "ead": sa_ccr_ead(0.0, a),
            "addon_csa": ir_addon([trade], 10), "ead_csa": sa_ccr_ead(0.0, ir_addon([trade], 10), th=0.0, mta=0.5e6)}


def im_today() -> float:
    return im_profile(NOTIONAL, 10, swap_rate())[0][1]


def funding_sensitivity(spreads_bp=(0, 20, 40, 60, 80, 100, 120)) -> list[tuple[float, float, float]]:
    """(funding spread bp, FCA uncollateralised, FCA under the CSA) in USD thousands."""
    out = []
    for s in spreads_bp:
        vals = []
        for c in (False, True):
            _, t, fee, _, _, surv = _setup(c, lag=0)
            vals.append(fca(fee, t, s * 1e-4, surv) / 1e3)
        out.append((s, *vals))
    return out


def stack_table() -> list[tuple[str, float, float]]:
    a, b = adjustments(), adjustments(csa=True, with_im=True)
    return [(k, a[k], b[k]) for k in ("cva", "dva", "fca", "fba", "mva", "kva", "total")]


def running_equivalent(x: float) -> float:
    return 1e4 * x / (NOTIONAL * annuity())


def dv01() -> float:
    return NOTIONAL * annuity() * 1e-4


def half_life() -> float:
    return math.log(2) / 0.05
