"""SQL and Data: every printed query runs on SQLite and on DuckDB, on the very tables and results printed in the book.

The tables are read out of the LaTeX of the stem, and each result table out of the LaTeX of the answer, so that what is
printed is what was run. A query that belongs to one dialect runs on that one, and the other dialect's failure is asserted.
PostgreSQL is not available here: claims about it rest on the ledger.
"""
import pathlib
import random
import re
import sqlite3

import duckdb
import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
SQL = HERE / "sql"
PARTS = HERE.parents[2] / "parts" / "interviews-3"
CHAPTER = (PARTS / "07-sql-and-data.tex").read_text(encoding="utf-8")
ANSWERS = (PARTS / "solutions" / "07-sql-and-data.tex").read_text(encoding="utf-8")

NONNUMERIC = {}

TRADES = "symbol TEXT, day TEXT, price DOUBLE, qty BIGINT"


def stem(n):
    return re.search(rf"\\label\{{iq:iv3:sql-and-data:{n}\}}(.*?)\\end\{{question\}}", CHAPTER, re.S).group(1)


def answer(n):
    return re.search(rf"\\begin\{{solution\}}\{{iq:iv3:sql-and-data:{n}\}}(.*?)\\end\{{solution\}}", ANSWERS, re.S).group(1)


def cells(text):
    """Every tabular in the text: a list of rows of cell strings, the header row first."""
    out = []
    for body in re.findall(r"\\begin\{tabular\}\{[^}]*\}(.*?)\\end\{tabular\}", text, re.S):
        rows = []
        for line in body.replace(r"\hline", "").split(r"\\"):
            if line.strip():
                rows.append([c.strip().replace(r"\_", "_").replace("$", "") for c in line.split("&")])
        out.append(rows)
    return out


def typed(rows, decl):
    kinds = [d.split()[1] for d in decl.split(", ")]
    assert [d.split()[0] for d in decl.split(", ")] == rows[0], (decl, rows[0])
    out = []
    for row in rows[1:]:
        conv = []
        for cell, kind in zip(row, kinds, strict=True):
            if cell == "NULL":
                conv.append(None)
            elif kind == "BIGINT":
                conv.append(int(cell))
            elif kind == "DOUBLE":
                conv.append(float(cell))
            else:
                conv.append(cell)
        out.append(tuple(conv))
    return out


def engines(*tables):
    """Two connections holding the tables: tables are (name, declaration, rows)."""
    lite, duck = sqlite3.connect(":memory:"), duckdb.connect(":memory:")
    for con in (lite, duck):
        for name, decl, rows in tables:
            con.execute(f"CREATE TABLE {name} ({decl})")
            if rows:
                marks = ", ".join("?" * len(rows[0]))
                con.executemany(f"INSERT INTO {name} VALUES ({marks})", rows)
    return {"sqlite": lite, "duckdb": duck}


def statements(name):
    text = (SQL / f"{name}.sql").read_text(encoding="utf-8")
    text = re.sub(r"--.*", "", text)
    return [s.strip() for s in text.split(";") if s.strip()]


def query(name, part=0):
    return statements(name)[part]


def norm(rows):
    return [tuple(float(v) if isinstance(v, float) or type(v).__name__ == "Decimal" else v for v in r) for r in rows]


def same(rows_a, rows_b):
    assert len(rows_a) == len(rows_b), (rows_a, rows_b)
    for a, b in zip(rows_a, rows_b, strict=True):
        assert len(a) == len(b), (a, b)
        for x, y in zip(a, b, strict=True):
            if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                assert x == pytest.approx(y, abs=1e-9), (rows_a, rows_b)
            else:
                assert x == y, (rows_a, rows_b)


def both(cons, sql):
    """Run on both engines, check they agree, and return the rows."""
    a = norm(cons["sqlite"].execute(sql).fetchall())
    b = norm(cons["duckdb"].execute(sql).fetchall())
    same(a, b)
    return a


