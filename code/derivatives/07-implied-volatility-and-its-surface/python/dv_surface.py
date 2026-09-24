"""The implied-volatility surface: a synthetic index surface, its static arbitrage checks, smile
regimes and the risk-neutral density (Book 5, Chapter 7)."""
import datetime as dt
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for comp in ("bs", "volsurface"):
    sys.path.insert(0, str(ROOT / f"code/firm/{comp}"))
from firm_bs import black, ncdf  # noqa: E402
from firm_volsurface import Surface, arbitrage_report, from_vols, risk_neutral_density  # noqa: E402

ASOF = dt.date(2026, 9, 24)
SPOT, RATE, YIELD = 100.0, 0.03, 0.015
TENORS = (30, 91, 182, 365, 730)                     # days
KS = tuple(round(-0.6 + 0.05 * j, 2) for j in range(21))   # log-moneyness -0.60 .. +0.40


def smile_vol(k: float, t: float) -> float:
    """Illustrative equity-index smile: an upward term structure of at-the-money volatility, a skew
    decaying like t^(-1/2), and a curvature that also decays."""
    atm = 0.20 - 0.06 * math.exp(-t / 0.5)
    return atm + (-0.15 * k + 0.35 * k * k) / math.sqrt(t)


def forward(t: float) -> float:
    return SPOT * math.exp((RATE - YIELD) * t)


def index_surface(bump: tuple[int, float, float] | None = None) -> Surface:
    """The chapter's surface; bump = (expiry index, k, vol points) adds a quote error at one node."""
    exps = [ASOF + dt.timedelta(days=d) for d in TENORS]
    vols = []
    for i, d in enumerate(TENORS):
        t = d / 365.0
        row = [smile_vol(k, t) for k in KS]
        if bump and bump[0] == i:
            row[KS.index(bump[1])] += bump[2]
        vols.append(row)
    return from_vols(ASOF, exps, [forward(d / 365.0) for d in TENORS], KS, vols)


def skew_90_110(t: float) -> float:
    """Volatility at strike 90 minus volatility at strike 110 (strikes in spot terms)."""
    f = forward(t)
    return smile_vol(math.log(90 / f), t) - smile_vol(math.log(110 / f), t)


def regimes(move: float = -0.05, days: int = 91) -> dict[str, float]:
    """A spot move under sticky strike and sticky delta: at-the-money volatility and the value of a long
    put struck at 100."""
    t = days / 365.0
    f0 = forward(t)
    f1 = f0 * (1 + move)
    df = math.exp(-RATE * t)
    vol_k100_before = smile_vol(math.log(100 / f0), t)
    strike_after = smile_vol(math.log(100 / f0), t)              # sticky strike: the 100 strike keeps its vol
    delta_after = smile_vol(math.log(100 / f1), t)               # sticky delta: vol follows moneyness
    atm_before = smile_vol(0.0, t)
    atm_strike = smile_vol(math.log(f1 / f0), t)                 # new ATM strike f1, read on the old curve
    put0 = black(f0, 100, t, df, vol_k100_before, "P")
    return {"atm_before": atm_before, "atm_sticky_strike": atm_strike, "atm_sticky_delta": atm_before,
            "vol100_strike": strike_after, "vol100_delta": delta_after,
            "put_before": put0, "put_sticky_strike": black(f1, 100, t, df, strike_after, "P"),
            "put_sticky_delta": black(f1, 100, t, df, delta_after, "P")}


def density(days: int = 91, flat: bool = False) -> list[tuple[float, float]]:
    t = days / 365.0
    f, df = forward(t), math.exp(-RATE * t)
    ks = np.arange(40.0, 160.01, 0.5)
    atm = smile_vol(0.0, t)
    calls = [black(f, k, t, df, atm if flat else smile_vol(math.log(k / f), t), "C") for k in ks]
    return risk_neutral_density(ks, calls, df)


def crash_probability(level: float = 80.0, days: int = 91) -> dict[str, float]:
    """Risk-neutral probability that the index ends below `level`: minus the strike derivative of the
    put, discounted back, with and without the skew."""
    t = days / 365.0
    f, df = forward(t), math.exp(-RATE * t)
    h = 0.01

    def put(k, flat):
        vol = smile_vol(0.0, t) if flat else smile_vol(math.log(k / f), t)
        return black(f, k, t, df, vol, "P")
    skew = (put(level + h, False) - put(level - h, False)) / (2 * h) / df
    flat = (put(level + h, True) - put(level - h, True)) / (2 * h) / df
    atm = smile_vol(0.0, t)
    d2 = (math.log(f / level) - 0.5 * atm * atm * t) / (atm * math.sqrt(t))
    return {"skewed": skew, "flat": flat, "flat_formula": ncdf(-d2), "ratio": skew / flat,
            "vol_at_80": smile_vol(math.log(level / f), t), "atm": atm}


def asset_class_smiles(ks) -> list[tuple[float, float, float, float]]:
    """Illustrative three-month smiles by asset class, as functions of log-moneyness."""
    out = []
    for k in ks:
        equity = smile_vol(k, 0.25)
        fx = 0.095 - 0.03 * k + 0.25 * k * k           # nearly symmetric, a small risk reversal
        commodity = 0.30 + 0.15 * k + 0.4 * k * k       # volatility rises with the price
        out.append((k, equity, fx, commodity))
    return out


def check(surface: Surface) -> dict:
    rep = arbitrage_report(surface)
    return {"calendar": len(rep["calendar"]), "butterfly": len(rep["butterfly"]),
            "worst": min((g for _, _, g in rep["butterfly"]), default=0.0), "detail": rep}

