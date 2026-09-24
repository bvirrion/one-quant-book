"""Chapter 23 of Book 2: credit default swaps. Upfront and running quotes with a flat hazard rate,
survival curves, the first stage of the Lehman Brothers settlement auction of 10 October 2008 (bids,
offers and physical settlement requests published in FRBNY Staff Report 372, Box 1), and the second
stage replayed on an illustrative book of limit orders consistent with the published result."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/cds"))
from firm_cds import (
    Cds,
    cash_settlement,
    final_price,
    hazard_from_spread,
    inside_market_midpoint,
    legs,
    open_interest,
    upfront_from_spread,
)

R = 0.04                                     # flat continuously compounded rate, illustrative
IG, HY = Cds(5.0, 0.01), Cds(5.0, 0.05)       # five-year contracts with the two standard coupons

# Lehman Brothers, 10 October 2008: the fourteen dealers' first-stage submissions (Box 1)
BIDS = [8, 8, 8, 8, 8.25, 8.75, 8.875, 9, 9, 9.25, 9.25, 9.5, 9.5, 10]
OFFERS = [10, 10, 10, 10, 10.25, 10.75, 10.875, 11, 11, 11, 11.25, 11.5, 11.5, 12]
REQUESTS = [("buy", 130), ("sell", 755), ("sell", 870), ("sell", 141), ("sell", 480), ("sell", 464), ("sell", 1470),
            ("sell", 390), ("buy", 612), ("sell", 574), ("sell", 191), ("sell", 170), ("buy", 30), ("sell", 187)]
QUOTATION_SIZE = 5e6
# Second stage: illustrative limit bids to buy bonds (price, USD millions); only the range (10.75 to
# 0.125), the median price and the result are published.
ORDERS = [(10.75, 50), (10.0, 150), (9.5, 300), (9.0, 900), (8.75, 1400), (8.625, 2600), (8.5, 1800),
          (8.0, 2500), (7.5, 3000), (5.0, 2000), (0.125, 500)]


def upfront_curve(lo: int = 0, hi: int = 1500, step: int = 25) -> list[tuple[int, float, float]]:
    """(quoted spread bp, upfront % for the 100 bp coupon, upfront % for the 500 bp coupon)."""
    return [(s, 100 * upfront_from_spread(IG, s / 1e4, R), 100 * upfront_from_spread(HY, s / 1e4, R))
            for s in range(lo, hi + 1, step)]


def survival_curves(spreads: tuple[int, ...] = (100, 300, 800), years: int = 10) -> list[tuple[float, ...]]:
    lams = [hazard_from_spread(IG, s / 1e4, R) for s in spreads]
    return [(t / 4, *(math.exp(-lam * t / 4) for lam in lams)) for t in range(4 * years + 1)]


def tutorial() -> dict[str, float]:
    lam = hazard_from_spread(IG, 0.01, R)
    a, p = legs(IG, lam, R)
    lam2 = hazard_from_spread(IG, 0.02, R)
    return {"lam_100": lam, "triangle_100": 0.01 / 0.6, "annuity_100": a, "protection_100": p,
            "surv5_100": math.exp(-5 * lam), "annuity_200": legs(IG, lam2, R)[0],
            "ig_200": upfront_from_spread(IG, 0.02, R), "ig_50": upfront_from_spread(IG, 0.005, R),
            "hy_300": upfront_from_spread(HY, 0.03, R), "hy_800": upfront_from_spread(HY, 0.08, R),
            "hy_1200": upfront_from_spread(HY, 0.12, R), "dv01_10m": 10e6 * a * 1e-4}


def first_stage() -> dict[str, float]:
    b, o = sorted(BIDS, reverse=True), sorted(OFFERS)
    crossed = 0
    while crossed < len(b) and b[crossed] >= o[crossed]:
        crossed += 1
    h = math.ceil((len(b) - crossed) / 2)
    raw = (sum(b[crossed:crossed + h]) + sum(o[crossed:crossed + h])) / (2 * h)
    imm = inside_market_midpoint(BIDS, OFFERS)
    sells = sum(x for side, x in REQUESTS if side == "sell")
    buys = sum(x for side, x in REQUESTS if side == "buy")
    return {"crossed": crossed, "half": h, "raw_mean": raw, "imm": imm, "sells": sells, "buys": buys,
            "oi": open_interest(REQUESTS), "penalty": QUOTATION_SIZE * (10.0 - imm) / 100}


def order_book() -> list[tuple[float, float, float]]:
    """(price, size, cumulative size) with bids sorted highest first."""
    out, cum = [], 0.0
    for p, s in sorted(ORDERS, key=lambda x: -x[0]):
        cum += s
        out.append((p, s, cum))
    return out


def problem() -> dict[str, float]:
    fs = first_stage()
    fp = final_price(fs["imm"], fs["oi"], ORDERS)
    thin = [(p, 1000 if p == 8.625 else s) for p, s in ORDERS]
    a_cash = cash_settlement(20e6, fp)                 # A: holds 20m of bonds and 20m of protection
    b_cash = cash_settlement(50e6, fp)                 # B: 50m of protection, no bonds
    c_cash = -cash_settlement(100e6 - 60e6, fp)        # C: sold 100m, bought 60m of protection
    d_cash = -cash_settlement(30e6, fp)                # D: sold 30m, asks to buy 30m of bonds
    return {**fs, "final": fp, "cap": fs["imm"] + 1.0, "all_high": final_price(fs["imm"], fs["oi"], [(12.0, 6000)]),
            "thin": final_price(fs["imm"], fs["oi"], thin), "paid_per_100": 100 - fp,
            "a_cash": a_cash, "a_bond": 20e6 * fp / 100, "b_cash": b_cash, "c_cash": c_cash, "d_cash": d_cash,
            "d_bonds": 30e6 * fp / 100, "gross": 72e9, "net": 5.2e9}