def printed(rows_printed, rows):
    """A printed result table against the rows: numbers to the printed number of decimals."""
    body = rows_printed[1:]
    assert len(body) == len(rows), (body, rows)
    for line, row in zip(body, rows, strict=True):
        assert len(line) == len(row), (line, row)
        for cell, v in zip(line, row, strict=True):
            if v is None:
                assert cell == "NULL", (line, row)
            elif isinstance(v, (int, float)):
                decimals = len(cell.split(".")[1]) if "." in cell else 0
                assert abs(float(cell) - float(v)) <= 0.5 * 10**-decimals + 1e-12, (line, row)
            else:
                assert cell == str(v), (line, row)


def test_q1():
    t = cells(stem(1))[0]
    c = engines(("trades", TRADES, typed(t, TRADES)))
    r = both(c, query("vwap"))
    assert r == [("AAA", "2026-03-02", 100.75)]
    printed(cells(answer(1))[0], r)
    assert both(c, "SELECT AVG(price) FROM trades WHERE symbol = 'AAA' AND day = '2026-03-02'") == [(101.0,)]
    bad = "SELECT symbol FROM trades WHERE COUNT(*) > 2 GROUP BY symbol"
    with pytest.raises(sqlite3.Error):
        c["sqlite"].execute(bad)
    with pytest.raises(duckdb.Error):
        c["duckdb"].execute(bad)
    # a symbol-day whose quantities sum to zero: NULLIF gives NULL everywhere, where a bare division differs by engine
    assert both(c, "SELECT 1.0 / NULLIF(0, 0)") == [(None,)]
    assert c["sqlite"].execute("SELECT 1.0 / 0").fetchall() == [(None,)]
    assert c["duckdb"].execute("SELECT CAST(1 AS DOUBLE) / 0").fetchall() == [(float("inf"),)]
    # the stem's own case: a correction at the same price has a zero numerator as well, and at another price a negative one
    same_price = c["duckdb"].execute("SELECT CAST(100 * 5 + 100 * -5 AS DOUBLE) / (5 + -5)").fetchall()[0][0]
    assert same_price != same_price  # NaN
    assert c["duckdb"].execute("SELECT CAST(100 * 5 + 101 * -5 AS DOUBLE) / (5 + -5)").fetchall() == [(float("-inf"),)]
    ticks = "symbol TEXT, day TEXT, price BIGINT, qty BIGINT"
    ints = engines(("trades", ticks, [(s, d, int(p), q) for s, d, p, q in typed(t, TRADES)]))
    assert ints["sqlite"].execute(query("vwap")).fetchall() == [("AAA", "2026-03-02", 100)]


def test_q2():
    a, b = cells(stem(2))
    o, f = "order_id BIGINT, symbol TEXT", "order_id BIGINT, venue TEXT, qty BIGINT"
    c = engines(("orders", o, typed(a, o)), ("fills", f, typed(b, f)))
    assert both(c, query("venue_fills", 0)) == [(1, 100)]
    r = both(c, query("venue_fills", 1) + " ORDER BY o.order_id")
    assert r == [(1, 100), (2, None), (3, None)]
    printed(cells(answer(2))[0], r)
    # patching query A with IS NULL brings back order 3 and still loses order 2, whose only fill is on venue Y
    alt = ("SELECT o.order_id, f.qty FROM orders o LEFT JOIN fills f ON o.order_id = f.order_id "
           "WHERE f.venue = 'X' OR f.venue IS NULL ORDER BY o.order_id")
    assert both(c, alt) == [(1, 100), (3, None)]


def test_q3():
    a, b = cells(stem(3))
    o, bl = "order_id BIGINT, trader TEXT", "trader TEXT"
    c = engines(("orders", o, typed(a, o)), ("blocked", bl, typed(b, bl)))
    assert both(c, query("not_in")) == []
    assert both(c, query("not_exists") + " ORDER BY o.order_id") == [(1,), (3,)]
    filtered = "SELECT order_id FROM orders WHERE trader NOT IN (SELECT trader FROM blocked WHERE trader IS NOT NULL)"
    assert both(c, filtered) == [(1,)]
    assert both(c, "SELECT 'ann' NOT IN ('bob', NULL)") == [(None,)]


