"""Caps, floors and swaptions on the multi-curve (build of One Quant Book 6, chapter 4).

Caplets are forward-looking (an interbank index fixed at the start of its period, paid at the end),
priced by Black or Bachelier on the forward from the projection curve, discounted on the discount
curve; the market convention of skipping the first (already fixed) caplet is the default. Flat cap
volatilities are stripped into piecewise-constant caplet volatilities. Swaptions are priced
physically settled on the multi-curve annuity, or cash-settled with the cash (par-yield) annuity.
Uses Book 2's `firm_normalvol` (imported, never edited). Rates and volatilities are decimals.
"""
import datetime as dt
import pathlib
import sys
from collections.abc import Callable
from dataclasses import dataclass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "normalvol"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "multicurve"))
from firm_multicurve import add_months, annuity, float_leg, simple_forward  # noqa: E402
from firm_normalvol import bachelier, black, normal_vega  # noqa: E402

PRICERS = {"normal": bachelier, "lognormal": black}


@dataclass(frozen=True)
class Cap:
    start: dt.date
    years: int
    strike: float
    months: int = 6
    floor: bool = False
    skip_first: bool = True


def caplets(cap: Cap, proj, disc) -> list[dict]:
    """One dict per caplet: fixing time, forward, accrual, discount factor of the payment."""
    n = 12 * cap.years // cap.months
    out = []
    for k in range(1 if cap.skip_first else 0, n):
        s, e = add_months(cap.start, k * cap.months), add_months(cap.start, (k + 1) * cap.months)
        out.append({"t": disc.t(s), "fwd": simple_forward(proj, s, e), "delta": (e - s).days / 360,
                    "df": disc.df(e), "end": disc.t(e)})
    return out


def _vol_at(vol, t: float) -> float:
    return vol(t) if callable(vol) else vol


def cap_price(cap: Cap, proj, disc, vol: float | Callable[[float], float], model: str = "normal",
              notional: float = 1.0) -> float:
    """Sum of caplet (or floorlet) prices; `vol` is one flat volatility or a function of fixing time."""
    price = PRICERS[model]
    return notional * sum(price(c["fwd"], cap.strike, c["t"], _vol_at(vol, c["t"]), c["delta"] * c["df"],
                                payer=not cap.floor) for c in caplets(cap, proj, disc))


def cap_vega(cap: Cap, proj, disc, vol, notional: float = 1.0) -> float:
    """Normal vega: value change per unit of normal volatility (divide by 1e4 for one basis point)."""
    return notional * sum(normal_vega(c["fwd"], cap.strike, c["t"], _vol_at(vol, c["t"]), c["delta"] * c["df"])
                          for c in caplets(cap, proj, disc))


def strip_caplet_vols(start: dt.date, maturities: list[int], flat_vols: list[float], strike: float, proj, disc,
                      model: str = "normal", months: int = 6) -> list[tuple[float, float]]:
    """Piecewise-constant caplet volatilities, one level per interval between cap maturities, such
    that every cap reprices at its flat volatility. Returns (last fixing time of the interval, vol)."""
    knots: list[tuple[float, float]] = []

    def stripped(t: float) -> float:
        for tk, v in knots:
            if t <= tk + 1e-9:
                return v
        return knots[-1][1]
    for m, fv in zip(maturities, flat_vols, strict=True):
        cap = Cap(start, m, strike, months)
        target = cap_price(cap, proj, disc, fv, model)
        last_fix = caplets(cap, proj, disc)[-1]["t"]
        lo, hi = 1e-6, 5.0 if model == "lognormal" else 0.05
        for _ in range(100):
            mid = 0.5 * (lo + hi)
            knots.append((last_fix, mid))
            p = cap_price(cap, proj, disc, stripped, model)
            knots.pop()
            lo, hi = (mid, hi) if p < target else (lo, mid)
        knots.append((last_fix, 0.5 * (lo + hi)))
    return knots


def piecewise(knots: list[tuple[float, float]]) -> Callable[[float], float]:
    def f(t: float) -> float:
        for tk, v in knots:
            if t <= tk + 1e-9:
                return v
        return knots[-1][1]
    return f


def forward_swap(proj, disc, expiry: dt.date, tenor: int, months: int = 6) -> tuple[float, float]:
    """Forward par rate and annuity (annual ACT/360 fixed leg) of the swap starting at expiry."""
    a = annuity(disc, expiry, tenor)
    return float_leg(proj, disc, expiry, tenor, months) / a, a


def swaption_physical(expiry: dt.date, tenor: int, strike: float, proj, disc, vol: float, model: str = "normal",
                      payer: bool = True, notional: float = 1.0) -> float:
    s, a = forward_swap(proj, disc, expiry, tenor)
    return notional * PRICERS[model](s, strike, disc.t(expiry), vol, a, payer)


def cash_annuity(rate: float, tenor: int, freq: int = 1) -> float:
    """Annuity of a swap discounted at its own rate (par-yield, or IRR, method)."""
    return sum((1.0 / freq) / (1.0 + rate / freq) ** i for i in range(1, tenor * freq + 1))


def swaption_cash_irr(expiry: dt.date, tenor: int, strike: float, proj, disc, vol: float, model: str = "normal",
                      payer: bool = True, notional: float = 1.0) -> float:
    """The traditional market formula for a par-yield cash-settled swaption: discount to expiry,
    times the cash annuity at the forward rate, times the option on the rate."""
    s, _ = forward_swap(proj, disc, expiry, tenor)
    t = disc.t(expiry)
    return notional * disc.df(expiry) * cash_annuity(s, tenor) * PRICERS[model](s, strike, t, vol, 1.0, payer)
