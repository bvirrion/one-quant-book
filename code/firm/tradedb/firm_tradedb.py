"""firm.tradedb -- a relational trade store: schema, migrations, bitemporal tables, time travel (Book 15, ch. 25).

Instruments, accounts and trades are relational tables with primary and foreign keys; migrations are numbered SQL
scripts applied once each and recorded. The trades table is bitemporal: every row version carries a valid-time
interval (when the trade is true in the world) and a system-time interval (when the database believed it), both
half-open [from, to) in seconds, with END for an open end. A correction never updates a row: it closes the current
version's system time and inserts the corrected version, so that any past state of knowledge can be queried again
with as_of(valid, system). Writers run inside BEGIN IMMEDIATE transactions with retry; an index advisor reads SQLite's
EXPLAIN QUERY PLAN; the same SQL runs on sqlite3 and DuckDB.

API (stable):
    connect(path=':memory:') -> sqlite3.Connection with foreign keys on ; migrate(conn) -> version
    book(conn, trade, sys_time) ; correct(conn, trade_id, changes, sys_time) ; cancel(conn, trade_id, sys_time)
    as_of(conn, valid, system) -> [trade rows] ; positions(conn, valid, system) -> {(account, symbol): qty}
    transact(conn, fn, retries=5) -> fn's result, BEGIN IMMEDIATE ... COMMIT, retried while the database is locked
    plan(conn, sql, params=()) -> [str] ; advise(conn, sql, params=()) -> [table scanned without an index]
    to_duckdb(conn, tables) -> duckdb connection holding copies of the tables
"""
from __future__ import annotations

import sqlite3
import time

END = 10**12                                    # an open end of an interval (seconds)

MIGRATIONS = [
    (1, """
CREATE TABLE instruments (id INTEGER PRIMARY KEY, symbol TEXT NOT NULL UNIQUE,
  currency TEXT NOT NULL);
CREATE TABLE accounts (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
CREATE TABLE trades (
  trade_id TEXT NOT NULL,
  account_id INTEGER NOT NULL REFERENCES accounts(id),
  instrument_id INTEGER NOT NULL REFERENCES instruments(id),
  qty INTEGER NOT NULL, price REAL NOT NULL,
  valid_from INTEGER NOT NULL, valid_to INTEGER NOT NULL,
  sys_from INTEGER NOT NULL, sys_to INTEGER NOT NULL,
  PRIMARY KEY (trade_id, sys_from));
"""),
    (2, "CREATE TABLE audit (at INTEGER NOT NULL, trade_id TEXT NOT NULL, what TEXT);"),
]


def connect(path: str = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(path, isolation_level=None, timeout=0)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def migrate(conn: sqlite3.Connection) -> int:
    conn.execute("CREATE TABLE IF NOT EXISTS schema_version (v INTEGER PRIMARY KEY)")
    have = {r[0] for r in conn.execute("SELECT v FROM schema_version")}
    for v, sql in MIGRATIONS:
        if v not in have:
            conn.execute("BEGIN")
            for stmt in filter(str.strip, sql.split(";")):
                conn.execute(stmt)
            conn.execute("INSERT INTO schema_version VALUES (?)", (v,))
            conn.execute("COMMIT")
    return max(v for v, _ in MIGRATIONS)


# ------------------------------------------------------------ bitemporal writes
COLS = "trade_id, account_id, instrument_id, qty, price, valid_from, valid_to, sys_from, sys_to"


def book(conn, t: dict, sys_time: int) -> None:
    """A new trade, true from its trade time, known from sys_time."""
    conn.execute(f"INSERT INTO trades ({COLS}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                 (t["trade_id"], t["account_id"], t["instrument_id"], t["qty"], t["price"],
                  t["time"], END, sys_time, END))


def _current(conn, trade_id: str) -> tuple:
    row = conn.execute(f"SELECT {COLS} FROM trades WHERE trade_id = ? AND sys_to = ?",
                       (trade_id, END)).fetchone()
    if row is None:
        raise KeyError(trade_id)
    return row


def correct(conn, trade_id: str, changes: dict, sys_time: int) -> None:
    """Close what we believed and record what we now believe; nothing is updated in place
    except the closing of the old version's system time."""
    old = dict(zip(COLS.split(", "), _current(conn, trade_id), strict=True))
    conn.execute("UPDATE trades SET sys_to = ? WHERE trade_id = ? AND sys_to = ?",
                 (sys_time, trade_id, END))
    new = {**old, **changes, "sys_from": sys_time, "sys_to": END}
    conn.execute(f"INSERT INTO trades ({COLS}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                 tuple(new[c] for c in COLS.split(", ")))
    conn.execute("INSERT INTO audit VALUES (?, ?, ?)",
                 (sys_time, trade_id, repr(sorted(changes))))


def cancel(conn, trade_id: str, sys_time: int) -> None:
    """A trade that never happened: its valid time becomes empty."""
    old = dict(zip(COLS.split(", "), _current(conn, trade_id), strict=True))
    correct(conn, trade_id, {"valid_to": old["valid_from"]}, sys_time)


# ------------------------------------------------------------ time travel
AS_OF = f"""SELECT {COLS} FROM trades
WHERE valid_from <= :v AND :v < valid_to AND sys_from <= :s AND :s < sys_to"""

POSITIONS = """SELECT a.name, i.symbol, SUM(t.qty)
FROM trades t JOIN accounts a ON a.id = t.account_id
  JOIN instruments i ON i.id = t.instrument_id
WHERE t.valid_from <= :v AND :v < t.valid_to AND t.sys_from <= :s AND :s < t.sys_to
GROUP BY a.name, i.symbol"""


def as_of(conn, valid: int, system: int) -> list:
    return conn.execute(AS_OF, {"v": valid, "s": system}).fetchall()


def positions(conn, valid: int, system: int) -> dict:
    """Positions from the trades true at `valid`, as the database knew them at `system`."""
    return {(a, s): q for a, s, q in conn.execute(POSITIONS, {"v": valid, "s": system})}


# ------------------------------------------------------------ transactions
def transact(conn, fn, retries: int = 5, wait: float = 0.0):
    """Run fn(conn) in a write transaction taken at BEGIN; retry while another writer
    holds the database."""
    for attempt in range(retries + 1):
        try:
            conn.execute("BEGIN IMMEDIATE")
        except sqlite3.OperationalError as e:
            if "locked" not in str(e) or attempt == retries:
                raise
            time.sleep(wait)
            continue
        try:
            out = fn(conn)
            conn.execute("COMMIT")
            return out
        except BaseException:
            conn.execute("ROLLBACK")
            raise
    raise RuntimeError("unreachable")


# ------------------------------------------------------------ plans and engines
def plan(conn, sql: str, params=()) -> list[str]:
    return [r[-1] for r in conn.execute("EXPLAIN QUERY PLAN " + sql, params)]


def advise(conn, sql: str, params=()) -> list[str]:
    """Tables the plan reads in full (SCAN) rather than through an index (SEARCH)."""
    out = []
    for step in plan(conn, sql, params):
        if step.startswith("SCAN ") and "USING" not in step:
            out.append(step.split()[1])
    return out


def to_duckdb(conn, tables):
    import duckdb
    import pandas as pd
    d = duckdb.connect()
    d.execute("SET threads = 1")
    for t in tables:
        df = pd.read_sql_query(f"SELECT * FROM {t}", conn)   # noqa: F841 - read by DuckDB by name
        d.execute(f"CREATE TABLE {t} AS SELECT * FROM df")
    return d