def test_q4():
    q = "bid DOUBLE"
    c = engines(("quotes", q, [(10.0,), (None,), (20.0,), (20.0,), (None,)]))
    r = both(c, query("counts", 0))
    same(r, [(5, 3, 2, 50.0, 50 / 3, 10.0)])
    assert both(c, query("counts", 1)) == [(0,)]
    assert both(c, "SELECT COUNT(*) FROM quotes WHERE bid IS NULL") == [(2,)]
    assert re.search(r"5, 3, 2, 50, 16\.67, 10", answer(4))
    assert both(c, "SELECT AVG(COALESCE(bid, 0)) FROM quotes") == [(10.0,)]


def test_q5():
    f = "filled BIGINT, ordered BIGINT"
    c = engines(("fills", f, [(30, 100), (45, 50)]))
    assert c["sqlite"].execute(query("fill_ratio")).fetchall() == [(0,)]
    assert c["duckdb"].execute(query("fill_ratio")).fetchall() == [(0.5,)]
    assert both(c, query("fill_ratio_fixed")) == [(0.5,)]
    assert both(c, "SELECT CAST(SUM(filled) AS DOUBLE) / SUM(ordered) FROM fills") == [(0.5,)]
    assert c["sqlite"].execute("SELECT 7 / 2").fetchall() == [(3,)]
    assert c["duckdb"].execute("SELECT 7 / 2, 7 // 2").fetchall() == [(3.5, 3)]


def test_q6():
    decl = "seq BIGINT, trade_id BIGINT, symbol TEXT, qty BIGINT"
    c = engines(("trades", decl, typed(cells(stem(6))[0], decl)))
    r = both(c, query("duplicates", 0) + " ORDER BY trade_id")
    assert r == [(2, 2, 1), (3, 2, 2)]
    printed(cells(answer(6))[0], r)
    r = both(c, query("duplicates", 1))
    assert r == [("AAA", 300), ("BBB", 130)]
    printed(cells(answer(6))[1], r)
    assert both(c, query("distinct_total")) == [("AAA", 300), ("BBB", 180)]


def test_q7():
    decl = "symbol TEXT, ts BIGINT, price DOUBLE"
    c = engines(("prices", decl, typed(cells(stem(7))[0], decl)))
    lite = c["sqlite"].execute(query("latest_bare") + " ORDER BY symbol").fetchall()
    assert lite == [("AAA", 3, 101.0), ("BBB", 5, 50.0)]
    with pytest.raises(duckdb.BinderException):
        c["duckdb"].execute(query("latest_bare"))
    r = both(c, query("latest_portable"))
    assert r == [("AAA", 3, 101.0), ("BBB", 5, 50.0)]
    printed(cells(answer(7))[0], r)
    assert c["duckdb"].execute("SELECT symbol, arg_max(price, ts) FROM prices GROUP BY symbol ORDER BY symbol").fetchall() == [
        ("AAA", 101.0), ("BBB", 50.0)]
    assert c["duckdb"].execute("SELECT symbol, price FROM prices QUALIFY ROW_NUMBER() OVER "
                               "(PARTITION BY symbol ORDER BY ts DESC) = 1 ORDER BY symbol").fetchall() == [
        ("AAA", 101.0), ("BBB", 50.0)]
    # two aggregates: the row is no longer tied to one extreme, and SQLite's special case does not apply
    assert c["sqlite"].execute("SELECT symbol, MAX(ts), MIN(ts), price FROM prices GROUP BY symbol").fetchall()


def test_q8():
    decl = "desk TEXT, trader TEXT, pnl BIGINT"
    c = engines(("pnl", decl, typed(cells(stem(8))[0], decl)))
    r = both(c, query("ranks"))
    printed(cells(answer(8))[0], r)
    keep = {}
    for k, col in (("row", 3), ("rank", 4), ("dense", 5)):
        keep[k] = {row[1] for row in r if row[col] <= 2}
    assert keep["row"] == {"ann", "bob", "eve", "fay"}
    assert keep["rank"] == {"ann", "bob", "eve", "fay", "gus"}
    assert keep["dense"] == {"ann", "bob", "cid", "eve", "fay", "gus"}


