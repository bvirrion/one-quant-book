"""Chapter 2 of Book 6: multi-curve and collateral discounting. An illustrative euro market (an
ESTR OIS discount curve and a six-month Euribor projection curve), the tenor basis, the value of
an off-market swap under three discountings, a collateral-choice CSA in dollars, and the 27 July
2020 switch from EONIA to ESTR discounting at a clearing house."""
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/multicurve"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/curvebuild"))
from firm_curvebuild import Swap, calibrate  # noqa: E402
from firm_multicurve import (  # noqa: E402
    CollateralChoiceCurve,
    Fixing,
    IborSwap,
    ShiftedCurve,
    add_months,
    calibrate_projection,
    ibor_swap_pv,
    simple_forward,
    tenor_basis,
)

SPOT = dt.date(2026, 9, 29)
YEARS = [1, 2, 3, 5, 7, 10, 15, 20, 30]
OIS = [0.0195, 0.0202, 0.0210, 0.0225, 0.0240, 0.0255, 0.0270, 0.0272, 0.0260]       # ESTR OIS, illustrative
IRS = [0.0215, 0.0221, 0.0228, 0.0242, 0.0256, 0.0270, 0.0284, 0.0285, 0.0272]       # vs 6M Euribor, illustrative
FIX6M = 0.0213                                                                       # 6M Euribor fixing


def discount():
    return calibrate(SPOT, [Swap(SPOT, n, r, f"{n}Y") for n, r in zip(YEARS, OIS, strict=True)],
                     "monotone_convex").curve


def projection(disc=None):
    disc = disc or discount()
    ins = [Fixing(SPOT, add_months(SPOT, 6), FIX6M, "6M")] + [
        IborSwap(SPOT, n, r, 6, f"{n}Y") for n, r in zip(YEARS, IRS, strict=True)]
    return calibrate_projection(SPOT, disc, ins)


def single_curve():
    """The pre-2007 practice: one curve from the Euribor swaps, projecting and discounting."""
    return calibrate(SPOT, [Swap(SPOT, n, r, f"{n}Y") for n, r in zip(YEARS, IRS, strict=True)],
                     "monotone_convex").curve


def forward_table(step: float = 0.25) -> list[tuple[float, float, float, float]]:
    """(start years, 6M Euribor forward %, 6M OIS forward %, difference bp) on six-month periods."""
    disc, proj = discount(), projection()
    out = []
    for k in range(0, int(29.5 / step) + 1):
        s = SPOT + dt.timedelta(days=round(365 * k * step))
        e = add_months(s, 6)
        fp, fd = simple_forward(proj, s, e), simple_forward(disc, s, e)
        out.append((k * step, 100 * fp, 100 * fd, 1e4 * (fp - fd)))
    return out


def basis_table() -> list[tuple[int, float]]:
    disc, proj = discount(), projection(discount())
    return [(n, 1e4 * tenor_basis(proj, disc, SPOT, n)) for n in YEARS]


def discounting_comparison(fixed: float = 0.035, years: int = 10, notional: float = 1e8) -> dict[str, float]:
    """A receiver of 3.5% on EUR 100 million for ten years against 6M Euribor, on three set-ups."""
    disc, proj, single = discount(), projection(), single_curve()
    return {"ois": ibor_swap_pv(proj, disc, SPOT, years, fixed, notional, payer=False),
            "single": ibor_swap_pv(single, single, SPOT, years, fixed, notional, payer=False),
            "par_multi": IborSwap(SPOT, years, 0.0).model(proj, disc),
            "par_single": IborSwap(SPOT, years, 0.0).model(single, single)}


# ---- collateral choice (a dollar trade whose CSA also accepts euro cash) --------------------------
USD_YEARS = [1, 2, 3, 5, 7, 10]
SOFR = [0.0360, 0.0340, 0.0335, 0.0343, 0.0357, 0.0375]                              # illustrative


