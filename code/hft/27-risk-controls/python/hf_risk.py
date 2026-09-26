"""Risk controls (One Quant Book 11, chapter 27).

A runaway shaped on the SEC's account of 1 August 2012 (1,481 orders a second of 100 shares for 45 minutes, a loss of
$1.16 a share traded, $2.46 million of gross position a second), stopped by each control of firm.riskctl in turn;
the same controls' false alarms on 2,500 ordinary days of a legitimate market-making book; the trade-off between
catching the runaway and firing on ordinary days, for the loss limit and the position limit.
"""
from __future__ import annotations

import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "riskctl"))
import firm_riskctl as rc  # noqa: E402

CONTROLS = {
    "none (stopped at 45 minutes)": {},
    "person at 5 minutes": {"human_s": 300},
    "order-rate throttle, 500 a second": {"throttle": 500},
    "price collar, 5%": {"collar_bp": 500},
    "capital threshold, $1 billion gross": {"capital": 1e9},
    "position limit, $250 million gross": {"position": 2.5e8},
    "loss limit, $2 million, marked each second": {"loss": 2e6},
}
ALL = {"human_s": 300, "throttle": 500, "collar_bp": 500, "capital": 1e9, "position": 2.5e8, "loss": 2e6}


def table() -> dict:
    out = {}
    for name, c in CONTROLS.items():
        r = rc.runaway(c)
        fa = rc.normal_days(c)
        out[name] = {**r, "false_alarm": max(fa.values()) if fa else 0.0}
    r = rc.runaway(ALL)
    out["all of them"] = {**r, "false_alarm": max(rc.normal_days(ALL).values())}
    return out


def sweep() -> dict:
    """Loss limits from $0.5 to $4 million and position limits from $100 to $600 million: runaway loss against the
    share of ordinary days on which the control fires."""
    loss = {v: (rc.runaway({"loss": v})["loss"], rc.normal_days({"loss": v})["loss limit"])
            for v in (0.5e6, 0.75e6, 1e6, 1.5e6, 2e6, 3e6, 4e6)}
    pos = {v: (rc.runaway({"position": v})["loss"], rc.normal_days({"position": v})["position limit"])
           for v in (1e8, 1.5e8, 2e8, 2.5e8, 3e8, 4e8, 6e8)}
    return {"loss": loss, "position": pos}
