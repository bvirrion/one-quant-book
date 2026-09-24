"""Chapter 4 of Book 6: vanilla rates options on the euro curves of chapter 2. The lognormal smile
implied by a flat normal volatility, caplet stripping from flat cap volatilities, physical and
cash-settled swaptions, and the treasurer's cap of the weekend problem."""
import datetime as dt
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/capfloor"))
sys.path.insert(0, str(ROOT / "code/firm/normalvol"))
sys.path.insert(0, str(ROOT / "code/rates-credit-risk/02-multi-curve-and-collateral-discounting/python"))
import rc_multicurve as mc  # noqa: E402
from firm_capfloor import (  # noqa: E402
    Cap,
    cap_price,
    cap_vega,
    caplets,
    cash_annuity,
    forward_swap,
    piecewise,
    strip_caplet_vols,
    swaption_cash_irr,
    swaption_physical,
)
from firm_normalvol import bachelier, black, normal_to_black  # noqa: E402

SPOT = mc.SPOT
DISC = mc.discount()
PROJ = mc.projection(DISC)
CAP_YEARS = [1, 2, 3, 4, 5, 7, 10]
CAP_VOLS = [0.0058, 0.0066, 0.0072, 0.0075, 0.0076, 0.0075, 0.0072]     # flat normal vols, strike 3%, illustrative
CAP_STRIKE = 0.03


def smile_from_flat_normal(f: float = 0.025, t: float = 5.0, vol_n: float = 0.0080) -> list[tuple[float, float]]:
    """Black (lognormal) implied volatility, in per cent, of options priced with one normal vol."""
    return [(k / 1e4, 100 * normal_to_black(f, k / 1e4, t, vol_n)) for k in range(50, 501, 10)]


def stripped():
    return strip_caplet_vols(SPOT, CAP_YEARS, CAP_VOLS, CAP_STRIKE, PROJ, DISC)


def strip_table() -> list[tuple[float, float, float]]:
    """(fixing time, stripped caplet vol bp, flat vol bp of the shortest cap containing it)."""
    knots = stripped()
    f = piecewise(knots)
    rows = []
    for c in caplets(Cap(SPOT, 10, CAP_STRIKE), PROJ, DISC):
        flat = next(v for m, v in zip(CAP_YEARS, CAP_VOLS, strict=True) if c["end"] <= m + 0.01)
        rows.append((c["t"], 1e4 * f(c["t"]), 1e4 * flat))
    return rows


# ---- swaptions ---------------------------------------------------------------------------------------
def swaption_table(vol: float = 0.0080) -> dict:
    """A 5y-into-10y payer at the money: physical versus the par-yield cash formula."""
    ex = dt.date(2031, 9, 29)
    s, a = forward_swap(PROJ, DISC, ex, 10)
    phys = swaption_physical(ex, 10, s, PROJ, DISC, vol, notional=1e8)
    cash = swaption_cash_irr(ex, 10, s, PROJ, DISC, vol, notional=1e8)
    return {"fwd": s, "annuity": a, "cash_annuity_x_df": DISC.df(ex) * cash_annuity(s, 10),
            "physical": phys, "cash": cash, "lognormal_vol": normal_to_black(s, s, DISC.t(ex), vol)}


# ---- the treasurer's cap -------------------------------------------------------------------------------
LOAN = 200e6


def treasurer_cap(strike: float = 0.03, years: int = 5) -> dict:
    cap = Cap(SPOT, years, strike)
    vol = piecewise(stripped())
    prem = cap_price(cap, PROJ, DISC, vol, notional=LOAN)
    vega = cap_vega(cap, PROJ, DISC, vol, notional=LOAN) * 1e-4
    cl = caplets(cap, PROJ, DISC)
    ann = sum(c["delta"] * c["df"] for c in cl)
    flat5 = CAP_VOLS[CAP_YEARS.index(years)]
    return {"premium": prem, "premium_pct": 100 * prem / LOAN, "running_bp": 1e4 * prem / (LOAN * ann),
            "vega_per_bp": vega, "annuity": ann, "n": len(cl),
            "flat_check": cap_price(cap, PROJ, DISC, flat5, notional=LOAN),
            "fwd_avg": sum(c["fwd"] * c["delta"] * c["df"] for c in cl) / ann,
            "intrinsic": LOAN * sum(max(c["fwd"] - strike, 0.0) * c["delta"] * c["df"] for c in cl),
            "lognormal": cap_price(cap, PROJ, DISC, 0.25, model="lognormal", notional=LOAN)}


def cap_strike_table() -> list[tuple[float, float, float]]:
    """(strike %, premium as % of notional, running bp) of a five-year cap."""
    out = []
    for k in range(200, 451, 25):
        r = treasurer_cap(k / 1e4)
        out.append((k / 100, r["premium_pct"], r["running_bp"]))
    return out


__all__ = ["bachelier", "black"]