def xccy_basis(t: float) -> float:
    """Illustrative EURUSD basis for lending euros against dollars: -15 bp at the front rising
    linearly to +5 bp at ten years (flat after). Posting euros earns SOFR - b in dollar terms."""
    return (-15.0 + 20.0 * min(t, 10.0) / 10.0) * 1e-4


def usd_discount():
    return calibrate(SPOT, [Swap(SPOT, n, r, f"{n}Y") for n, r in zip(USD_YEARS, SOFR, strict=True)],
                     "monotone_convex").curve


def collateral_choice(years: float = 10.0, amount: float = 1e8) -> dict[str, float]:
    """PV of a single USD payment in `years` under a USD-only CSA and under a USD-or-EUR CSA."""
    base = usd_discount()
    choice = CollateralChoiceCurve(base, [lambda t: 0.0, lambda t: -xccy_basis(t)])
    return {"usd_only": amount * base.df_t(years), "choice": amount * choice.df_t(years)}


def collateral_table(step: float = 0.1) -> list[tuple[float, float, float, float]]:
    base = usd_discount()
    out = []
    for k in range(1, int(10.0 / step) + 1):
        t = k * step
        f = base.fwd_t(t)
        out.append((t, 100 * f, 100 * (f - xccy_basis(t)), 100 * max(f, f - xccy_basis(t))))
    return out


# ---- the discounting switch of 27 July 2020 (EONIA = ESTR + 8.5 bp -> ESTR flat) -----------------
SWITCH = dt.date(2020, 7, 27)
OIS_2020 = [-0.0050, -0.0050, -0.0049, -0.0045, -0.0038, -0.0027, -0.0012, -0.0005, -0.0008]   # ESTR, illustrative
IRS_2020 = [-0.0033, -0.0033, -0.0032, -0.0029, -0.0022, -0.0012, 0.0002, 0.0008, 0.0004]      # vs 6M, illustrative
FIX6M_2020 = -0.0033
EONIA_SPREAD = 0.00085


def curves_2020():
    estr = calibrate(SWITCH, [Swap(SWITCH, n, r, f"{n}Y") for n, r in zip(YEARS, OIS_2020, strict=True)],
                     "monotone_convex").curve
    eonia = ShiftedCurve(estr, EONIA_SPREAD)
    ins = [Fixing(SWITCH, add_months(SWITCH, 6), FIX6M_2020, "6M")] + [
        IborSwap(SWITCH, n, r, 6, f"{n}Y") for n, r in zip(YEARS, IRS_2020, strict=True)]
    return estr, eonia, calibrate_projection(SWITCH, estr, ins)


def switch_value(years: int, fixed: float, notional: float, payer: bool = False) -> dict[str, float]:
    """Value of a cleared swap before (EONIA discounting) and after (ESTR flat), by the clearing
    house's constant-forward method: the cash flows projected under the EONIA regime are held
    fixed and only the discount factors change. Compensation = before - after, paid by the gainer."""
    estr, eonia, _ = curves_2020()
    ins = [Fixing(SWITCH, add_months(SWITCH, 6), FIX6M_2020, "6M")] + [
        IborSwap(SWITCH, n, r, 6, f"{n}Y") for n, r in zip(YEARS, IRS_2020, strict=True)]
    proj = calibrate_projection(SWITCH, eonia, ins)
    before = ibor_swap_pv(proj, eonia, SWITCH, years, fixed, notional, payer=payer)
    after = ibor_swap_pv(proj, estr, SWITCH, years, fixed, notional, payer=payer)
    return {"before": before, "after": after, "change": after - before, "compensation": before - after}


def switch_table(fixed: float = 0.015, notional: float = 1e8) -> list[tuple[int, float, float]]:
    out = []
    for n in (2, 3, 5, 7, 10, 15, 20, 30):
        v = switch_value(n, fixed, notional)
        out.append((n, v["before"] / 1e6, v["change"] / 1e3))
    return out
