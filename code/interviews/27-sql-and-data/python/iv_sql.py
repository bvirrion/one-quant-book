"""Book 18, chapter 27: fixtures with planted ties and NULLs, a runner for the chapter's .sql files on DuckDB and
SQLite, and pandas / Polars / numpy reference answers."""
import pathlib
import sqlite3

import duckdb
import numpy as np
import pandas as pd

SQL = pathlib.Path(__file__).resolve().parents[1] / "sql"


def fixtures(seed: int = 27):
    rng = np.random.default_rng(seed)
    syms = ["AAA", "BBB", "CCC"]
    n = 60
    trades = pd.DataFrame({
        "ts": np.sort(rng.choice(np.arange(1, 1200), n, replace=False)),
        "sym": rng.choice(syms, n),
        "px": np.round(100 + rng.normal(0, 1, n), 2),
        "qty": rng.integers(1, 20, n) * 100,
        "account": rng.choice(["A1", "A2", "A3", "X9"], n, p=[0.35, 0.35, 0.25, 0.05]),
    })
    trades.loc[[3, 17], "qty"] = None  # two trades with an unknown quantity
    planted = pd.DataFrame({"ts": [125], "sym": ["AAA"], "px": [100.43], "qty": [500], "account": ["A3"]})
    trades = pd.concat([trades, planted], ignore_index=True).sort_values("ts", kind="stable").reset_index(drop=True)
    trades["qty"] = trades["qty"].astype("Int64")
    q = []
    for s in syms:
        ts = np.sort(rng.choice(np.arange(0, 1200), 80, replace=False))
        mid = 100 + np.cumsum(rng.normal(0, 0.1, 80))
        q.append(pd.DataFrame({"ts": ts, "sym": s, "bid": np.round(mid - 0.01, 2), "ask": np.round(mid + 0.01, 2)}))
    quotes = pd.concat(q, ignore_index=True)
    # planted tie: a second quote with the same (sym, ts) as the first quote of AAA, and one exactly at a trade time
    tie = quotes[quotes["sym"] == "AAA"].iloc[[5]].copy()
    tie["bid"] += 0.05
    tie["ask"] += 0.05
    quotes = pd.concat([quotes, tie], ignore_index=True)
    quotes = quotes.sort_values(["sym", "ts"], kind="stable").reset_index(drop=True)
    accounts = pd.DataFrame({"account": ["A1", "A2", "A3"], "desk": ["delta1", "delta1", "vol"]})
    days = np.arange(1, 41)
    pnl = pd.DataFrame({
        "day": np.tile(days, 2),
        "account": np.repeat(["A1", "A2"], 40),
        "pnl": np.round(np.concatenate([rng.normal(0.5, 3, 40), rng.normal(-0.2, 3, 40)]), 1),
    })
    status = pd.DataFrame({
        "ts": [0, 100, 160, 400, 470, 900, 0, 300, 360],
        "sym": ["AAA"] * 6 + ["BBB"] * 3,
        "state": ["OPEN", "HALTED", "OPEN", "HALTED", "OPEN", "OPEN", "OPEN", "HALTED", "OPEN"],
    })
    return {"trades": trades, "quotes": quotes, "accounts": accounts, "pnl": pnl, "status": status}


def run_duckdb(name, tables):
    con = duckdb.connect()
    for k, v in tables.items():
        con.register(k, v)
    return con.execute((SQL / f"{name}.sql").read_text()).df()


def run_sqlite(name, tables):
    con = sqlite3.connect(":memory:")
    for k, v in tables.items():
        v.astype(object).where(v.notna(), None).to_sql(k, con, index=False)
    return pd.read_sql_query((SQL / f"{name}.sql").read_text(), con)


def asof_numpy(trades, quotes):
    """Last quote at or before each trade, per symbol, by searchsorted (ties: the last of equal timestamps)."""
    out = []
    for _, t in trades.iterrows():
        q = quotes[quotes["sym"] == t["sym"]]
        i = np.searchsorted(q["ts"].to_numpy(), t["ts"], side="right") - 1
        out.append(np.nan if i < 0 else q["bid"].to_numpy()[i])
    return np.array(out)


def asof_pandas(trades, quotes):
    """pandas merge_asof: both frames sorted by time; `by` matches the symbol; backward search."""
    t = trades.sort_values("ts", kind="stable")
    q = quotes.sort_values("ts", kind="stable")
    return pd.merge_asof(t, q[["ts", "sym", "bid"]], on="ts", by="sym", direction="backward")


def asof_polars(trades, quotes):
    import polars as pl

    t = pl.from_pandas(trades.astype({"qty": "float64"})).sort("ts")
    q = pl.from_pandas(quotes[["ts", "sym", "bid"]]).sort("ts")
    return t.join_asof(q, on="ts", by="sym", strategy="backward", check_sortedness=False).to_pandas()
