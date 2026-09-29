"""Acceptance tests of firm.tradedb (One Quant Book 15, chapter 25)."""
import pathlib
import sqlite3
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_tradedb as D  # noqa: E402


def _db(path=":memory:"):
    c = D.connect(path)
    assert D.migrate(c) == 2 and D.migrate(c) == 2                 # applied once
    c.execute("INSERT INTO instruments VALUES (1, 'AAA', 'USD')")
    c.execute("INSERT INTO accounts VALUES (1, 'ACC1')")
    return c


def test_keys_enforced():
    c = _db()
    with pytest.raises(sqlite3.IntegrityError):
        D.book(c, {"trade_id": "X", "account_id": 9, "instrument_id": 1, "qty": 1, "price": 1.0, "time": 0}, 0)
    with pytest.raises(sqlite3.IntegrityError):
        c.execute("INSERT INTO instruments VALUES (2, 'AAA', 'USD')")          # symbol unique


def test_bitemporal_correction_and_time_travel():
    c = _db()
    D.book(c, {"trade_id": "T1", "account_id": 1, "instrument_id": 1, "qty": 700, "price": 10.0, "time": 100}, 105)
    D.book(c, {"trade_id": "T2", "account_id": 1, "instrument_id": 1, "qty": 100, "price": 10.0, "time": 200}, 205)
    D.correct(c, "T1", {"qty": 70}, 1000)
    D.cancel(c, "T2", 1100)
    D.book(c, {"trade_id": "T3", "account_id": 1, "instrument_id": 1, "qty": 5, "price": 10.0, "time": 300}, 1200)
    assert D.positions(c, 500, 500) == {("ACC1", "AAA"): 800}                   # as it stood
    assert D.positions(c, 500, 2000) == {("ACC1", "AAA"): 75}                   # as now known
    assert D.positions(c, 150, 2000) == {("ACC1", "AAA"): 70}
    assert len(D.as_of(c, 500, 1050)) == 2 and c.execute("SELECT COUNT(*) FROM trades").fetchone()[0] == 5
    assert c.execute("SELECT COUNT(*) FROM audit").fetchone()[0] == 2
    with pytest.raises(KeyError):
        D.correct(c, "nope", {"qty": 1}, 3000)


def test_transact_retries_while_locked(tmp_path):
    a, b = _db(str(tmp_path / "x.db")), D.connect(str(tmp_path / "x.db"))
    a.execute("BEGIN IMMEDIATE")
    with pytest.raises(sqlite3.OperationalError):
        D.transact(b, lambda c: c.execute("INSERT INTO accounts VALUES (2, 'B')"), retries=1)
    a.execute("COMMIT")
    D.transact(b, lambda c: c.execute("INSERT INTO accounts VALUES (2, 'B')"))
    with pytest.raises(ZeroDivisionError):                                     # a failing body rolls back
        D.transact(b, lambda c: (c.execute("INSERT INTO accounts VALUES (3, 'C')"), 1 / 0))
    assert a.execute("SELECT COUNT(*) FROM accounts").fetchone()[0] == 2


def test_plan_advise_and_duckdb():
    c = _db()
    for i in range(50):
        D.book(c, {"trade_id": f"T{i}", "account_id": 1, "instrument_id": 1, "qty": i, "price": 1.0, "time": i}, i)
    q = "SELECT SUM(qty) FROM trades WHERE account_id = 1 AND instrument_id = 1"
    assert D.advise(c, q) == ["trades"]
    c.execute("CREATE INDEX ix ON trades (account_id, instrument_id)")
    assert D.advise(c, q) == [] and "USING INDEX ix" in D.plan(c, q)[0]
    d = D.to_duckdb(c, ["trades"])
    assert d.execute(q).fetchone()[0] == c.execute(q).fetchone()[0] == 1225
