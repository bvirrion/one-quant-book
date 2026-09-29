"""Position and P&L services (One Quant Book 15, chapter 17).

A quoting strategy (five hundred shares a side, an inventory limit of five thousand, orders left working if the
session drops) trades one hour of Book 10's simulator with a drop-copy session. At a seeded minute its order-entry
session drops for four seconds; the client logs back in asking for new messages only, so the execution reports
generated while it was down never reach it -- until operations request a replay a minute later. The drop copy carries
every execution, 50 milliseconds late. At minute 50 the venue busts the execution nearest minute 30. Three services
are compared with the clearing statement (every execution but the busted one): session reports only; session and drop
copy merged by execution identifier; merged with the bust applied.
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for p in ("code/firm/posservice", "code/firm/exchsim", "code/firm/tape", "code/firm/feed"):
    sys.path.insert(0, str(ROOT / p))
import firm_exchsim as X  # noqa: E402
import firm_posservice as P  # noqa: E402
from firm_tape import TapeConfig  # noqa: E402

SEC, MIN = X.SEC, 60 * X.SEC
CLIP, LIMIT, OUTAGE = 500, 5_000, 4 * SEC
DROPCOPY_LAG, REPLAY_AFTER = 50_000_000, 60 * SEC
BUST_AT, BUST_NOTICE = 30 * MIN, 50 * MIN


class Quoter(X.Agent):
    name = "q"

    def on_book(self, ctx, loc, top):
        b, _, a, _ = top
        if b is None or a is None:
            return
        live = [o for o in ctx.working() if o["status"] in ("live", "pending")]
        for o in live:
            if o["price"] != (b if o["side"] == "B" else a):
                ctx.cancel(o["cl"])
        sides = {o["side"] for o in live if o["price"] == (b if o["side"] == "B" else a)}
        pos = ctx.position(1)
        for side, px in (("B", b), ("S", a)):
            if side not in sides and (pos < LIMIT if side == "B" else pos > -LIMIT):
                ctx.send(X.Order(1, side, CLIP, px))


def day(seed: int, seconds: float = 3600.0, cod: bool = False) -> dict:
    rng = np.random.default_rng(seed)
    o = X.OPEN_NS
    drop = o + int(rng.integers(5, max(6, int(seconds / 60) - 20))) * MIN
    ph = X.Phases(start_ns=o - SEC, open_ns=o, close_ns=o + int(seconds) * SEC, end_ns=o + int(seconds + 1) * SEC)
    faults = (X.Fault("drop_session", drop, drop + OUTAGE, session="q@SIMX"),)
    cfg = X.ExchangeConfig(phases=ph, fees=X.FeeSchedule(make=0.0, take=0.0), faults=faults)
    sim = X.Simulator(cfg, seed=1)
    sim.add_background(X.TapeBackground(TapeConfig(seconds=seconds, seed=seed, news_at=None)))
    sim.add_agent(Quoter(), X.SessionSpec("HF1", cod=cod, drop_copy=True))
    res = sim.run()
    ctx = res.agents["q"]
    side = {o["cl"]: (1 if o["side"] == "B" else -1) for o in ctx.orders.values()}
    ex = res.drop_copy("HF1")
    ex = ex[ex["type"] == "E"]
    execs = [P.Execution(f"{int(r['match'])}-{int(r['cl_ord_id'])}", "HF1", "SIM1", side[int(r["cl_ord_id"])],
                         int(r["qty"]), int(r["price"]), int(r["ts"]), 0, 1) for r in ex]
    trades = res.engine().trades
    close = int(trades[-1][2]) if trades else 1_000_000
    bust = min(execs, key=lambda e: abs(e.ts - (o + BUST_AT))) if execs else None
    return {"execs": execs, "drop": drop, "close": close, "bust": bust, "open": o, "end": o + int(seconds) * SEC}


def services(d: dict) -> dict:
    """Feed the three services in arrival order; return them and the arrival log."""
    start, end = d["drop"], d["drop"] + OUTAGE
    replay = end + REPLAY_AFTER
    events = []
    for e in d["execs"]:
        lost = start <= e.ts < end
        events.append((replay if lost else e.ts, "session", e, lost))
        events.append((e.ts + DROPCOPY_LAG, "dropcopy", e, False))
    events.sort(key=lambda x: (x[0], x[1], x[2].exec_id))
    a, b, c = P.PositionService(("session",)), P.PositionService(), P.PositionService()
    for _t, src, e, replayed in events:
        if src == "session" and not replayed:
            a.on_execution(src, e)        # the session-only service never replays
        b.on_execution(src, e)
        c.on_execution(src, e)
    if d["bust"] is not None:
        c.on_bust(d["bust"].exec_id, d["open"] + BUST_NOTICE)
    return {"session": a, "merged": b, "merged+bust": c,
            "events": [(t, src, e) for t, src, e, _r in events]}


def truth(d: dict) -> P.PositionService:
    t = P.PositionService(("clearing",))
    for e in d["execs"]:
        t.on_execution("clearing", e)
    if d["bust"] is not None:
        t.on_bust(d["bust"].exec_id, d["bust"].ts)          # the statement treats a busted trade as never done
    return t


def at_close(seeds=range(1, 11), seconds: float = 3600.0, cod: bool = False) -> list[dict]:
    rows = []
    for s in seeds:
        d = day(s, seconds, cod)
        sv, tr = services(d), truth(d)
        truth_p = tr.position("HF1", "SIM1")
        lost = [e.ts for e in d["execs"] if d["drop"] <= e.ts < d["drop"] + OUTAGE]
        pending = (d["drop"] + OUTAGE + REPLAY_AFTER - (min(lost) + DROPCOPY_LAG)) / SEC if lost else 0.0
        row = {"seed": s, "drop_min": (d["drop"] - d["open"]) / MIN, "fills": len(d["execs"]), "pending_s": pending,
               "lost": sum(d["drop"] <= e.ts < d["drop"] + OUTAGE for e in d["execs"]),
               "true_pos": truth_p.quantity, "true_pnl": truth_p.total(d["close"]) / 1e4}
        for k in ("session", "merged", "merged+bust"):
            p = sv[k].position("HF1", "SIM1")
            row[f"{k}_pos_err"] = p.quantity - truth_p.quantity
            row[f"{k}_pnl_err"] = (p.total(d["close"]) - truth_p.total(d["close"])) / 1e4
        rows.append(row)
    return rows


def timeline(seed: int, step: int = 5 * SEC, seconds: float = 3600.0) -> dict:
    """Position of each service and of the clearing statement through the day, on a grid."""
    d = day(seed, seconds)
    sv = services(d)
    grid = np.arange(d["open"], d["end"] + 1, step)
    lost = {e.exec_id for e in d["execs"] if d["drop"] <= e.ts < d["drop"] + OUTAGE}
    bust = d["bust"].exec_id if d["bust"] is not None else None
    out = {"t_min": (grid - d["open"]) / MIN, "drop_min": (d["drop"] - d["open"]) / MIN}
    for k in ("session", "merged", "merged+bust"):
        first: dict = {}
        for t, src, e in sv["events"]:
            if k == "session" and (src != "session" or e.exec_id in lost):
                continue
            first.setdefault(e.exec_id, (t, e.side * e.qty))
        ev = [(t, q) for x, (t, q) in first.items()]
        if k == "merged+bust" and bust in first:
            ev.append((d["open"] + BUST_NOTICE, -first[bust][1]))
        ev.sort()
        ts = np.array([t for t, _ in ev])
        cum = np.cumsum([q for _, q in ev])
        idx = np.searchsorted(ts, grid, side="right") - 1
        out[k] = np.where(idx >= 0, cum[np.maximum(idx, 0)], 0)
    ev = sorted((e.ts, e.side * e.qty) for e in d["execs"] if e.exec_id != bust)
    ts, cum = np.array([t for t, _ in ev]), np.cumsum([q for _, q in ev])
    idx = np.searchsorted(ts, grid, side="right") - 1
    out["truth"] = np.where(idx >= 0, cum[np.maximum(idx, 0)], 0)
    out["lost"], out["bust_min"] = len(lost), (d["bust"].ts - d["open"]) / MIN if d["bust"] else None
    return out
