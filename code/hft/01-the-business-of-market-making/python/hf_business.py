"""The business of market making (One Quant Book 11, chapter 1).

Two parts. (1) Unit economics from public statements: Virtu Financial's 10-K for 2025 and Flow Traders' results for
2025 (figures copied from the filings, sources in sources/hft/01-the-business-of-market-making.md), and a synthetic
small firm's break-even volume and operating leverage (firm.mmecon). (2) A first market maker in firm.tape's
synthetic market, run through firm.mmharness: it joins the best bid and ask with 100 shares, holds at most 500, and
its P&L is decomposed into spread capture, adverse selection and inventory against the mid and against the efficient
price, over ten simulated hours. Money in dollars.
"""
from __future__ import annotations

import functools
import os
import pathlib
import sys
from dataclasses import replace

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
for dep in ("mmharness", "mmecon", "tape"):
    sys.path.insert(0, str(ROOT / "firm" / dep))
import firm_mmecon as econ  # noqa: E402
import firm_mmharness as mh  # noqa: E402
import firm_tape as ft  # noqa: E402

# Virtu Financial, Form 10-K for 2025 ($ millions; 248.5 trading days; about 1,027 employees on 13 February 2026).
VIRTU = {"trading_income": 2436.707, "interest_dividends_income": 508.817, "commissions_tech": 617.025,
         "other": 69.569, "total_revenue": 3632.118, "brokerage_exchange_pfof": 769.774,
         "interest_dividends_expense": 647.448, "employee_comp": 528.085, "comm_data": 249.207,
         "ops_admin": 97.922, "depreciation": 64.420, "anti": 2145.3, "anti_mm": 1666.304, "days": 248.5,
         "employees": 1027}
# Flow Traders, 4Q and FY 2025 results (EUR millions; ETP value traded EUR bn; FTEs at year end).
FLOW = {"nti": 485.8, "etp_value_traded_bn": 1940.0, "fixed_employee": 97.3, "technology": 70.6, "other": 36.3,
        "fixed_opex": 204.1, "variable_employee": 77.4, "total_opex": 281.6, "ebitda": 198.9, "net_profit": 133.6,
        "ftes": 635}

FEES = mh.Fees(make=-0.001, take=0.001)          # illustrative: a 0.1 cent rebate, a 0.1 cent take fee, per share
SEEDS = tuple(range(1, 11))
HORIZONS = (0.0, 0.5, 1, 2, 5, 10, 20, 30, 60)


def public() -> dict:
    v, f = VIRTU, FLOW
    fixed_v = v["employee_comp"] + v["comm_data"] + v["ops_admin"] + v["depreciation"]
    return {
        "virtu_anti_day": econ.per_day(v["anti"], v["days"]),
        "virtu_mm_day": econ.per_day(v["anti_mm"], v["days"]),
        "virtu_mm_share": v["anti_mm"] / v["anti"],
        "virtu_direct": v["brokerage_exchange_pfof"] + v["interest_dividends_expense"],
        "virtu_fixed": fixed_v,
        "virtu_fixed_day": econ.per_day(fixed_v, v["days"]),
        "virtu_comm_data_day": econ.per_day(v["comm_data"], v["days"]),
        "virtu_comp_per_employee": v["employee_comp"] / v["employees"],
        "virtu_anti_per_employee": v["anti"] / v["employees"],
        "flow_capture_bp": econ.capture_bp(f["nti"] * 1e6, f["etp_value_traded_bn"] * 1e9),
        "flow_fixed_per_fte": f["fixed_opex"] / f["ftes"],
        "flow_ebitda_margin": f["ebitda"] / f["nti"],
        "flow_tech_share_fixed": f["technology"] / f["fixed_opex"],
    }


# A synthetic small firm: 0.5 bp gross capture on value traded, 0.2 bp of fees and financing, $40,000 a day of fixed
# costs (about $10 million a year).
SMALL = {"capture": 0.5e-4, "variable": 0.2e-4, "fixed": 40_000.0}


def small_firm(volume: float = 2e9) -> dict:
    c, v, f = SMALL["capture"], SMALL["variable"], SMALL["fixed"]
    return {"breakeven": econ.breakeven_volume(c, v, f), "profit": float(econ.profit(volume, c, v, f)),
            "leverage": econ.operating_leverage(volume, c, v, f)}


def cfg(seed: int) -> ft.TapeConfig:
    return replace(ft.TapeConfig(), seed=seed)


@functools.cache
def first_day(seed: int, fees: mh.Fees = FEES) -> mh.Result:
    return mh.run_tape(mh.SymmetricQuoter(100, 500), cfg(seed), fees=fees)


def decomposition(H: float = 10.0, ref: str = "mid") -> dict:
    """Mean over the ten seeds of the P&L parts per simulated hour, and per share traded (cents)."""
    rows = [first_day(s).decompose(H, ref) for s in SEEDS]
    vol = [first_day(s).volume() for s in SEEDS]
    out = {k: float(np.mean([r[k] for r in rows])) for k in rows[0]}
    out["volume"] = float(np.mean(vol))
    out["per_share"] = {k: 100 * float(np.sum([r[k] for r in rows]) / np.sum(vol)) for k in rows[0]}
    out["sd_total"] = float(np.std([r["total"] for r in rows], ddof=1))
    out["se_total"] = out["sd_total"] / np.sqrt(len(rows))
    out["messages"] = float(np.mean([first_day(s).messages for s in SEEDS]))
    out["market_share"] = float(np.sum(vol) / np.sum([first_day(s).tape.trades["qty"].sum() for s in SEEDS]))
    return out


def markout_curve(ref: str) -> np.ndarray:
    """Quantity-weighted mean mark-out (cents per share) of every fill of the ten runs, by horizon."""
    num, den = np.zeros(len(HORIZONS)), 0.0
    for s in SEEDS:
        r = first_day(s)
        m = r.markouts(HORIZONS, ref) * 100 * r.tick
        num += r.fills["qty"] @ m
        den += r.fills["qty"].sum()
    return num / den


def waterfall() -> list[tuple[str, float]]:
    """Virtu 2025 from revenue to pre-tax operating result before financing and one-offs ($ millions)."""
    v = VIRTU
    rev = v["trading_income"] + v["interest_dividends_income"] + v["commissions_tech"] + v["other"]
    steps = [("revenue", rev), ("fees and order flow", -v["brokerage_exchange_pfof"]),
             ("interest and dividends", -v["interest_dividends_expense"]), ("staff", -v["employee_comp"]),
             ("communication and data", -v["comm_data"]), ("operations", -v["ops_admin"]),
             ("depreciation", -v["depreciation"])]
    return steps


def feedback() -> tuple[int, int]:
    """Messages in the first 1,400 seconds of seed 1: quoting off the raw top (own orders included) against the book
    without the Quoter's own orders."""
    c = replace(cfg(1), seconds=1400.0)
    return tuple(mh.run_tape(mh.SymmetricQuoter(100, 500, raw=raw), c, fees=FEES).messages for raw in (True, False))