def test_q9():
    decl = "seq BIGINT, ts BIGINT, qty BIGINT"
    c = engines(("fills", decl, typed(cells(stem(9))[0], decl)))
    bad = both(c, query("position"))
    assert [row[3] for row in bad] == [100, 50, 50, 0]
    good = both(c, query("position_fixed"))
    assert [row[3] for row in good] == [100, -50, 50, 0]
    printed(cells(answer(9))[0], [(row[0], b[3], row[3]) for row, b in zip(good, bad, strict=True)])


def test_q10():
    a, b = cells(stem(10))
    o, f = "order_id BIGINT, desk TEXT, qty BIGINT", "order_id BIGINT, filled BIGINT"
    c = engines(("orders", o, typed(a, o)), ("fills", f, typed(b, f)))
    r = both(c, query("fanout"))
    assert r == [("fx", 200, 150), ("rates", 200, 100)]
    printed(cells(answer(10))[0], r)
    r = both(c, query("fanout_fixed"))
    assert r == [("fx", 200, 150), ("rates", 150, 100)]
    printed(cells(answer(10))[1], r)


def test_q11():
    decl = "day BIGINT, price DOUBLE"
    c = engines(("closes", decl, typed(cells(stem(11))[0], decl)))
    r = both(c, query("moving"))
    printed(cells(answer(11))[0], r)
    assert r[3][2] == pytest.approx(110 / 3) and r[3][3] == 60.0 and r[4][3] == 75.0


def test_q12():
    decl = "minute BIGINT, seq BIGINT, price DOUBLE"
    c = engines(("ticks", decl, typed(cells(stem(12))[0], decl)))
    bad = both(c, query("bars_bad"))
    assert len(bad) == 5
    printed(cells(answer(12))[0], bad)
    good = both(c, query("bars_fixed"))
    assert good == [(1, 100.0, 103.0, 100.0, 101.0), (2, 102.0, 102.0, 99.0, 99.0)]
    printed(cells(answer(12))[1], good)
    arg = ("SELECT minute, arg_min(price, seq), MAX(price), MIN(price), arg_max(price, seq) FROM ticks "
           "GROUP BY minute ORDER BY minute")
    assert c["duckdb"].execute(arg).fetchall() == good


def test_q13():
    a, b = cells(stem(13))
    t, q = "trade_id BIGINT, ts BIGINT", "ts BIGINT, bid DOUBLE, ask DOUBLE"
    c = engines(("trades", t, typed(a, t)), ("quotes", q, typed(b, q)))
    r = both(c, query("asof_correlated"))
    assert r == [(1, None, None, None), (2, 3, 99.9, 100.1), (3, 12, 100.4, 100.7), (4, None, None, None)]
    printed(cells(answer(13))[0], r)
    # index or not: SQLite's plan says which, for the correlated part
    plan = lambda con, s: " ".join(str(x[-1]) for x in con.execute("EXPLAIN QUERY PLAN " + s).fetchall())  # noqa: E731
    sub = "SELECT (SELECT MAX(q.ts) FROM quotes q WHERE q.ts <= t.ts AND q.ts >= t.ts - 10) FROM trades t"
    assert "USING" not in plan(c["sqlite"], sub)
    whole = plan(c["sqlite"], query("asof_correlated"))
    assert "SEARCH q USING AUTOMATIC COVERING INDEX (ts=?)" in whole and "CORRELATED SCALAR SUBQUERY 1 SEARCH q " in whole
    c["sqlite"].execute("CREATE INDEX by_ts ON quotes (ts)")
    assert "SEARCH q USING COVERING INDEX by_ts (ts>? AND ts<?)" in plan(c["sqlite"], sub)
    assert both({"sqlite": c["sqlite"], "duckdb": c["duckdb"]}, query("asof_correlated")) == r


def test_q14():
    c = engines(("msgs", "seq BIGINT", [(s,) for s in (1, 2, 3, 6, 7, 11)]))
    r = both(c, query("seq_gaps"))
    assert r == [(4, 5), (8, 10)]
    printed(cells(answer(14))[0], r)
    assert both(c, "SELECT MAX(seq) - MIN(seq) + 1 - COUNT(*) FROM msgs") == [(5,)]
    c2 = engines(("msgs", "seq BIGINT", [(s,) for s in (1, 2, 2, 3, 6)]))
    assert both(c2, query("seq_gaps")) == [(4, 5)]
    assert both(c2, "SELECT MAX(seq) - MIN(seq) + 1 - COUNT(*) FROM msgs") == [(1,)]  # a duplicate hides a hole
    assert both(c2, "SELECT MAX(seq) - MIN(seq) + 1 - COUNT(DISTINCT seq) FROM msgs") == [(2,)]


