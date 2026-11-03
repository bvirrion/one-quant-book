"""A double-entry ledger on SQLite. A transfer is two rows adding to zero, in one commit."""
import sqlite3


def connect(path):
    db = sqlite3.connect(path, isolation_level=None, timeout=30)
    db.executescript("""
        CREATE TABLE IF NOT EXISTS entries(request TEXT, account TEXT, amount INTEGER);
        CREATE TABLE IF NOT EXISTS done(request TEXT PRIMARY KEY, result TEXT);""")
    return db


def balance(db, account):
    return db.execute("SELECT coalesce(sum(amount), 0) FROM entries WHERE account = ?",
                      (account,)).fetchone()[0]


def transfer(db, request, source, target, amount, fail_after_first=False):
    if amount <= 0:
        raise ValueError("the amount must be positive")
    db.execute("BEGIN IMMEDIATE")            # one writer at a time, from the first read on
    try:
        row = db.execute("SELECT result FROM done WHERE request = ?", (request,)).fetchone()
        if row:
            db.execute("COMMIT")
            return row[0]
        result = "ok" if balance(db, source) >= amount else "insufficient"
        if result == "ok":
            db.execute("INSERT INTO entries VALUES (?, ?, ?)", (request, source, -amount))
            if fail_after_first:
                raise RuntimeError("crash")
            db.execute("INSERT INTO entries VALUES (?, ?, ?)", (request, target, amount))
        db.execute("INSERT INTO done VALUES (?, ?)", (request, result))
        db.execute("COMMIT")
        return result
    except BaseException:
        db.execute("ROLLBACK")
        raise
