"""firm.marketdf -- market-data idioms with one contract and three engines (build of One Quant Book 15, chapter 10).

Each idiom is written for pandas (eager), Polars (lazy, collected) and DuckDB (SQL), and the three must return the same
rows. The conventions are explicit arguments, never engine defaults: a bar is identified by its left or its right edge,
an interval is closed on the left or on the right, empty bars are dropped or filled. Times are integer nanoseconds;
prices are integers in 1/10,000; volumes are integers; trades at the same time are ordered by their column seq.

Conventions of bars(ticks, width, label, closed, fill):
    closed='left'   a trade at t belongs to the bar [k w, (k+1) w)    -> k = floor(t / w)
    closed='right'  a trade at t belongs to the bar (k w, (k+1) w]    -> k = ceil(t / w) - 1 = floor((t - 1) / w)
    label='left'    the bar is named by its left edge k w; label='right' by its right edge (k+1) w
    fill=False      only bars with trades; fill=True every bar between each symbol's first and last, empty ones with
                    zero volume and the previous close as open, high, low and close

API (stable):
    ENGINES = ('pandas', 'polars', 'duckdb')
    bars(ticks, width, label='left', closed='left', fill=False, engine='pandas') -> pandas.DataFrame
        columns symbol, bar, open, high, low, close, volume, trades (sorted by symbol, bar)
    asof(left, right, by='symbol', on='ts', engine='pandas', strict=False) -> left with right's other columns
    rolling_mean(df, by, order, column, window, engine='pandas') -> Series (mean of the last `window` rows per group)
    xs_rank(df, time, column, engine='pandas') -> Series (rank within each time, 1 = smallest, average for ties)
    to_wide(df, index, columns, values) / to_long(wide, index, columns, values) -> DataFrame (pandas; the pivot)
"""
from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd
import polars as pl

ENGINES = ("pandas", "polars", "duckdb")
COLS = ["symbol", "bar", "open", "high", "low", "close", "volume", "trades"]


def _bucket_pd(t: pd.Series, width: int, closed: str) -> pd.Series:
    return t // width if closed == "left" else (t - 1) // width      # integer times: ceil(t / w) - 1


def _fill(b: pd.DataFrame, width: int) -> pd.DataFrame:
    out = []
    for sym, g in b.groupby("symbol", sort=True):
        full = pd.DataFrame({"bar": np.arange(g["bar"].min(), g["bar"].max() + width, width)})
        g = full.merge(g, on="bar", how="left")
        g["symbol"] = sym
        g["close"] = g["close"].ffill()
        for c in ("open", "high", "low"):
            g[c] = g[c].fillna(g["close"])
        g[["volume", "trades"]] = g[["volume", "trades"]].fillna(0)
        out.append(g)
    b = pd.concat(out, ignore_index=True)
    return b.astype({c: "int64" for c in COLS[2:]})