def test_q15():
    decl = "seq BIGINT, ts BIGINT, bid DOUBLE, ask DOUBLE, bid_size BIGINT"
    c = engines(("quotes", decl, typed(cells(stem(15))[0], decl)))
    r = both(c, query("bad_ticks"))
    assert r == [(3, "crossed"), (4, "size"), (5, "time"), (6, "jump"), (7, "jump")]
    printed(cells(answer(15))[0], r)
    assert c["duckdb"].execute(query("jump_median")).fetchall() == [(6,)]
    with pytest.raises(sqlite3.Error):
        c["sqlite"].execute(query("jump_median"))


def test_q16():
    values = (10, 12, 13, 15, 20, 22, 25, 30, 80, 200)
    c = engines(("latency", "us BIGINT", [(v,) for v in values]))
    disc, cont = c["duckdb"].execute(query("quantile_duckdb")).fetchall()[0]
    assert disc == 80 and cont == pytest.approx(92.0) and repr(cont) == "91.99999999999996"
    assert 80 + 0.1 * (200 - 80) == pytest.approx(92.0) and 0.9 * 9 == pytest.approx(8.1)
    assert both(c, query("nearest_rank")) == [(80,)]
    for fn in ("quantile_cont", "percentile_cont"):
        with pytest.raises(sqlite3.Error):
            c["sqlite"].execute(f"SELECT {fn}(us, 0.9) FROM latency")
    p99 = query("nearest_rank").replace("pos * 10 >= n * 9", "pos * 100 >= n * 99")
    assert both(c, p99) == [(200,)]  # the 99th percentile of ten rows is the maximum
    ties = engines(("latency", "us BIGINT", [(1,), (1,), (1,), (1,)]))
    groups = both(ties, "SELECT NTILE(2) OVER (ORDER BY us) AS g FROM latency ORDER BY g")
    assert [g[0] for g in groups] == [1, 1, 2, 2]  # equal values land in different groups


def test_q17():
    con = sqlite3.connect(":memory:")
    parts = statements("index_plans")
    con.execute(parts[0])
    con.execute(parts[1])
    plans = [" ".join(row[-1] for row in con.execute("EXPLAIN QUERY PLAN " + s).fetchall()) for s in parts[2:]]
    a, b, c, d, e = plans
    assert "SEARCH trades USING INDEX by_symbol_ts (symbol=? AND ts>?)" in a and "TEMP" not in a
    assert b.startswith("SCAN trades")
    assert "SEARCH trades USING INDEX by_symbol_ts (symbol=?)" in c and "TEMP" not in c
    assert "SEARCH trades USING INDEX by_symbol_ts (symbol=?)" in d and "USE TEMP B-TREE FOR ORDER BY" in d
    assert e.startswith("SCAN trades")
    assert "(symbol=? AND ts>?)" in answer(17).replace(r"\_", "_")
    con.execute("CREATE INDEX covering ON trades (symbol, ts, price)")
    assert "COVERING INDEX covering" in " ".join(row[-1] for row in con.execute("EXPLAIN QUERY PLAN " + parts[2]).fetchall())


def test_q18():
    decl = "day BIGINT, pnl BIGINT"
    c = engines(("daily", decl, typed(cells(stem(18))[0], decl)))
    r = both(c, query("islands"))
    assert r == [(6, 8, 3)]
    rng = random.Random(18)
    for _ in range(100):
        days = sorted(rng.sample(range(1, 40), rng.randint(1, 15)))
        rows = [(d, rng.choice([-1, 1])) for d in days]
        if all(p < 0 for _, p in rows):
            continue
        c2 = engines(("daily", decl, rows))
        best, cur = None, []
        for d, p in rows + [(None, -1)]:
            if p > 0:
                cur.append(d)
            else:
                if cur and (best is None or len(cur) > len(best)):
                    best = cur
                cur = []
        assert both(c2, query("islands")) == [(best[0], best[-1], len(best))]


