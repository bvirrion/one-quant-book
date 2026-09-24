"""Chapter 13 of Book 6: reduced-form credit. An illustrative investment-grade name's CDS curve on
chapter 1's SOFR discount curve: hazard bootstrap, the credit triangle, standard-coupon upfront,
bucketed CS01 and jump-to-default of a protection position, and a negative-basis package (a bond
bought below its CDS-implied value, hedged with protection)."""
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
for p in ("code/firm/cdscurve", "code/rates-credit-risk/01-curve-construction/python"):
    sys.path.insert(0, str(ROOT / p))
import rc_curves as rc  # noqa: E402
from firm_cdscurve import (  # noqa: E402
    HazardCurve,
    bootstrap,
    bucketed_cs01,
    cds_value,
    jump_to_default,
    legs,
    par_spread,
    risky_bond,
    standard_upfront,
)

DISC = rc.curves()["monotone_convex"].curve
TENORS = [1.0, 2.0, 3.0, 5.0, 7.0, 10.0]
SPREADS = [0.0060, 0.0075, 0.0090, 0.0120, 0.0135, 0.0150]      # illustrative par CDS spreads
R = 0.40


def curve() -> HazardCurve:
    return bootstrap(DISC, TENORS, SPREADS, R)


def hazard_table():
    c = curve()
    return [(T, 100 * h, 100 * s / (1 - R), 100 * (1 - c.survival(T))) for T, h, s in
            zip(TENORS, c.hazards, SPREADS, strict=True)]


def zero_rate(T: float) -> float:
    return -math.log(DISC.df_t(T)) / T


def upfront_5y() -> float:
    return standard_upfront(5.0, 0.0120, 0.0100, zero_rate(5.0), R)


def protection_position(notional: float = 10e6):
    """Long five-year protection at the 100 bp standard coupon."""
    c = curve()
    mtm = notional * cds_value(c, DISC, 5.0, 0.0100, R)
    cs01 = bucketed_cs01(DISC, TENORS, SPREADS, R, lambda cv: notional * cds_value(cv, DISC, 5.0, 0.0100, R))
    return {"mtm": mtm, "cs01": cs01, "jtd": jump_to_default(mtm, notional, R, True),
            "annuity": legs(c, DISC, 5.0, R)[0]}


# ---- the negative-basis package ---------------------------------------------------------------------------
BOND_COUPON, BOND_PRICE = 0.05, 0.970


def implied_flat_spread(price: float, coupon: float = BOND_COUPON, maturity: float = 5.0) -> float:
    """Par CDS spread of the flat hazard at which the bond is worth `price` (a bond-implied CDS spread)."""
    lo, hi = 0.0, 1.0
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        v = risky_bond(HazardCurve([maturity], [mid]), DISC, maturity, coupon, R)
        lo, hi = (mid, hi) if v > price else (lo, mid)
    return par_spread(HazardCurve([maturity], [0.5 * (lo + hi)]), DISC, maturity, R)


def basis_package(face: float = 100e6, recovery: float = R) -> dict:
    c = curve()
    model = risky_bond(c, DISC, 5.0, BOND_COUPON, R)
    cds_mtm_unit = cds_value(c, DISC, 5.0, 0.0100, R)
    out = {"model_price": model, "bond_spread": implied_flat_spread(BOND_PRICE), "cds_spread": SPREADS[3]}
    out["basis_bp"] = 1e4 * (out["cds_spread"] - out["bond_spread"])
    for label, n in (("par", face), ("mv", face * BOND_PRICE)):
        jtd = face * (recovery - BOND_PRICE) + n * (1 - recovery) - n * cds_mtm_unit
        out["jtd_" + label] = jtd
        cs = bucketed_cs01(DISC, TENORS, SPREADS, R,
                           lambda cv, n=n: face * risky_bond(cv, DISC, 5.0, BOND_COUPON, R)
                           + n * cds_value(cv, DISC, 5.0, 0.0100, R))
        out["cs01_" + label] = sum(cs)
    n = face * BOND_PRICE
    # break-even recovery of the market-value hedge: face (R - P) + n (1 - R) - n MtM = 0
    out["be_recovery_mv"] = (face * BOND_PRICE - n + n * cds_mtm_unit) / (face - n)
    return out


def upfront_table() -> list[tuple[float, float, float]]:
    """(quoted spread bp, five-year upfront % at a 100 bp coupon, at a 500 bp coupon)."""
    z = zero_rate(5.0)
    return [(s, 100 * standard_upfront(5.0, s * 1e-4, 0.01, z, R), 100 * standard_upfront(5.0, s * 1e-4, 0.05, z, R))
            for s in range(25, 801, 25)]


def survival_table():
    c = curve()
    return [(t / 4, c.survival(t / 4), c.cum(t / 4 + 1e-9) - c.cum(t / 4)) for t in range(0, 41)]
