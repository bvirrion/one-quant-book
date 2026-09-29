"""firm.tsbench -- a benchmark of market-data query shapes across engines (build of One Quant Book 15, chapter 5).

One dataset (quotes and trades as Arrow tables), five query shapes, five engines. Every engine's answer to each query is
checked against the others' before anything is timed; timings are interleaved (every engine once per round, rounds
repeated) so that a drift of the machine hits all engines alike; each engine's first run on a fresh instance is kept
apart as the cold run.

Query shapes (params fixed per dataset):
    point     the last quote of one symbol at or before one time
    range     every quote of one symbol in a one-hour window of one day
    bars      one-minute bars (last mid, count) of one symbol over one day
    asof      every trade of one day with its symbol's prevailing quote (last quote at or before it)
    xsection  the mean quoted spread of every symbol over the whole dataset

Engines: 'duckdb' (embedded, over Parquet partitioned by date and sorted by symbol and time), 'polars' (lazy scan of the
same files), 'sqlite' (embedded row store, a table with an index on (symbol, ts)), 'pandas' (in memory, eager),
'numpy' (the flat, sorted arrays with a per-symbol offset index, a hand-written engine).

API (stable):
    QUERIES; ENGINES
    Params(symbol, date, t0, t1, point_t)
    write_dataset(quotes, trades, root) -> None           Parquet partitions for the file-based engines
    make_engine(name, quotes, trades, root) -> Engine     .run(query, params) -> list of tuples (sorted, rounded)
    check(engines, params) -> dict[query, bool]           every engine gives the same answer
    bench(engines, params, rounds=5) -> list[dict]        {engine, query, cold, median, spread}
"""
from __future__ import annotations

import pathlib
import sqlite3
import statistics
import time
from dataclasses import dataclass

import duckdb
import numpy as np
import pandas as pd
import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq

QUERIES = ("point", "range", "bars", "asof", "xsection")
ENGINES = ("duckdb", "polars", "sqlite", "pandas", "numpy")
MIN_NS = 60 * 10**9


@dataclass(frozen=True)
class Params:
    symbol: str
    date: int            # trading-day index
    t0: int              # window start, ns
    t1: int              # window end, ns (exclusive)
    point_t: int         # time of the point lookup, ns


def _r(x):
    return round(float(x), 6) if isinstance(x, float | np.floating) else (int(x) if isinstance(x, np.integer) else x)


def _rows(it) -> list[tuple]:
    return sorted(tuple(_r(v) for v in row) for row in it)


def write_dataset(quotes: pa.Table, trades: pa.Table, root) -> None:
    root = pathlib.Path(root)
    for name, t in (("quotes", quotes), ("trades", trades)):
        for d in sorted(set(t["date"].to_pylist())):
            part = t.filter(pa.compute.equal(t["date"], d)).sort_by([("symbol", "ascending"), ("ts", "ascending")])
            out = root / name / f"date={d}"
            out.mkdir(parents=True, exist_ok=True)
            pq.write_table(part.drop_columns(["date"]), out / "part.parquet", row_group_size=16_384,
                           compression="zstd")


# ------------------------------------------------------------------------------------------- engines
class DuckEngine:
    name = "duckdb"

    def __init__(self, root):
        self.con = duckdb.connect()
        for t in ("quotes", "trades"):
            files = f"{root}/{t}/date=*/part.parquet"
            self.con.execute(f"CREATE VIEW {t} AS SELECT * FROM "
                             f"read_parquet('{files}', hive_partitioning = true)")

    def run(self, q: str, p: Params):
        one = f"symbol = '{p.symbol}' AND date = {p.date}"
        sql = {
            "point": f"SELECT bid, ask FROM quotes WHERE {one} "
                     f"AND ts <= {p.point_t} ORDER BY ts DESC LIMIT 1",
            "range": f"SELECT ts, bid, ask FROM quotes WHERE {one} "
                     f"AND ts >= {p.t0} AND ts < {p.t1}",
            "bars": f"SELECT ts // {MIN_NS} AS m, arg_max((bid + ask) / 2.0, ts), count(*) "
                    f"FROM quotes WHERE {one} GROUP BY m",
            "asof": f"SELECT t.symbol, t.ts, t.price, q.bid, q.ask "
                    f"FROM (SELECT * FROM trades WHERE date = {p.date}) t "
                    f"ASOF LEFT JOIN (SELECT * FROM quotes WHERE date = {p.date}) q "
                    f"ON t.symbol = q.symbol AND t.ts >= q.ts",
            "xsection": "SELECT symbol, avg(ask - bid) FROM quotes GROUP BY symbol",
        }[q]
        return _rows(self.con.execute(sql).fetchall())