def test_q19():
    decl = "trader TEXT, ts BIGINT"
    c = engines(("events", decl, typed(cells(stem(19))[0], decl)))
    r = both(c, query("sessions"))
    assert r == [("ann", 1, 100, 200, 2), ("ann", 2, 700, 800, 2), ("ann", 3, 1500, 1500, 1), ("bob", 1, 150, 150, 1), ("bob", 2, 460, 760, 2)]
    printed(cells(answer(19))[0], r)
    assert 460 - 150 == 310 and 760 - 460 == 300
    strict = both(c, query("sessions").replace("<= 300", "< 300"))
    assert ("bob", 3, 760, 760, 1) in strict  # the strict test splits the pair exactly 300 apart
    # the wrong answer, ts / 300: same bucket means under 300 apart, so its faults are the two the answer names
    assert 299 // 300 != 300 // 300 and all(a // 300 != b // 300 for a in range(600) for b in range(a + 300, 900))
    long_session = [0, 200, 400, 600]  # gaps of 200: one session, by the rule
    assert len({ts // 300 for ts in long_session}) == 3


def test_q20():
    decl = "day BIGINT, price DOUBLE"
    c = engines(("closes", decl, typed(cells(stem(20))[0], decl)))
    r = both(c, query("ffill"))
    assert r == [(1, None), (2, 10.0), (3, 10.0), (4, 10.0), (5, 12.0), (6, 12.0)]
    printed(cells(answer(20))[0], r)
    assert c["duckdb"].execute(query("ffill_duckdb")).fetchall() == r
    with pytest.raises(sqlite3.Error):
        c["sqlite"].execute(query("ffill_duckdb"))
    lag = both(c, "SELECT day, COALESCE(price, LAG(price) OVER (ORDER BY day)) FROM closes ORDER BY day")
    assert lag[3] == (4, None) and lag[2] == (3, 10.0)
    limit = both(c, query("ffill_limit"))
    assert limit == [(1, None), (2, 10.0), (3, 10.0), (4, None), (5, 12.0), (6, 12.0)]


def asof_brute(trades, quotes):
    out = []
    for s, t in trades:
        best = None
        for qs, qt, mid in quotes:
            if qs == s and qt <= t and (best is None or qt > best[0]):
                best = (qt, mid)
        out.append((s, t, best[1] if best else None))
    return sorted(out, key=lambda r: (r[0], r[1]))


def test_q21():
    a, b = cells(stem(21))
    t, q = "symbol TEXT, ts BIGINT", "symbol TEXT, ts BIGINT, mid DOUBLE"
    rows_t, rows_q = typed(a, t), typed(b, q)
    c = engines(("trades", t, rows_t), ("quotes", q, rows_q))
    r = both(c, query("asof_union"))
    assert r == [("AAA", 5, 100.0), ("AAA", 12, 101.0), ("BBB", 1, None), ("BBB", 7, 50.0)]
    printed(cells(answer(21))[0], r)
    assert c["duckdb"].execute(query("asof_duckdb")).fetchall() == r
    with pytest.raises(sqlite3.Error):
        c["sqlite"].execute(query("asof_duckdb"))
    rng = random.Random(21)
    for _ in range(100):
        tr = [(rng.choice("AB"), rng.randint(0, 20)) for _ in range(rng.randint(1, 12))]
        qt = {}
        for _ in range(rng.randint(0, 12)):  # unique (symbol, ts) among quotes, which the question's tie rule needs
            qt[(rng.choice("AB"), rng.randint(0, 20))] = float(rng.randint(1, 99))
        qu = [(s, ts, m) for (s, ts), m in qt.items()]
        c2 = engines(("trades", t, tr), ("quotes", q, qu))
        want = asof_brute(tr, qu)
        same(sorted(both(c2, query("asof_union")), key=str), sorted(want, key=str))
        same(sorted(norm(c2["duckdb"].execute(query("asof_duckdb")).fetchall()), key=str), sorted(want, key=str))
    # two quotes at one time: each gets its own group, and the row order decides, not the size
    for order, want in (([100.0, 101.0], 101.0), ([101.0, 100.0], 100.0)):
        c3 = engines(("trades", t, [("AAA", 5)]), ("quotes", q, [("AAA", 3, m) for m in order]))
        assert both(c3, query("asof_union")) == [("AAA", 5, want)]
    inner = query("asof_duckdb").replace("ASOF LEFT JOIN", "ASOF JOIN")
    assert ("BBB", 1, None) not in c["duckdb"].execute(inner).fetchall() and len(c["duckdb"].execute(inner).fetchall()) == 3


def test_q22():
    a, b = cells(stem(22))
    m, t = "inst_id BIGINT, ticker TEXT, valid_from TEXT, valid_to TEXT", "ticker TEXT, day TEXT, qty BIGINT"
    c = engines(("master", m, typed(a, m)), ("trades", t, typed(b, t)))
    r = both(c, query("pit_between"))
    assert r == [("XYZ", "2022-07-01", 30, 3), ("XYZ", "2022-07-01", 30, 4), ("ABC", "2024-04-30", 10, 1),
                 ("ABC", "2024-05-01", 20, 1), ("ABC", "2024-05-01", 20, 2)]
    printed(cells(answer(22))[0], r)
    r = both(c, query("pit_fixed"))
    assert r == [("XYZ", "2022-07-01", 30, 3), ("XYZ", "2022-07-01", 30, 4), ("ABC", "2024-04-30", 10, 1), ("ABC", "2024-05-01", 20, 2)]
    assert both(c, query("pit_overlaps")) == [(3, 4, "XYZ")]


def test_q23():
    decl = "ts BIGINT, price DOUBLE, qty BIGINT"
    rows = typed(cells(stem(23))[0], decl)
    c = engines(("trades", decl, rows))
    r = both(c, query("rolling_vwap"))
    want = []
    for ts, _p, _ in sorted(rows, key=lambda x: (x[0], x[1])):
        w = [(a, b) for u, a, b in rows if ts - 300 < u <= ts]
        want.append((ts, sum(a * b for a, b in w) / sum(b for _, b in w)))
    same(r, want)
    printed(cells(answer(23))[0], r)
    assert r[-1][1] == r[-2][1]
    rng = random.Random(23)
    for _ in range(50):
        rs = []
        t0 = 0
        for _ in range(rng.randint(1, 15)):
            t0 += rng.randint(0, 150)
            rs.append((t0, float(rng.randint(90, 110)), rng.randint(1, 9)))
        cx = engines(("trades", decl, rs))
        want = []
        for ts, _p, _ in sorted(rs, key=lambda x: (x[0], x[1])):
            w = [(a, b) for u, a, b in rs if ts - 300 < u <= ts]
            want.append((ts, sum(a * b for a, b in w) / sum(b for _, b in w)))
        got = both(cx, query("rolling_vwap"))
        same(got, want)


def fifo_brute(fills):
    """A queue of open lots, long or short: a fill closes the oldest lots of the other side, then opens the rest."""
    lots, out = [], []
    for seq, side, price, qty in fills:
        left = qty
        while left and lots and lots[0][0] != side:
            take = min(left, lots[0][3])
            buy, sell = ((lots[0][1], lots[0][2]), (seq, price)) if side == "S" else ((seq, price), (lots[0][1], lots[0][2]))
            out.append((buy[0], sell[0], take, (sell[1] - buy[1]) * take))
            lots[0][3] -= take
            left -= take
            if lots[0][3] == 0:
                lots.pop(0)
        if left:
            lots.append([side, seq, price, left])
    return sorted(out, key=lambda r: (r[1], r[0]))


def test_q24():
    decl = "seq BIGINT, side TEXT, price BIGINT, qty BIGINT"
    rows = typed(cells(stem(24))[0], decl)
    c = engines(("fills", decl, rows))
    r = both(c, query("fifo"))
    assert r == [(1, 3, 100, 2000), (2, 3, 20, 200), (2, 5, 30, 600), (4, 5, 30, 1200)]
    printed(cells(answer(24))[0], r)
    assert sum(row[3] for row in r) == 4000
    assert r == fifo_brute(rows)
    rng = random.Random(24)
    for _ in range(150):
        pos, fs = 0, []
        for seq in range(1, rng.randint(2, 15)):
            if pos and rng.random() < 0.5:
                q = rng.randint(1, pos)
                fs.append((seq, "S", rng.randint(90, 110), q))
                pos -= q
            else:
                q = rng.randint(1, 9)
                fs.append((seq, "B", rng.randint(90, 110), q))
                pos += q
        cx = engines(("fills", decl, fs))
        assert both(cx, query("fifo")) == fifo_brute(fs)
    # the position may cross zero: the same query, against a queue that holds long and short lots
    crossed = 0
    for _ in range(150):
        pos, fs = 0, []
        for seq in range(1, rng.randint(2, 15)):
            side, q = rng.choice("BS"), rng.randint(1, 9)
            if (pos > 0 and pos - q < 0 and side == "S") or (pos < 0 and pos + q > 0 and side == "B"):
                crossed += 1
            pos += q if side == "B" else -q
            fs.append((seq, side, rng.randint(90, 110), q))
        cx = engines(("fills", decl, fs))
        assert both(cx, query("fifo")) == fifo_brute(fs)
    assert crossed > 20
    assert both(c, "SELECT CASE WHEN 1 < 2 THEN 1 ELSE 2 END") == [(1,)]
    assert c["sqlite"].execute("SELECT MIN(3, 2)").fetchall() == [(2,)]
    with pytest.raises(sqlite3.Error):
        c["sqlite"].execute("SELECT LEAST(3, 2)")
    assert c["duckdb"].execute("SELECT LEAST(3, 2)").fetchall() == [(2,)]
    assert c["duckdb"].execute("SELECT MIN(3, 2)").fetchall() == [([3],)]  # the smallest 2 values of a column, as a list


def book_brute(events):
    levels, out = {}, []
    for seq, price, delta in events:
        levels[price] = levels.get(price, 0) + delta
        live = [p for p, q in levels.items() if q > 0]
        best = max(live) if live else None
        out.append((seq, best, levels[best] if best is not None else None))
    return out


def test_q25():
    decl = "seq BIGINT, price BIGINT, delta BIGINT"
    rows = typed(cells(stem(25))[0], decl)
    c = engines(("events", decl, rows))
    r = both(c, query("best_bid"))
    assert r == [(1, 100, 50), (2, 101, 20), (3, 101, 20), (4, 100, 80), (5, 100, 80), (6, 99, 40)]
    printed(cells(answer(25))[0], r)
    rng = random.Random(25)
    for _ in range(100):
        levels, ev = {}, []
        for seq in range(1, rng.randint(2, 25)):
            p = rng.randint(95, 100)
            have = levels.get(p, 0)
            d = -rng.randint(1, have) if have and rng.random() < 0.5 else rng.randint(1, 9)
            levels[p] = have + d
            ev.append((seq, p, d))
        cx = engines(("events", decl, ev))
        assert both(cx, query("best_bid")) == book_brute(ev)
    # the cost on SQLite: no index for the inequality, so virtual-machine steps, a count and not a clock, quadruple per doubling
    def steps(n):
        draw = random.Random(250)
        levels, ev = {}, []
        for seq in range(1, n + 1):
            p = draw.randint(100, 104)  # a fixed number of levels, so only n grows
            have = levels.get(p, 0)
            d = -draw.randint(1, have) if have and draw.random() < 0.5 else draw.randint(1, 9)
            levels[p] = have + d
            ev.append((seq, p, d))
        con = sqlite3.connect(":memory:")
        con.execute("CREATE TABLE events (seq BIGINT, price BIGINT, delta BIGINT)")
        con.executemany("INSERT INTO events VALUES (?, ?, ?)", ev)
        ticks = [0]
        def tick():
            ticks[0] += 1
        con.set_progress_handler(tick, 1000)
        con.execute(query("best_bid")).fetchall()
        con.close()
        return ticks[0]
    assert 3.5 < steps(2000) / steps(1000) < 4.5
    # the classic wrong answer: the largest price ever added, which forgets that a level can empty out
    assert both(c, "SELECT MAX(price) FROM events WHERE delta > 0 AND seq <= 4") == [(101,)]
