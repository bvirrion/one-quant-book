"""Dataframes (One Quant Book 15, chapter 10).

Two studies. Conventions: one symbol-day of trades with timestamps truncated to the second (as vendors may deliver)
is turned into five-minute bars under three conventions (left-labelled and left-closed, right-labelled and right-closed,
and the first with empty bars filled), and the bars' volumes and returns are compared. Engines: one research pipeline
over the chapter 3 month of quotes and a month of trades (fifty symbols, twenty days) -- one-minute bars, bar returns,
their cross-sectional rank in each minute, each symbol's average rank; every trade joined as of the prevailing quote and
each symbol's mean effective spread -- written for pandas (eager, the whole month in memory), Polars (eager, lazy, and
lazy with the streaming engine) and DuckDB (SQL over the files). Each run happens in its own process, which reports its
wall time and peak resident memory; the answers must agree.
"""
from __future__ import annotations

import functools
import json
import pathlib
import shutil
import subprocess
import sys
import time

import duckdb
import numpy as np
import pandas as pd
import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = pathlib.Path(__file__).resolve().parents[4]
for p in ("code/firm/marketdf", "code/firm/tsbench", "code/platforms/03-columnar-formats/python"):
    sys.path.insert(0, str(ROOT / p))
from firm_marketdf import bars  # noqa: E402
from firm_tsbench import write_dataset  # noqa: E402
from pl_colfmt import quotes  # noqa: E402

S, MIN = 10**9, 60 * 10**9
GEN = ROOT / "data/platforms/generated/dataframes"
ENGINES = ("pandas", "polars eager", "polars lazy", "polars streaming", "duckdb")


@functools.lru_cache(maxsize=2)
def month(trades_per_day: int = 20_000, days: int = 20, symbols: int = 50, per: int = 1000, seed: int = 10):
    q = quotes(symbols, days, per).select(["date", "symbol", "ts", "bid", "ask"])
    rng = np.random.default_rng(seed)
    date = q["date"].to_numpy()
    picks = np.sort(np.concatenate([rng.choice(np.flatnonzero(date == d), trades_per_day) for d in range(days)]))
    sub = q.take(picks)
    side = rng.integers(0, 2, len(picks))
    price = np.where(side == 1, sub["ask"].to_numpy(), sub["bid"].to_numpy())
    ts = sub["ts"].to_numpy() + 1 + rng.integers(0, 10**9, len(picks))
    t = pa.table({"date": sub["date"], "symbol": sub["symbol"], "ts": pa.array(ts), "price": pa.array(price),
                  "qty": pa.array(rng.integers(1, 20, len(picks)) * 100)}).sort_by([("ts", "ascending")])
    return q, t.append_column("seq", pa.array(np.arange(len(picks))))        # the feed numbers trades in time order


BIG = {"trades_per_day": 60_000, "per": 3_000}               # the measured month: 3 million quotes, 1.2 million trades


def write_month(root: pathlib.Path = GEN, **kw) -> pathlib.Path:
    q, t = month(**kw)
    if root.exists():
        shutil.rmtree(root)
    write_dataset(q, t, root)
    return root