class PolarsEngine:
    name = "polars"

    def __init__(self, root):
        self.q = pl.scan_parquet(f"{root}/quotes/date=*/part.parquet", hive_partitioning=True)
        self.t = pl.scan_parquet(f"{root}/trades/date=*/part.parquet", hive_partitioning=True)

    def run(self, q: str, p: Params):
        c = pl.col
        day = self.q.filter(c("date") == p.date)
        one = day.filter(c("symbol") == p.symbol)
        if q == "point":
            r = one.filter(c("ts") <= p.point_t).sort("ts").tail(1).select("bid", "ask")
        elif q == "range":
            r = one.filter((c("ts") >= p.t0) & (c("ts") < p.t1)).select("ts", "bid", "ask")
        elif q == "bars":
            r = (one.sort("ts").with_columns((c("ts") // MIN_NS).alias("m"), ((c("bid") + c("ask")) / 2.0).alias("mid"))
                 .group_by("m").agg(c("mid").last(), pl.len()))
        elif q == "asof":
            tr = self.t.filter(c("date") == p.date).sort("ts")
            r = (tr.join_asof(day.sort("ts").select("symbol", "ts", "bid", "ask"), on="ts", by="symbol",
                              check_sortedness=False).select("symbol", "ts", "price", "bid", "ask"))
        else:
            r = self.q.group_by("symbol").agg((c("ask") - c("bid")).mean())
        return _rows(r.collect().iter_rows())


class SqliteEngine:
    name = "sqlite"

    def __init__(self, quotes: pa.Table, trades: pa.Table):
        self.con = sqlite3.connect(":memory:")
        self.con.execute("CREATE TABLE quotes (date INT, symbol TEXT, ts INT, bid INT, ask INT)")
        self.con.execute("CREATE TABLE trades (date INT, symbol TEXT, ts INT, price INT)")
        qd, td = quotes.to_pydict(), trades.to_pydict()
        self.con.executemany("INSERT INTO quotes VALUES (?,?,?,?,?)",
                             zip(qd["date"], qd["symbol"], qd["ts"], qd["bid"], qd["ask"], strict=True))
        self.con.executemany("INSERT INTO trades VALUES (?,?,?,?)",
                             zip(td["date"], td["symbol"], td["ts"], td["price"], strict=True))
        self.con.execute("CREATE INDEX q_sym_ts ON quotes (symbol, ts)")
        self.con.commit()

    def run(self, q: str, p: Params):
        sql = {
            "point": f"SELECT bid, ask FROM quotes WHERE symbol = '{p.symbol}' AND ts <= {p.point_t} "
                     f"ORDER BY ts DESC LIMIT 1",
            "range": f"SELECT ts, bid, ask FROM quotes WHERE symbol = '{p.symbol}' AND ts >= {p.t0} AND ts < {p.t1}",
            "bars": f"SELECT ts / {MIN_NS} AS m, (SELECT (q2.bid + q2.ask) / 2.0 FROM quotes q2 WHERE q2.symbol = "
                    f"'{p.symbol}' AND q2.ts >= (q.ts / {MIN_NS}) * {MIN_NS} AND q2.ts < (q.ts / {MIN_NS} + 1) * "
                    f"{MIN_NS} ORDER BY q2.ts DESC LIMIT 1), count(*) "
                    f"FROM quotes q WHERE symbol = '{p.symbol}' AND date = {p.date} GROUP BY m",
            "asof": f"SELECT t.symbol, t.ts, t.price, (SELECT bid FROM quotes q WHERE q.symbol = t.symbol AND "
                    f"q.date = {p.date} AND q.ts <= t.ts ORDER BY q.ts DESC LIMIT 1), (SELECT ask FROM quotes q WHERE "
                    f"q.symbol = t.symbol AND q.date = {p.date} AND q.ts <= t.ts ORDER BY q.ts DESC LIMIT 1) "
                    f"FROM trades t WHERE t.date = {p.date}",
            "xsection": "SELECT symbol, avg(ask - bid) FROM quotes GROUP BY symbol",
        }[q]
        return _rows(self.con.execute(sql).fetchall())


class PandasEngine:
    name = "pandas"

    def __init__(self, quotes: pa.Table, trades: pa.Table):
        self.q = quotes.to_pandas().sort_values(["symbol", "ts"], kind="stable").reset_index(drop=True)
        self.t = trades.to_pandas()

    def run(self, q: str, p: Params):
        d = self.q
        one = d[(d["symbol"] == p.symbol) & (d["date"] == p.date)]
        if q == "point":
            r = one[one["ts"] <= p.point_t].tail(1)[["bid", "ask"]]
        elif q == "range":
            r = one[(one["ts"] >= p.t0) & (one["ts"] < p.t1)][["ts", "bid", "ask"]]
        elif q == "bars":
            g = one.assign(m=one["ts"] // MIN_NS, mid=(one["bid"] + one["ask"]) / 2.0).groupby("m")
            r = pd.DataFrame({"mid": g["mid"].last(), "n": g.size()}).reset_index()
        elif q == "asof":
            tr = self.t[self.t["date"] == p.date].sort_values("ts")
            qu = d[d["date"] == p.date].sort_values("ts")[["symbol", "ts", "bid", "ask"]]
            r = pd.merge_asof(tr, qu, on="ts", by="symbol")[["symbol", "ts", "price", "bid", "ask"]]
        else:
            r = d.assign(s=d["ask"] - d["bid"]).groupby("symbol")["s"].mean().reset_index()
        return _rows(r.itertuples(index=False))


class NumpyEngine:
    """Hand-written: arrays sorted by (symbol, ts), and the first row of each symbol."""
    name = "numpy"

    def __init__(self, quotes: pa.Table, trades: pa.Table):
        q = quotes.sort_by([("symbol", "ascending"), ("ts", "ascending")])
        self.sym = q["symbol"].to_numpy(zero_copy_only=False).astype(str)
        self.date, self.ts = q["date"].to_numpy(), q["ts"].to_numpy()
        self.bid, self.ask = q["bid"].to_numpy(), q["ask"].to_numpy()
        names, first = np.unique(self.sym, return_index=True)
        self.span = {n: (int(f), int(f2)) for n, f, f2 in zip(names, first, list(first[1:]) + [len(self.sym)],
                                                            strict=True)}
        self.t = trades.to_pandas()

    def _day(self, sym, date):
        a, b = self.span[sym]
        lo = a + np.searchsorted(self.date[a:b], date, "left")
        hi = a + np.searchsorted(self.date[a:b], date, "right")
        return lo, hi

    def run(self, q: str, p: Params):
        if q in ("point", "range", "bars"):
            lo, hi = self._day(p.symbol, p.date)
            ts = self.ts[lo:hi]
            if q == "point":
                i = lo + np.searchsorted(ts, p.point_t, "right") - 1
                return _rows([(self.bid[i], self.ask[i])])
            if q == "range":
                i, j = lo + np.searchsorted(ts, p.t0), lo + np.searchsorted(ts, p.t1)
                return _rows(zip(self.ts[i:j], self.bid[i:j], self.ask[i:j], strict=True))
            m = ts // MIN_NS
            last = np.r_[m[1:] != m[:-1], True]
            starts = np.r_[True, m[1:] != m[:-1]]
            counts = np.diff(np.r_[np.flatnonzero(starts), len(m)])
            mid = (self.bid[lo:hi] + self.ask[lo:hi]) / 2.0
            return _rows(zip(m[last], mid[last], counts, strict=True))
        if q == "asof":
            tr = self.t[self.t["date"] == p.date]
            out = []
            for s, g in tr.groupby("symbol"):
                lo, hi = self._day(s, p.date)
                i = lo + np.searchsorted(self.ts[lo:hi], g["ts"].to_numpy(), "right") - 1
                ok = i >= lo
                for k, (tt, pr) in enumerate(zip(g["ts"], g["price"], strict=True)):
                    out.append((s, tt, pr, self.bid[i[k]] if ok[k] else None, self.ask[i[k]] if ok[k] else None))
            return _rows(out)
        return _rows((s, float((self.ask[a:b] - self.bid[a:b]).mean())) for s, (a, b) in self.span.items())


def make_engine(name: str, quotes: pa.Table, trades: pa.Table, root):
    if name == "duckdb":
        return DuckEngine(root)
    if name == "polars":
        return PolarsEngine(root)
    return {"sqlite": SqliteEngine, "pandas": PandasEngine, "numpy": NumpyEngine}[name](quotes, trades)


def check(engines: dict, p: Params) -> dict[str, bool]:
    out = {}
    for q in QUERIES:
        answers = [e.run(q, p) for e in engines.values()]
        out[q] = all(a == answers[0] for a in answers[1:]) and len(answers[0]) > 0
    return out


def bench(factory, p: Params, rounds=5, engines=ENGINES, queries=QUERIES) -> list[dict]:
    """factory(name) builds a fresh engine; its first run of each query is the cold one.
    Warm runs are interleaved: in each round every engine runs every query once."""
    live, cold = {}, {}
    for name in engines:
        live[name] = factory(name)
        for q in queries:
            t = time.perf_counter()
            live[name].run(q, p)
            cold[(name, q)] = time.perf_counter() - t
    warm = {k: [] for k in cold}
    for _ in range(rounds):
        for q in queries:
            for name in engines:
                t = time.perf_counter()
                live[name].run(q, p)
                warm[(name, q)].append(time.perf_counter() - t)
    return [{"engine": n, "query": q, "cold": cold[(n, q)],
             "median": statistics.median(warm[(n, q)]),
             "spread": max(warm[(n, q)]) - min(warm[(n, q)])} for n, q in cold]