def bars(ticks: pd.DataFrame, width: int, label: str = "left", closed: str = "left",
         fill: bool = False, engine: str = "pandas") -> pd.DataFrame:
    shift = width if label == "right" else 0
    if engine == "pandas":
        t = ticks.sort_values(["symbol", "ts", "seq"], kind="stable")
        k = _bucket_pd(t["ts"], width, closed)
        g = t.assign(bar=k * width + shift).groupby(["symbol", "bar"], sort=True)
        b = g.agg(open=("price", "first"), high=("price", "max"), low=("price", "min"),
                  close=("price", "last"), volume=("qty", "sum"), trades=("qty", "size"))
        b = b.reset_index()
    elif engine == "polars":
        c = pl.col
        k = (c("ts") // width) if closed == "left" else ((c("ts") - 1) // width)
        b = (pl.from_pandas(ticks).lazy().sort(["symbol", "ts", "seq"], maintain_order=True)
             .with_columns((k * width + shift).alias("bar"))
             .group_by(["symbol", "bar"], maintain_order=True)
             .agg(c("price").first().alias("open"), c("price").max().alias("high"),
                  c("price").min().alias("low"), c("price").last().alias("close"),
                  c("qty").sum().alias("volume"), pl.len().alias("trades"))
             .sort(["symbol", "bar"]).collect().to_pandas())
    elif engine == "duckdb":
        x = "ts" if closed == "left" else "(ts - 1)"   # floor division, whatever `//` does
        k = f"(({x} - ((({x}) % {width}) + {width}) % {width}) // {width})"
        con = duckdb.connect()
        con.register("ticks", ticks)
        b = con.execute(f"""
            SELECT symbol, {k} * {width} + {shift} AS bar,
                   first(price ORDER BY ts, seq) AS open, max(price) AS high,
                   min(price) AS low, last(price ORDER BY ts, seq) AS close,
                   sum(qty) AS volume, count(*) AS trades
            FROM ticks GROUP BY ALL ORDER BY symbol, bar""").df()
    else:
        raise ValueError(engine)
    b = b[COLS].astype({c: "int64" for c in COLS[1:]}).reset_index(drop=True)
    return _fill(b, width) if fill else b


def asof(left: pd.DataFrame, right: pd.DataFrame, by: str = "symbol", on: str = "ts", engine: str = "pandas",
         strict: bool = False) -> pd.DataFrame:
    """Each left row with the last right row of the same group at or before it (strictly before if strict)."""
    if engine == "pandas":
        out = pd.merge_asof(left.sort_values(on), right.sort_values(on), on=on, by=by,
                            allow_exact_matches=not strict)
    elif engine == "polars":
        out = (pl.from_pandas(left).sort(on).join_asof(pl.from_pandas(right).sort(on), on=on, by=by,
                                                         strategy="backward", allow_exact_matches=not strict,
                                                         check_sortedness=False).to_pandas())
    elif engine == "duckdb":
        con = duckdb.connect()
        con.register("l", left)
        con.register("r", right)
        rest = [c for c in right.columns if c not in (by, on)]
        sel = ", ".join(f"r.{c}" for c in rest)
        op = ">" if strict else ">="
        out = con.execute(f"SELECT l.*, {sel} FROM l ASOF LEFT JOIN r ON l.{by} = r.{by} AND l.{on} {op} r.{on}").df()
    else:
        raise ValueError(engine)
    return out.sort_values([by, on], kind="stable").reset_index(drop=True)


def rolling_mean(df: pd.DataFrame, by: str, order: str, column: str, window: int, engine: str = "pandas") -> pd.Series:
    d = df.sort_values([by, order], kind="stable").reset_index(drop=True)
    if engine == "pandas":
        r = d.groupby(by)[column].transform(lambda s: s.rolling(window, min_periods=1).mean())
    elif engine == "polars":
        r = (pl.from_pandas(d).select(pl.col(column).rolling_mean(window, min_samples=1).over(by))
             .to_series().to_pandas())
    elif engine == "duckdb":
        con = duckdb.connect()
        con.register("d", d.assign(_i=np.arange(len(d))))
        r = con.execute(f"""SELECT avg({column}) OVER (PARTITION BY {by} ORDER BY {order}, _i
                            ROWS BETWEEN {window - 1} PRECEDING AND CURRENT ROW) AS m FROM d ORDER BY _i""").df()["m"]
    else:
        raise ValueError(engine)
    return pd.Series(np.asarray(r, dtype=float), name=f"{column}_mean{window}")


def xs_rank(df: pd.DataFrame, time: str, column: str, engine: str = "pandas") -> pd.Series:
    """Rank of each row's value among the rows of the same time (average rank for ties), in the input order."""
    if engine == "pandas":
        r = df.groupby(time)[column].rank(method="average")
    elif engine == "polars":
        r = pl.from_pandas(df).select(pl.col(column).rank("average").over(time)).to_series().to_pandas()
    elif engine == "duckdb":
        con = duckdb.connect()
        con.register("d", df.assign(_i=np.arange(len(df))))
        r = con.execute(f"""SELECT (2 * rank() OVER w + count(*) OVER (PARTITION BY {time}, {column}) - 1) / 2.0 AS r
                            FROM d WINDOW w AS (PARTITION BY {time} ORDER BY {column}) ORDER BY _i""").df()["r"]
    else:
        raise ValueError(engine)
    return pd.Series(np.asarray(r, dtype=float), name=f"{column}_rank")


def to_wide(df: pd.DataFrame, index: str, columns: str, values: str) -> pd.DataFrame:
    return df.pivot(index=index, columns=columns, values=values).sort_index()


def to_long(wide: pd.DataFrame, index: str, columns: str, values: str) -> pd.DataFrame:
    out = wide.reset_index().melt(id_vars=index, var_name=columns, value_name=values)
    return out.dropna(subset=[values]).sort_values([index, columns]).reset_index(drop=True)