# ------------------------------------------------------------------------------------------------ conventions
def conventions(symbol: str = "S007", day: int = 5, width: int = 5 * MIN) -> dict:
    _, t = month()
    d = t.filter(pa.compute.and_(pa.compute.equal(t["symbol"], symbol), pa.compute.equal(t["date"], day))).to_pandas()
    d["ts"] = d["ts"] // S * S                                           # a vendor that stamps to the second
    on_edge = int((d["ts"] % width == 0).sum())
    a = bars(d, width, "left", "left")
    b = bars(d, width, "right", "right")
    f = bars(d, width, "left", "left", fill=True)
    a_ret = np.diff(np.log(a["close"].to_numpy(dtype=float)))
    f_ret = np.diff(np.log(f["close"].to_numpy(dtype=float)))
    same = a.assign(bar=a["bar"] + width).merge(b, on="bar", suffixes=("_a", "_b"))   # the same interval, both labels
    return {"trades": len(d), "on_edge": on_edge, "bars_left": len(a), "bars_right": len(b), "bars_filled": len(f),
            "volume_differs": int((same["volume_a"] != same["volume_b"]).sum()), "common_bars": len(same),
            "moved_volume": int((same["volume_a"] - same["volume_b"]).abs().sum() // 2),
            "returns_dropped": len(a_ret), "returns_filled": len(f_ret),
            "label_gap": int((b["bar"] - a["bar"]).iloc[0]) if len(a) and len(b) else 0}


# ------------------------------------------------------------------------------------------------ the pipeline
def _finish(ranks: pd.DataFrame, spreads: pd.DataFrame) -> dict:
    r = ranks.sort_values("symbol")
    s = spreads.sort_values("symbol")
    return {"avg_rank": dict(zip(r["symbol"], np.round(r["avg_rank"].astype(float), 9), strict=True)),
            "spread_bp": dict(zip(s["symbol"], np.round(s["spread_bp"].astype(float), 9), strict=True))}


def pipeline_pandas(root: pathlib.Path) -> dict:
    t = pq.read_table(root / "trades").to_pandas()
    q = pq.read_table(root / "quotes").to_pandas()
    t["date"], q["date"] = t["date"].astype(int), q["date"].astype(int)
    t = t.sort_values(["symbol", "ts", "seq"], kind="stable")
    t["bar"] = t["ts"] // MIN
    b = t.groupby(["symbol", "bar"], sort=True)["price"].last().reset_index(name="close")
    b["ret"] = np.log(b["close"]).groupby(b["symbol"]).diff()
    b = b.dropna(subset=["ret"])
    b["rank"] = b.groupby("bar")["ret"].rank(method="average")
    ranks = b.groupby("symbol")["rank"].mean().reset_index(name="avg_rank")
    j = pd.merge_asof(t.sort_values("ts"), q.sort_values("ts")[["symbol", "ts", "bid", "ask"]], on="ts", by="symbol")
    mid = (j["bid"] + j["ask"]) / 2.0
    j["spread_bp"] = 2e4 * (j["price"] - mid).abs() / mid
    return _finish(ranks, j.groupby("symbol")["spread_bp"].mean().reset_index())


def _polars_plan(t: pl.LazyFrame, q: pl.LazyFrame):
    c = pl.col
    b = (t.with_columns((c("ts") // MIN).alias("bar")).sort(["symbol", "ts", "seq"])
         .group_by(["symbol", "bar"]).agg(c("price").last().alias("close"))
         .sort(["symbol", "bar"])
         .with_columns(c("close").log().diff().over("symbol").alias("ret")).drop_nulls("ret")
         .with_columns(c("ret").rank("average").over("bar").alias("rank")))
    ranks = b.group_by("symbol").agg(c("rank").mean().alias("avg_rank"))
    quote = q.select(["symbol", "ts", "bid", "ask"]).sort("ts")
    j = (t.sort("ts").join_asof(quote, on="ts", by="symbol", check_sortedness=False)
         .with_columns(((c("bid") + c("ask")) / 2.0).alias("mid"))
         .with_columns((2e4 * (c("price") - c("mid")).abs() / c("mid")).alias("spread_bp")))
    spreads = j.group_by("symbol").agg(c("spread_bp").mean())
    return ranks, spreads


def pipeline_polars(root: pathlib.Path, mode: str) -> dict:
    if mode == "eager":
        t = pl.read_parquet(str(root / "trades/*/*.parquet"), hive_partitioning=True).lazy()
        q = pl.read_parquet(str(root / "quotes/*/*.parquet"), hive_partitioning=True).lazy()
    else:
        t = pl.scan_parquet(str(root / "trades/*/*.parquet"), hive_partitioning=True)
        q = pl.scan_parquet(str(root / "quotes/*/*.parquet"), hive_partitioning=True)
    ranks, spreads = _polars_plan(t, q)
    engine = "streaming" if mode == "streaming" else "auto"
    r, s = ranks.collect(engine=engine), spreads.collect(engine=engine)
    return _finish(r.to_pandas(), s.to_pandas())


def pipeline_duckdb(root: pathlib.Path) -> dict:
    con = duckdb.connect()
    con.execute("SET threads = 1")
    for name in ("trades", "quotes"):
        con.execute(f"CREATE VIEW {name[0]} AS SELECT * FROM "
                    f"read_parquet('{root}/{name}/*/*.parquet', hive_partitioning = true)")
    ranks = con.execute(f"""
        WITH b AS (SELECT symbol, ts // {MIN} AS bar, last(price ORDER BY ts, seq) AS close
                   FROM t GROUP BY ALL),
             r AS (SELECT symbol, bar, ln(close) - lag(ln(close))
                          OVER (PARTITION BY symbol ORDER BY bar) AS ret FROM b),
             k AS (SELECT symbol, bar,
                          (2 * rank() OVER w + count(*) OVER (PARTITION BY bar, ret) - 1)
                          / 2.0 AS rank
                   FROM r WHERE ret IS NOT NULL WINDOW w AS (PARTITION BY bar ORDER BY ret))
        SELECT symbol, avg(rank) AS avg_rank FROM k GROUP BY symbol""").df()
    spreads = con.execute("""
        WITH j AS (SELECT t.symbol, t.price, (q.bid + q.ask) / 2 AS mid
                   FROM t ASOF LEFT JOIN q ON t.symbol = q.symbol AND t.ts >= q.ts)
        SELECT symbol, avg(2e4 * abs(price - mid) / mid) AS spread_bp
        FROM j GROUP BY symbol""").df()
    return _finish(ranks, spreads)


def run_engine(engine: str, root: pathlib.Path = GEN) -> dict:
    if engine == "baseline":                                      # the imports alone: subtracted from the others
        return {"avg_rank": {}, "spread_bp": {}}
    if engine == "pandas":
        return pipeline_pandas(root)
    if engine.startswith("polars"):
        return pipeline_polars(root, engine.split()[1])
    if engine == "duckdb":
        return pipeline_duckdb(root)
    raise ValueError(engine)


def child(engine: str, root: str) -> None:
    """Entry point of the measuring subprocess: runs one engine and prints its time, peak memory and answer."""
    t = time.perf_counter()
    out = run_engine(engine, pathlib.Path(root))
    dt = time.perf_counter() - t
    # the high-water mark of this process's own memory; ru_maxrss would include the parent's, kept across exec
    hwm = [x for x in pathlib.Path("/proc/self/status").read_text().splitlines() if x.startswith("VmHWM:")][0]
    rss_mb = int(hwm.split()[1]) / 1024
    print(json.dumps({"engine": engine, "seconds": dt, "peak_mb": rss_mb, "answer": out}))


def measure(engine: str, root: pathlib.Path = GEN) -> dict:
    code = f"import sys; sys.path.insert(0, {str(pathlib.Path(__file__).parent)!r}); import pl_dataframes as P; " \
           f"P.child({engine!r}, {str(root)!r})"
    env = {"POLARS_MAX_THREADS": "1", "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "PATH": "/usr/bin:/bin"}
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True, env=env)
    return json.loads(r.stdout.strip().splitlines()[-1])


def plan_text(root: pathlib.Path = GEN) -> str:
    """The optimised lazy plan of a narrow query: pushdowns visible in it."""
    lf = (pl.scan_parquet(str(root / "trades/*/*.parquet"), hive_partitioning=True)
          .filter((pl.col("symbol") == "S007") & (pl.col("date") == 5)).select(["ts", "price"]))
    return lf.explain()
