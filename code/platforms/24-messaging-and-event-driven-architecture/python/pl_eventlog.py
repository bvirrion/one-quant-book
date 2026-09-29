"""Messaging and event-driven architecture (One Quant Book 15, chapter 24).

A day of 10,000 synthetic fills for ten accounts and twenty stocks is published to a partitioned log keyed by account
and consumed by a position service in batches of 100, under crash schedules: ten crashes a day at points drawn
uniformly over the consumer's steps (each message, and the moment between processing a batch and committing its
offset), a hundred days per mode. Three modes: commit before processing (at-most-once), commit after (at-least-once),
and positions and offsets in one SQLite transaction (atomic). For each fill we count how many times it was applied;
lost and duplicated fills and the position error follow. A trade-capture service then publishes 2,000 trades three
ways -- write then publish, publish then write, and through a transactional outbox -- with a 1% chance of a crash
at the dangerous point of each.
"""
from __future__ import annotations

import pathlib
import sys
import tempfile

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/eventlog"))
import firm_eventlog as L  # noqa: E402

ACCOUNTS = [f"ACC{i}" for i in range(10)]
SYMBOLS = [f"S{i:02d}" for i in range(20)]
PARTITIONS, BATCH, CRASHES = 4, 100, 10
MODES = ("at-most-once", "at-least-once", "atomic")


def fills(n: int = 10_000, seed: int = 24) -> list[dict]:
    rng = np.random.default_rng(seed)
    return [{"id": i, "account": str(rng.choice(ACCOUNTS)), "symbol": str(rng.choice(SYMBOLS)),
             "qty": int(rng.choice([-1, 1])) * int(rng.integers(1, 11)) * 100} for i in range(n)]


def truth(fs: list[dict]) -> dict:
    out: dict = {}
    for f in fs:
        k = f["account"] + "/" + f["symbol"]
        out[k] = out.get(k, 0) + f["qty"]
    return out


def publish(fs: list[dict]) -> L.Log:
    log = L.Log()
    log.create("fills", PARTITIONS)
    for f in fs:
        log.append("fills", f["account"], f)
    return log


def day(fs: list[dict], mode: str, crash_steps: list[int], db: str | None = None) -> dict:
    """Consume the day's fills with crashes at the given step numbers; returns applications
    per fill id, the positions and the crashes that happened."""
    log = publish(fs)
    applied = np.zeros(len(fs), dtype=int)
    pos: dict = {}
    store = L.AtomicStore(db) if mode == "atomic" else None
    pending: list = []
    steps, todo, crashed = [0], sorted(crash_steps), [0]

    def crash(stage, i):
        steps[0] += 1
        if todo and steps[0] == todo[0]:
            todo.pop(0)
            raise L.Crash(stage)

    done = set()                                     # 'idempotent': applied fill ids, kept with the state

    def apply(f):
        if mode == "atomic":
            store.apply(f)
            pending.append(f["id"])
        elif mode == "idempotent" and f["id"] in done:
            return
        else:
            done.add(f["id"])
            k = f["account"] + "/" + f["symbol"]
            pos[k] = pos.get(k, 0) + f["qty"]
            applied[f["id"]] += 1

    busy = True
    while busy:
        busy = False
        for p in range(PARTITIONS):
            try:
                m = "at-least-once" if mode == "idempotent" else mode
                n = L.run_batch(log, "positions", "fills", p, BATCH, apply, m, crash, store)
                if mode == "atomic":
                    applied[pending] += 1
                    pending.clear()
            except L.Crash:
                crashed[0] += 1
                n = 1
                if store is not None:
                    store.rollback()
                    pending.clear()
            busy = busy or n > 0
    if store is not None:
        pos = store.positions()
        store.db.close()
    return {"applied": applied, "positions": pos, "crashes": crashed[0], "steps": steps[0]}


def schedules(mode: str, days: int = 100, n: int = 10_000, seed: int = 24) -> dict:
    """`days` days of `CRASHES` crashes each; lost and duplicated fills per 1,000 crashes and
    the largest position error (shares) in any account and stock at the end of a day."""
    fs = fills(n)
    true = truth(fs)
    total_steps = n + (n // BATCH + PARTITIONS)          # one step per message and per commit point
    rng = np.random.default_rng(seed)
    lost = dup = crashes = 0
    worst = []
    with tempfile.TemporaryDirectory() as tmp:
        for d in range(days):
            steps = sorted(rng.choice(np.arange(1, total_steps), CRASHES, replace=False).tolist())
            r = day(fs, mode, steps, db=f"{tmp}/d{d}.sqlite")
            a = r["applied"]
            lost += int((a == 0).sum())
            dup += int(np.clip(a - 1, 0, None).sum())
            crashes += r["crashes"]
            worst.append(max(abs(r["positions"].get(k, 0) - v) for k, v in true.items()))
    return {"lost": lost, "dup": dup, "crashes": crashes, "lost_per_1000": 1000 * lost / crashes,
            "dup_per_1000": 1000 * dup / crashes, "worst": worst, "max_error": max(worst)}


# ------------------------------------------------------------ publishing trades
def publishing(design: str, n: int = 2_000, p_crash: float = 0.01, seed: int = 24) -> dict:
    """Trades written and announced under three designs; a crash at the dangerous point
    loses the in-flight work and the service restarts. Counts events lost, phantom and
    duplicated in the log against the trades in the database."""
    rng = np.random.default_rng(seed)
    log = L.Log()
    log.create("trades", 4)
    db_trades = set()
    with tempfile.TemporaryDirectory() as tmp:
        box = L.Outbox(f"{tmp}/o.sqlite") if design.startswith("outbox") else None
        idem = design == "outbox"
        for i in range(n):
            t, ev = {"id": f"T{i}"}, {"key": f"T{i}", "trade": f"T{i}"}
            die = rng.random() < p_crash
            if design == "write-then-publish":
                db_trades.add(t["id"])
                if not die:
                    log.append("trades", ev["key"], ev)
            elif design == "publish-then-write":
                log.append("trades", ev["key"], ev)
                if not die:
                    db_trades.add(t["id"])
            else:
                box.write(t, ev)
                db_trades.add(t["id"])

                def crash(stage, num, die=die):
                    if die and stage == "published":
                        raise L.Crash(stage)
                try:
                    _relay(box, log, idem, crash)
                except L.Crash:
                    _relay(box, log, idem, None)           # the restarted relay resends
        if box is not None:
            box.db.close()
    events = [v["trade"] for part in log.parts["trades"] for _o, _k, v in part]
    seen = set(events)
    return {"lost": len(db_trades - seen), "phantom": len(seen - db_trades), "duplicated": len(events) - len(seen)}


def _relay(box, log, idem, crash):
    if idem:
        return box.relay(log, "trades", crash)
    n = 0                                               # the same relay without idempotence keys
    rows = box.db.execute("SELECT n, key, body FROM outbox WHERE sent = 0 ORDER BY n").fetchall()
    for num, key, body in rows:
        log.append("trades", key, L.json.loads(body))
        if crash:
            crash("published", num)
        box.db.execute("UPDATE outbox SET sent = 1 WHERE n = ?", (num,))
        n += 1
    return n
