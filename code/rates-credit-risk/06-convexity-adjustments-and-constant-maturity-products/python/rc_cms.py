"""Chapter 6 of Book 6: convexity adjustments and constant-maturity products, on chapter 2's euro
curves and chapter 5's synthetic cube. Timing adjustments, CMS rates by replication (flat smile
and cube smile), CMS caplets, a quanto adjustment, and the steepener note of the weekend problem
(correlation of 2y and 10y moves estimated on chapter 3's Treasury data)."""
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for p in ("code/firm/cms", "code/firm/multicurve",
          "code/rates-credit-risk/05-sabr-in-rates-and-the-volatility-cube/python",
          "code/rates-credit-risk/03-rates-risk/python"):
    sys.path.insert(0, str(ROOT / p))
import rc_sabrcube as sc  # noqa: E402
from firm_cms import (  # noqa: E402
    cms_caplet,
    cms_rate,
    cms_rate_hagan,
    cms_spread_option,
    linear_tsr,
    otm_integral,
    quanto_adjustment_normal,
    spread_vol,
    timing_adjustment_black,
    timing_adjustment_normal,
)
from firm_multicurve import add_months, annuity  # noqa: E402

DISC, PROJ = sc.DISC, sc.PROJ
SPOT = sc.mc.SPOT
CUBE, _ = sc.build_cube()
LO = -sc.SHIFT + 0.0010          # the cube is shifted SABR at 3%: no mass below -3%


def setup(expiry: float, tenor: int = 10) -> dict:
    """Forward swap rate, annuity, payment discount factor (one year after expiry) and accruals."""
    ex = add_months(SPOT, int(round(12 * expiry)))
    pay = add_months(ex, 12)
    fwd = sc.forward(expiry, tenor)
    dates = [add_months(ex, 12 * k) for k in range(tenor + 1)]
    return {"fwd": fwd, "t": DISC.t(ex), "annuity": annuity(DISC, ex, tenor), "df_pay": DISC.df(pay),
            "accruals": [(b - a).days / 360 for a, b in zip(dates, dates[1:], strict=False)]}


def smile(expiry: float, tenor: int = 10):
    return lambda k: CUBE.normal_vol(expiry, tenor, k)


def cms_table(tenor: int = 10) -> list[tuple[float, float, float, float]]:
    """(expiry, forward %, CMS adjustment with flat ATM vol bp, with the cube's smile bp)."""
    out = []
    for e in (1.0, 2.0, 3.0, 5.0, 7.0, 10.0):
        s = setup(e, tenor)
        sm = smile(e, tenor)
        flat = cms_rate_hagan(s["fwd"], s["t"], sm(s["fwd"]), s["annuity"], s["df_pay"], s["accruals"])
        full = cms_rate(s["fwd"], s["t"], s["annuity"], s["df_pay"], s["accruals"], sm, LO)
        out.append((e, 100 * s["fwd"], 1e4 * (flat - s["fwd"]), 1e4 * (full - s["fwd"])))
    return out


def replication_contributions(expiry: float = 10.0, tenor: int = 10) -> list[tuple[float, float]]:
    """Contribution density, by strike, of out-of-the-money swaptions to the CMS adjustment (bp per %)."""
    s = setup(expiry, tenor)
    sm = smile(expiry, tenor)
    a0, a1 = linear_tsr(s["annuity"], s["df_pay"], s["fwd"], s["accruals"])
    from firm_cms import bachelier_call, bachelier_put
    rows = []
    for x in range(-290, 701, 10):
        k = x * 1e-4
        v = bachelier_put(s["fwd"], k, s["t"], sm(k)) if k < s["fwd"] else bachelier_call(s["fwd"], k, s["t"], sm(k))
        rows.append((100 * k, 1e4 * 2 * a1 * v / (a0 + a1 * s["fwd"]) * 1e-2))
    return rows


def timing_example() -> dict:
    """A six-month Euribor forward of 3% fixing in 5 years, paid at fixing instead of at the end."""
    return {"black": timing_adjustment_black(0.03, 0.5, 5.0, 0.25),
            "normal": timing_adjustment_normal(0.03, 0.5, 5.0, 0.0075)}


def quanto_example() -> float:
    """A euro rate paid in dollars: normal vol 75 bp, EURUSD vol 8%, correlation 0.3, 5 years."""
    return quanto_adjustment_normal(0.0075, 0.08, 0.3, 5.0)


# ---- the steepener note --------------------------------------------------------------------------------
def treasury_corr_2_10() -> float:
    import rc_ratesrisk as rr
    _, ch = rr.treasury_changes()
    return float(np.corrcoef(ch[:, 1], ch[:, 5])[0, 1])


def steepener(rho: float | None = None, years: int = 10, fixed: float = 0.02) -> dict:
    """Coupon each year k = 1..years: participation * max(S10(k) - S2(k), 0), paid at k + 1.
    Fair participation: the coupon leg worth as much as a fixed 2% coupon leg on the same dates."""
    rho = treasury_corr_2_10() if rho is None else rho
    legs, fixed_leg = [], 0.0
    for k in range(1, years + 1):
        e = float(k)
        s10, s2 = setup(e, 10), setup(e, 2)
        c10 = cms_rate(s10["fwd"], s10["t"], s10["annuity"], s10["df_pay"], s10["accruals"], smile(e, 10), LO)
        c2 = cms_rate(s2["fwd"], s2["t"], s2["annuity"], s2["df_pay"], s2["accruals"], smile(e, 2), LO)
        v10, v2 = smile(e, 10)(s10["fwd"]), smile(e, 2)(s2["fwd"])
        legs.append(cms_spread_option(c10, c2, 0.0, s10["t"], v10, v2, rho, s10["df_pay"]))
        fixed_leg += fixed * s10["df_pay"]
    value = sum(legs)
    return {"rho": rho, "unit_leg": value, "fixed_leg": fixed_leg, "participation": fixed_leg / value,
            "first_spread_vol": spread_vol(smile(1.0, 10)(setup(1.0, 10)["fwd"]),
                                           smile(1.0, 2)(setup(1.0, 2)["fwd"]), rho)}


__all__ = ["cms_caplet", "otm_integral"]
