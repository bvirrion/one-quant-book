"""Chapter 11 of Book 6: inflation derivatives. Illustrative sterling nominal (SONIA) and RPI
zero-coupon swap curves; a Jarrow-Yildirim model with deterministic nominal rates; year-on-year
convexity, year-on-year swap rates and caplets; limited price indexation by simulation; and
monthly seasonality of the forward index from US CPI (Book 2's data file and seasonal factors)."""
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for p in ("code/firm/inflopt", "code/firm/breakeven"):
    sys.path.insert(0, str(ROOT / p))
from firm_breakeven import seasonal_factors  # noqa: E402
from firm_inflopt import JYDet, LogLinearCurve, real_curve  # noqa: E402

YEARS = [1, 2, 3, 5, 7, 10, 15, 20, 30]
SONIA = [0.0380, 0.0365, 0.0360, 0.0365, 0.0375, 0.0390, 0.0410, 0.0420, 0.0410]   # zero rates, illustrative
RPI_ZC = [0.0340, 0.0330, 0.0325, 0.0320, 0.0322, 0.0328, 0.0333, 0.0335, 0.0325]  # ZC RPI swaps, illustrative
NOMINAL = LogLinearCurve(YEARS, [math.exp(-z * t) for z, t in zip(SONIA, YEARS, strict=True)])
REAL = real_curve(NOMINAL, YEARS, RPI_ZC)
PARAMS = {"kappa": 0.05, "sigma_r": 0.0080, "sigma_i": 0.015, "rho": 0.20}


def model(**over) -> JYDet:
    p = {**PARAMS, **over}
    return JYDet(NOMINAL, REAL, p["kappa"], p["sigma_r"], p["sigma_i"], p["rho"])


def convexity_table() -> list[tuple[int, float, float, float]]:
    """(year i, forward YoY %, YoY with convexity %, adjustment bp) for the rate I(i)/I(i-1) - 1."""
    m = model()
    rows = []
    for i in range(1, 21):
        f = (REAL.df_t(i) / REAL.df_t(i - 1)) / (NOMINAL.df_t(i) / NOMINAL.df_t(i - 1)) - 1
        y = m.yoy_ratio(i - 1, i) - 1
        rows.append((i, 100 * f, 100 * y, 1e4 * (y - f)))
    return rows


def rho_effect(i: int = 10) -> list[tuple[float, float]]:
    return [(rho, 1e4 * model(rho=rho).convexity(i - 1, i)) for rho in (-0.5, -0.2, 0.0, 0.2, 0.5)]


def mc_check(i: int = 10, paths: int = 40000) -> tuple[float, float, float]:
    m = model()
    r = m.simulate_ratios(i, paths)[:, i - 1]
    return m.yoy_ratio(i - 1, i), float(r.mean()), float(r.std(ddof=1) / math.sqrt(paths))


def caps(strike: float = 0.05, years: int = 10) -> dict:
    m = model()
    caplets = [m.yoy_caplet(i - 1, i, strike) for i in range(2, years + 1)]
    floors = [m.yoy_caplet(i - 1, i, 0.0, floor=True) for i in range(2, years + 1)]
    return {"cap": sum(caplets), "floor": sum(floors), "caplets": caplets,
            "yoy_swap": m.yoy_swap_rate(years), "zc_swap": m.zc_swap_rate(float(years))}


def lpi(years: int = 20) -> dict:
    m = model()
    five = m.lpi_leg(years, 0.05, 0.0)
    two = m.lpi_leg(years, 0.025, 0.0)
    return {"five": five, "two_half": two}


# ---- seasonality ---------------------------------------------------------------------------------------
DATA = ROOT / "data/markets-2/cpi_us_monthly.csv"


def us_seasonals() -> dict[int, float]:
    idx = {}
    for ln in open(DATA):
        if ln[0].isdigit():
            d, nsa, _ = ln.strip().split(",")
            idx[(int(d[:4]), int(d[5:7]))] = float(nsa)
    return seasonal_factors(idx)


def seasonal_forward_path(annual_rate: float = 0.03, months: int = 24) -> list[tuple[int, float, float]]:
    """Forward index (base 100) month by month: smooth, and with the US seasonal pattern (which sums to
    zero over a year, so annual points agree)."""
    s = us_seasonals()
    base = math.log(1 + annual_rate) / 12
    rows, lz, ls = [], 0.0, 0.0
    for k in range(months + 1):
        rows.append((k, 100 * math.exp(lz), 100 * math.exp(ls)))
        mth = (k % 12) + 1
        lz += base
        ls += base + s[mth] / 100
    return rows


__all__ = ["np"]
