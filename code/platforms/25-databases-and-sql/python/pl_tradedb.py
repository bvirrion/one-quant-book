"""Databases and SQL (One Quant Book 15, chapter 25).

A week of trades (twenty accounts, five hundred instruments) is stored in firm.tradedb's bitemporal trades table,
each trade known a few seconds after it happened. On Wednesday at 10:00 operations correct Monday's and Tuesday's
errors: quantities keyed ten times too large, trades that never happened, and trades booked late. A regulator then asks
for Tuesday's 18:00 positions report as the firm produced it; the bitemporal table gives it (valid Tuesday 18:00,
known Tuesday 18:00) and the corrected one (valid Tuesday 18:00, known now), and a table updated in place can only give
the second. Two writers updating one position show the lost update and its cures, and three queries are timed with
and without indexes in SQLite and in DuckDB (bench_tradedb.py, measured).
"""
from __future__ import annotations

import pathlib
import sys
import tempfile

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/tradedb"))
import firm_tradedb as D  # noqa: E402

DAY, HOUR = 86_400, 3_600
TUE_18 = DAY + 18 * HOUR
WED_10 = 2 * DAY + 10 * HOUR
NOW = 4 * DAY + 20 * HOUR                      # Friday evening
N_ACC, N_INST = 20, 500
FIXES = {"qty": 30, "cancel": 10, "late": 8}   # corrections made on Wednesday 10:00


