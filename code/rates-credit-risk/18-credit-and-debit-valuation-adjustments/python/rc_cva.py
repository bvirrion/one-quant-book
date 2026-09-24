"""Chapter 18 of Book 6: CVA and DVA of chapter 17's netting set (a ten-year USD swap and a ten-year
EUR/USD cross-currency swap). An illustrative BBB counterparty and a single-A bank on chapter 1's SOFR
curve; unilateral and first-to-default adjustments, uncollateralised and under a CSA; bucketed CS01;
wrong-way CVA as the counterparty's hazard is tied more strongly to the euro; and the DVA gain a bank
books when its own spread widens."""
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for p in ("code/firm/cva", "code/firm/cdscurve", "code/firm/exposure",
          "code/rates-credit-risk/17-counterparty-exposure/python"):
    sys.path.insert(0, str(ROOT / p))
import rc_exposure as ex  # noqa: E402
from firm_cdscurve import bootstrap, legs  # noqa: E402
from firm_cva import cs01_buckets, cva, cva_pathwise, deflators, discounted_profiles, dva, running_spread  # noqa: E402
from firm_exposure import collateral, exposure  # noqa: E402

DISC = ex.USD
TENORS = [1.0, 2.0, 3.0, 5.0, 7.0, 10.0]
CPTY = [0.0080, 0.0095, 0.0110, 0.0140, 0.0160, 0.0175]      # BBB counterparty, illustrative
OWN = [0.0040, 0.0048, 0.0055, 0.0070, 0.0080, 0.0090]       # single-A bank, illustrative
R = 0.40

_C = {}


def data():
    if not _C:
        sc = ex.scenarios()
        v = ex.values()
        V = v["swap"] + v["xccy"]
        D = deflators(sc)
        t = sc.times
        _C.update(sc=sc, V=V, D=D, t=t, E=exposure(V), Ecsa=exposure(V, collateral(V, 0.0, 0.5e6), 1),
                  Ex=exposure(v["xccy"]), cpty=bootstrap(DISC, TENORS, CPTY, R), own=bootstrap(DISC, TENORS, OWN, R))
    return _C


def adjustments(csa: bool = False) -> dict:
    d = data()
    E = d["Ecsa"] if csa else d["E"]
    E = E[:, :-1]
    t = d["t"][:-1]
    dee, dne = discounted_profiles(E, d["D"][:, :-1])
    out = {"cva": cva(dee, t, d["cpty"], R), "dva": dva(dne, t, d["own"], R),
           "cva_bil": cva(dee, t, d["cpty"], R, own=d["own"]), "dva_bil": dva(dne, t, d["own"], R, cpty=d["cpty"])}
    out["bcva"] = out["cva_bil"] - out["dva_bil"]
    out["dee"], out["dne"], out["t"] = dee, dne, t
    return out


def cs01() -> list[float]:
    a = adjustments()
    return cs01_buckets(a["dee"], a["t"], DISC, TENORS, CPTY, R)


def annuity10(spreads=CPTY) -> float:
    return legs(bootstrap(DISC, TENORS, spreads, R), DISC, 10.0, R)[0]


def running_bp() -> float:
    return 1e4 * running_spread(adjustments()["cva"], 100e6, annuity10())


def wrong_way(bs=(0.0, 2.0, 5.0, 10.0)) -> list[tuple[float, float]]:
    """CVA of the cross-currency swap with hazard lam(t) (X_t / F_X(0,t))^(-b), lam(t) the counterparty's
    bootstrapped hazard, renormalised so that the unconditional survival curve is kept (on average)."""
    d = data()
    sc, t = d["sc"], d["t"][:-1]
    fwd = ex.MKT.fx0 * np.array([ex.EUR.df_t(x) / ex.USD.df_t(x) for x in t])
    base = np.array([d["cpty"].hazards[min(np.searchsorted(d["cpty"].times, x, side="left"), 5)] for x in t])
    out = []
    for b in bs:
        m = (sc.fx[:, :-1] / fwd) ** (-b)
        lam = base[None, :] * m / m.mean(axis=0)
        out.append((b, cva_pathwise(d["Ex"][:, :-1], d["D"][:, :-1], t, lam, R)))
    return out


def dva_shift(shifts_bp=(0, 10, 20, 30, 40, 50, 75, 100)) -> list[tuple[float, float]]:
    """Unilateral DVA of the netting set as the bank's own spreads widen in parallel."""
    a = adjustments()
    return [(s, dva(a["dne"], a["t"], bootstrap(DISC, TENORS, [x + s * 1e-4 for x in OWN], R), R)) for s in shifts_bp]


def contributions() -> list[tuple[float, float]]:
    """CVA contribution per year of default time (USD million)."""
    a, d = adjustments(), data()
    t = a["t"]
    q = np.array([d["cpty"].survival(float(x)) for x in t])
    mid = 0.5 * (a["dee"][1:] + a["dee"][:-1])
    c = (1 - R) * mid * (q[:-1] - q[1:])
    years = np.floor(t[1:] - 1e-9).astype(int)
    return [(y + 0.5, float(c[years == y].sum() / 1e6)) for y in range(10)]
