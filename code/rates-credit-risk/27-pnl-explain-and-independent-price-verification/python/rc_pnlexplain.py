"""Chapter 27 of Book 6: explaining a day of a swaption book's P&L. An illustrative risk reversal on
one-year-into-ten-year USD swaptions (normal model, annuity 8.0): long USD 320m of payers struck at 4.50%
and short USD 320m of receivers at 3.50%. Start of day: forward 4.00%, normal volatility 95 bp a year,
0.75 years to expiry. The big-move day: the forward rises 30 bp and the volatility 12 bp. Risk-based
explain with and without the cross term, revaluation-based explain in two orders, IPV of the volatility
marks against a consensus, and the market price uncertainty AVA."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
for p in ("code/firm/pnlexplain", "code/firm/shortrate"):
    sys.path.insert(0, str(ROOT / p))
from firm_pnlexplain import (  # noqa: E402
    aggregate_ava,
    greeks,
    ipv,
    mpu_ava,
    revaluation_based,
    risk_based,
    simplified_ava,
)
from firm_shortrate import normal_price  # noqa: E402

ANNUITY = 8.0
BOOK = [(320e6, 0.0450, True), (-320e6, 0.0350, False)]     # notional, strike, payer
START = {"f": 0.0400, "s": 0.0095, "t": 0.75}
END = {"f": 0.0430, "s": 0.0107, "t": 0.75 - 1 / 365}
BUMPS = {"f": 1e-4, "s": 1e-4, "t": 1 / 365}


def value(state: dict) -> float:
    return sum(n * normal_price(state["f"], k, state["t"], state["s"], ANNUITY, payer) for n, k, payer in BOOK)


def day() -> dict:
    g = greeks(value, START, BUMPS)
    actual = value(END) - value(START)
    df, ds = END["f"] - START["f"], END["s"] - START["s"]
    desk = risk_based({**g, "volga": 0.0}, df, ds, cross=False)         # the desk's explain: delta, gamma, vega, theta
    full = risk_based(g, df, ds, cross=True)
    return {"greeks": g, "actual": actual, "desk": desk, "full": full,
            "unexplained_desk": actual - desk["explained"], "unexplained_full": actual - full["explained"]}


def revaluation() -> dict:
    return {"f_first": revaluation_based(value, START, END, ["f", "s", "t"]),
            "s_first": revaluation_based(value, START, END, ["s", "f", "t"])}


# ---- IPV and prudent valuation -------------------------------------------------------------------------------
MARKS = [0.0095, 0.0095]                  # desk's normal-vol marks for the two strikes (start of day)
CONSENSUS = [0.0097, 0.0091]              # consensus mids (illustrative): the market's skew
TOL = [0.0002, 0.0002]                    # tolerance band, 2 bp of normal vol
DISPERSION = [0.00020, 0.00025]           # standard deviation of contributors' vols


def ipv_table():
    out = []
    for (n, k, payer), m, c, tol in zip(BOOK, MARKS, CONSENSUS, TOL, strict=True):
        (v, adj), = ipv([m], [c], [tol])
        pv_change = n * (normal_price(START["f"], k, START["t"], v, ANNUITY, payer)
                         - normal_price(START["f"], k, START["t"], m, ANNUITY, payer))
        out.append({"strike": k, "mark": m, "verified": v, "adj_vol": adj, "adj_value": pv_change})
    return out


def ava_table():
    items = []
    for (n, k, payer), c, sd in zip(BOOK, CONSENSUS, DISPERSION, strict=True):
        unit_price = normal_price(START["f"], k, START["t"], c, ANNUITY, payer)
        dp = normal_price(START["f"], k, START["t"], c + sd, ANNUITY, payer) - unit_price     # price sd from vol sd
        fv = n * unit_price
        items.append(mpu_ava(fv, unit_price, abs(dp), n))
    fv_abs = sum(abs(n * normal_price(START["f"], k, START["t"], c, ANNUITY, payer))
                 for (n, k, payer), c in zip(BOOK, CONSENSUS, strict=True))
    return {"individual": items, "total": aggregate_ava(items), "simplified": simplified_ava(fv_abs), "fv_abs": fv_abs}


def unexplained_by_move() -> list[tuple[float, float, float]]:
    """(forward move bp, unexplained without the cross term, with it) for a volatility move of 12 bp."""
    import numpy as np
    g = greeks(value, START, BUMPS)
    out = []
    for bp in np.linspace(-40, 40, 17):
        end = {"f": START["f"] + bp * 1e-4, "s": START["s"] + 0.0012, "t": START["t"] - 1 / 365}
        actual = value(end) - value(START)
        df, ds = bp * 1e-4, 0.0012
        out.append((float(bp), actual - risk_based({**g, "volga": 0.0}, df, ds, cross=False)["explained"],
                    actual - risk_based(g, df, ds, cross=True)["explained"]))
    return out
