"""Market-data distribution and entitlements (One Quant Book 15, chapter 23).

Part one distributes ten minutes of depth updates for twenty instruments (Book 7's tape generator, the order flow
that firm.exchsim's background replays) to four subscribers of different speeds, with and without conflation, and
revokes a screen user's entitlement half-way through, with the check made at subscribe time only or at every
delivery. Part two is the audit: three years of a firm's usage logs -- display users by user identifier, eleven
applications by device -- reconciled with the licences it held (40 display subscribers, no non-display) and priced
with a venue's published 2026 monthly fees (ledger F1).
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("entitle", "tape"):
    sys.path.insert(0, str(ROOT / "code/firm" / c))
import firm_entitle as E  # noqa: E402
import firm_tape as T  # noqa: E402

SOURCE = "DEPTH"                                 # the venue's depth-of-book product
# Subscribers: (name, subject, use, seconds per message, instruments followed)
SUBSCRIBERS = [("strategy", "app:strat-a", "non-display", 20e-6, 20),
               ("risk", "app:risk", "non-display", 2e-3, 20),
               ("research", "app:dashboard", "non-display", 10e-3, 20),
               ("screen", "user:t07", "display", 50e-3, 5)]
REVOKE_AT = 300.0

# Fees (ledger F1): the venue's 2026 monthly fees for its depth product.
DISPLAY_FEE = 84.00                              # professional subscriber, per month
ND_TIERS = ((39, 412.00, "each"), (99, 16_490.00, "firm"), (249, 32_990.00, "firm"), (10**9, 75_000.00, "firm"))
MONTHS = 36                                      # the look-back of a good-faith error (ledger F4)
LICENSED = {"display": 40, "non-display": 0}
# The eleven applications: (name, first month used, devices)
APPS = [("strategy A", 0, 2), ("risk service", 0, 2), ("tick recorder", 2, 1), ("strategy B", 4, 2),
        ("P&L service", 6, 1), ("order router", 8, 2), ("strategy C", 10, 3), ("TCA", 12, 1),
        ("surveillance", 15, 2), ("research dashboard", 18, 4), ("strategy D", 22, 2)]


def non_display_fee(n: int) -> float:
    for top, fee, per in ND_TIERS:
        if n <= top:
            return fee * n if per == "each" else (fee if n > 0 else 0.0)
    raise ValueError(n)


FEES = {"display": lambda n: DISPLAY_FEE * n, "non-display": non_display_fee}


def updates(seconds: float = 600.0, n_inst: int = 20, seed: int = 23) -> list[tuple]:
    """(time, instrument, (bid, ask)) for every book message of every instrument, time-ordered."""
    rows = []
    for k in range(n_inst):
        tp = T.simulate(T.TapeConfig(seconds=seconds, seed=seed * 100 + k, news_at=None))
        top, name = tp.top, f"I{k:02d}"
        rows += [(float(t), name, (int(b), int(a))) for t, b, a in zip(top["t"], top["bid"], top["ask"], strict=True)]
    rows.sort(key=lambda r: (r[0], r[1]))
    return rows


def distribute(ups: list, policy: str, check_on_delivery: bool = True, trace_every: int = 0) -> dict:
    ents = E.EntitlementSystem()
    for _name, subject, use, _svc, _n in SUBSCRIBERS:
        ents.grant(E.Entitlement(subject, SOURCE, use), 0.0)
    ents.revoke(E.Entitlement("user:t07", SOURCE, "display"), REVOKE_AT)
    bus = E.Bus(ents, check_on_delivery, trace_every)
    for name, subject, use, svc, n in SUBSCRIBERS:
        pol = "conflate" if name == "screen" else policy
        bus.subscribe(name, subject, SOURCE, use, [f"I{k:02d}" for k in range(n)], svc, pol)
    return bus.run(ups)


def usage_log(seed: int = 23) -> E.UsageLog:
    """Three years of monthly usage: traders (38 growing to 47) with one or two user identifiers,
    and the eleven applications on their devices."""
    rng = np.random.default_rng(seed)
    second_id = rng.random(60) < 0.15                  # a second login (another desk, a laptop)
    log = E.UsageLog()
    for m in range(MONTHS):
        people = 38 + (9 * m) // (MONTHS - 1)
        for p in range(people):
            log.record(m, SOURCE, "display", f"user:t{p:02d}", f"t{p:02d}")
            if second_id[p]:
                log.record(m, SOURCE, "display", f"user:t{p:02d}b", f"t{p:02d}")
        for name, start, devices in APPS:
            if m >= start:
                for d in range(devices):
                    log.record(m, SOURCE, "non-display", f"host:{name}:{d}", name)
    return log


def audit(licensed: dict | None = None) -> dict:
    rows = E.audit(usage_log(), SOURCE, range(MONTHS), licensed or LICENSED, FEES)
    disp = sum(DISPLAY_FEE * r.shortfall["display"] for r in rows)
    return {"rows": rows, "owed": sum(r.owed for r in rows), "display_owed": disp,
            "non_display_owed": sum(r.owed for r in rows) - disp,
            "last": rows[-1], "under_pct": 100 * max((r.used["display"] + r.used["non-display"]) /
                                                     max(1, r.licensed["display"] + r.licensed["non-display"]) - 1
                                                     for r in rows)}
