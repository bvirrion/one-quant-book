"""Post-trade systems (One Quant Book 15, chapter 22).

A week of institutional equity trades (500 a day, allocations to five funds, eight executing brokers) is confirmed by
the brokers, with discrepancies planted at stated rates: three brokers round the average price to four decimals, and
some confirmations carry a wrong price, a wrong settlement date, a wrong account, a wrong quantity or are missing.
Matching at several price tolerances gives the automatic match rate. The breaks that remain go to an operations team
of three, each break taking a random time to fix, in the window the settlement cycle leaves before the affirmation
cut-off -- the next working day under T+2, the evening of the trade date under T+1. Unfixed breaks fail to settle;
positions are then reconciled with the custodian and the breaks aged over the week.
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/posttrade"))
import firm_posttrade as PT  # noqa: E402

BROKERS = [f"BRK{i}" for i in range(1, 9)]
FUNDS = [f"FUND{i}" for i in range(1, 6)]
SYMBOLS = [f"S{i:03d}" for i in range(50)]
ROUNDERS = {"BRK1", "BRK2", "BRK3"}                     # brokers that round the average price to four decimals
RATES = {"price": 0.010, "settle_date": 0.010, "account": 0.015, "qty": 0.005, "missing": 0.010}
FIX_MINUTES = {"price": 45, "settle_date": 30, "account": 60, "qty": 45, "missing": 90}
KEYS = ("symbol", "side", "counterparty", "trade_date", "fund")
TOL = {"price": 1e-4, "qty": 0, "settle_date": 0, "account": 0}
WINDOWS = {"T+2": (24 + 8.0, 24 + 17.0), "T+1": (17.0, 21.0)}   # hours after the trade date's midnight
STAFF = 3


def trades(day: int, cycle: int, n: int = 500, seed: int = 22) -> list[dict]:
    rng = np.random.default_rng(seed * 100 + day)
    out = []
    for i in range(n):
        out.append({"trade_id": f"D{day}-{i:03d}", "symbol": str(rng.choice(SYMBOLS)), "side": int(rng.choice([1, -1])),
                    "qty": int(rng.integers(1, 100)) * 100, "price": round(float(rng.uniform(20, 300)), 6),
                    "counterparty": str(rng.choice(BROKERS)), "fund": str(rng.choice(FUNDS)), "trade_date": day,
                    "settle_date": day + cycle, "account": "CUST-" + str(rng.choice(FUNDS)), "market": "US"})
        out[-1]["account"] = "CUST-" + out[-1]["fund"]
    return out


def confirms(ours: list[dict], seed: int = 22, rates: dict | None = None) -> tuple[list[dict], dict]:
    """The brokers' confirmations with planted discrepancies; returns them and the planted kind per trade id."""
    rng = np.random.default_rng(seed + 7)
    out, planted = [], {}
    for t in ours:
        c = dict(t)
        if c["counterparty"] in ROUNDERS:
            c["price"] = round(c["price"], 4)
        u = rng.random()
        acc = 0.0
        for kind, p in (rates or RATES).items():
            acc += p
            if u < acc:
                planted[t["trade_id"]] = kind
                if kind == "price":
                    c["price"] = round(c["price"] + float(rng.choice([-1, 1])) * float(rng.uniform(0.01, 0.05)), 4)
                elif kind == "settle_date":
                    c["settle_date"] += 1
                elif kind == "account":
                    c["account"] = "CUST-" + str(rng.choice([f for f in FUNDS if "CUST-" + f != t["account"]]))
                elif kind == "qty":
                    c["qty"] += 100
                break
        if planted.get(t["trade_id"]) != "missing":
            c.pop("trade_id")
            out.append(c)
    return out, planted


def match_rates(tols=(0.0, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2), cycle: int = 1) -> list[tuple]:
    ours = trades(0, cycle)
    theirs, _ = confirms(ours)
    rows = []
    for tol in tols:
        tolerances = dict(TOL, price=tol)
        r = PT.match(ours, theirs, KEYS, tolerances)
        rows.append((tol, PT.match_rate(r, len(ours)), len(r.partial), len(r.ours_only), len(r.theirs_only)))
    return rows


def breaks(ours, theirs) -> list[dict]:
    r = PT.match(ours, theirs, KEYS, TOL)
    out = [{"trade": o, "kind": d[0]} for o, _t, _s, d in r.partial]
    out += [{"trade": o, "kind": "missing"} for o in r.ours_only]
    return out


def resolve(brks: list[dict], cycle: str, seed: int = 0,
            staff: int = STAFF) -> tuple[list, list]:
    """The team fixes breaks, largest value first, inside the window; (fixed, failed)."""
    rng = np.random.default_rng(seed)
    start, end = WINDOWS[cycle]
    free = [start] * staff
    order = sorted(brks, key=lambda b: -b["trade"]["qty"] * b["trade"]["price"])
    fixed, failed = [], []
    for b in order:
        k = int(np.argmin(free))
        took = float(rng.exponential(FIX_MINUTES[b["kind"]])) / 60.0
        if free[k] + took <= end:
            free[k] += took
            fixed.append(b)
        else:
            failed.append(b)
    return fixed, failed


def week(cycle: str, days: int = 5, staff: int = STAFF, rates: dict | None = None) -> dict:
    n_cycle = 2 if cycle == "T+2" else 1
    out = {"breaks": 0, "failed": 0, "failed_value": 0.0, "by_kind": {}, "positions": []}
    for d in range(days):
        ours = trades(d, n_cycle)
        theirs, _ = confirms(ours, seed=22 + d, rates=rates)
        brks = breaks(ours, theirs)
        _fixed, failed = resolve(brks, cycle, seed=d, staff=staff)
        out["breaks"] += len(brks)
        out["failed"] += len(failed)
        out["failed_value"] += sum(b["trade"]["qty"] * b["trade"]["price"] for b in failed)
        for b in failed:
            out["by_kind"][b["kind"]] = out["by_kind"].get(b["kind"], 0) + 1
            out["positions"].append((d, b))
    return out


def custodian_recon(cycle: str) -> dict:
    """Friday evening: positions from the trades that should have settled by Friday, the firm's against the
    custodian's, with the failed trades as breaks, aged from their settlement date."""
    lag = 2 if cycle == "T+2" else 1
    w = week(cycle)
    ours, theirs, opened = {}, {}, {}
    for d in range(5):
        for t in trades(d, lag):
            if t["settle_date"] <= 4:
                k = (t["account"], t["symbol"])
                ours[k] = ours.get(k, 0) + t["side"] * t["qty"]
                theirs[k] = theirs.get(k, 0) + t["side"] * t["qty"]
    for _d, b in w["positions"]:
        t = b["trade"]
        if t["settle_date"] <= 4:
            k = (t["account"], t["symbol"])
            theirs[k] -= t["side"] * t["qty"]
            opened[k] = min(opened.get(k, 1e9), 24.0 * t["settle_date"])
    brks = PT.reconcile(ours, theirs)
    for b in brks:
        b.opened = opened.get(b.key, 0.0)
    return {"breaks": len(brks), "ageing": PT.age(brks, now=24.0 * 4 + 18), "fails": w["failed"]}