def load(conn, per_day: int = 100_000, seed: int = 25) -> dict:
    """Instruments, accounts and a week of trades; returns what was corrected on Wednesday."""
    rng = np.random.default_rng(seed)
    D.migrate(conn)
    conn.execute("BEGIN")
    conn.executemany("INSERT INTO instruments VALUES (?, ?, 'USD')", [(i, f"S{i:03d}") for i in range(N_INST)])
    conn.executemany("INSERT INTO accounts VALUES (?, ?)", [(a, f"ACC{a:02d}") for a in range(N_ACC)])
    rows, n = [], 0
    for d in range(5):
        t = np.sort(rng.uniform(d * DAY + 9.5 * HOUR, d * DAY + 16 * HOUR, per_day)).astype(int)
        acc, ins = rng.integers(0, N_ACC, per_day), rng.integers(0, N_INST, per_day)
        qty = rng.choice([-1, 1], per_day) * rng.integers(1, 11, per_day) * 100
        px = np.round(rng.uniform(10, 500, per_day), 2)
        for k in range(per_day):
            rows.append((f"T{n:07d}", int(acc[k]), int(ins[k]), int(qty[k]), float(px[k]), int(t[k]), D.END,
                         int(t[k]) + 5, D.END))
            n += 1
    conn.executemany(f"INSERT INTO trades ({D.COLS}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
    conn.execute("COMMIT")
    # Wednesday 10:00: the corrections, all to trades of Monday and Tuesday
    early = [r for r in rows if r[5] < 2 * DAY]
    pick = rng.choice(len(early), FIXES["qty"] + FIXES["cancel"], replace=False)
    fixed = {"qty": [], "cancel": [], "late": []}
    conn.execute("BEGIN")
    for j, i in enumerate(pick):
        r = early[i]
        if j < FIXES["qty"]:                               # keyed ten times too large
            D.correct(conn, r[0], {"qty": r[3] // 10}, WED_10)
            fixed["qty"].append(r[0])
        else:
            D.cancel(conn, r[0], WED_10)
            fixed["cancel"].append(r[0])
    for k in range(FIXES["late"]):                         # Tuesday trades booked on Wednesday
        t = {"trade_id": f"L{k:03d}", "account_id": int(rng.integers(0, N_ACC)),
             "instrument_id": int(rng.integers(0, N_INST)), "qty": int(rng.integers(1, 11)) * 100,
             "price": 100.0, "time": DAY + 15 * HOUR + k * 60}
        D.book(conn, t, WED_10)
        fixed["late"].append(t["trade_id"])
    conn.execute("COMMIT")
    return fixed


def in_place_copy(conn) -> dict:
    """What a table corrected in place holds: only the latest knowledge."""
    return D.positions(conn, TUE_18, NOW)


def report(per_day: int = 100_000) -> dict:
    conn = D.connect()
    fixed = load(conn, per_day)
    as_was, corrected = D.positions(conn, TUE_18, TUE_18), D.positions(conn, TUE_18, NOW)
    keys = sorted(set(as_was) | set(corrected))
    diff = [(k, as_was.get(k, 0), corrected.get(k, 0)) for k in keys if as_was.get(k, 0) != corrected.get(k, 0)]
    return {"as_was": as_was, "corrected": corrected, "diff": diff, "fixed": fixed,
            "in_place_equals_corrected": in_place_copy(conn) == corrected,
            "n_trades": conn.execute("SELECT COUNT(*) FROM trades WHERE sys_to = ?", (D.END,)).fetchone()[0],
            "versions": conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0], "conn": conn}


# ------------------------------------------------------------ the lost update
def interleavings(n: int, seed: int = 25) -> list[list[int]]:
    """n random orders of two transactions' two steps each (read, write), each keeping its own order."""
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        seq = [0, 0, 1, 1]
        rng.shuffle(seq)
        out.append(seq)
    return out


def lost_updates(mode: str, n: int = 1_000) -> int:
    """Two writers each add 100 shares to one position; count the trials where the result is
    not +200. Modes: 'autocommit' (read, then write, each its own transaction), 'transaction'
    (BEGIN IMMEDIATE around read and write), 'one statement' (UPDATE ... SET q = q + 100)."""
    lost = 0
    with tempfile.TemporaryDirectory() as tmp:
        path = f"{tmp}/p.db"
        a, b = D.connect(path), D.connect(path)
        for c in (a, b):
            c.execute("PRAGMA synchronous = OFF")           # concurrency is the point here, not durability
        a.execute("CREATE TABLE pos (k TEXT PRIMARY KEY, q INTEGER)")
        for order in interleavings(n):
            a.execute("DELETE FROM pos")
            a.execute("INSERT INTO pos VALUES ('x', 0)")
            conns, seen, step = (a, b), [None, None], [0, 0]
            queue = list(order)
            while queue:
                w = queue.pop(0)
                c = conns[w]
                try:
                    _step(c, mode, step[w], seen, w)
                except D.sqlite3.OperationalError:          # locked: wait for the other to finish
                    queue.append(w)
                    continue
                step[w] += 1
            if a.execute("SELECT q FROM pos").fetchone()[0] != 200:
                lost += 1
    return lost


def _step(c, mode, k, seen, w):
    if mode == "one statement":
        if k == 0:
            c.execute("UPDATE pos SET q = q + 100 WHERE k = 'x'")
        return
    if k == 0:
        if mode == "transaction":
            c.execute("BEGIN IMMEDIATE")
        seen[w] = c.execute("SELECT q FROM pos WHERE k = 'x'").fetchone()[0]
    else:
        c.execute("UPDATE pos SET q = ? WHERE k = 'x'", (seen[w] + 100,))
        if mode == "transaction":
            c.execute("COMMIT")


# ------------------------------------------------------------ queries timed by bench_tradedb.py
QUERIES = {
    "point": ("SELECT SUM(qty) FROM trades WHERE account_id = 7 AND instrument_id = 123 "
              "AND valid_from <= 151200 AND 151200 < valid_to AND sys_from <= 151200 AND 151200 < sys_to"),
    "report": D.POSITIONS.replace(":v", "151200").replace(":s", "151200"),
    "analytic": ("SELECT instrument_id, SUM(qty * price) FROM trades WHERE sys_to = 1000000000000 "
                 "GROUP BY instrument_id"),
}
INDEXES = {"none": [], "account, instrument": ["CREATE INDEX ix_ai ON trades (account_id, instrument_id)"],
           "valid time": ["CREATE INDEX ix_v ON trades (valid_from)"]}
ENGINE_LABELS = {"none": "SQLite no index", "account, instrument": "SQLite index account-instrument",
                 "valid time": "SQLite index valid time"}             # no commas in chart CSV labels

# exercise 7: every trade whose Tuesday 18:00 version differs from its current one
CHANGED = """SELECT o.trade_id, o.qty, n.qty, o.valid_to, n.valid_to
FROM trades o JOIN trades n ON n.trade_id = o.trade_id AND n.sys_to = 1000000000000
WHERE o.sys_from <= 151200 AND 151200 < o.sys_to
  AND (o.qty <> n.qty OR o.valid_to <> n.valid_to)"""
