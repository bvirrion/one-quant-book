"""Time-series databases and the alternatives (One Quant Book 15, chapter 5).

The chapter 3 month of quotes (fifty symbols, twenty days, a million rows) and 40,000 trades drawn from it (each one
nanosecond after a quote, at its bid or its ask) are loaded into five engines by firm.tsbench, which checks that all
five give the same answer to every query shape before it times anything.
"""
from __future__ import annotations

import functools
import pathlib
import shutil
import sys

import numpy as np
import pyarrow as pa

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/tsbench"))
sys.path.insert(0, str(ROOT / "code/platforms/03-columnar-formats/python"))
from firm_tsbench import ENGINES, QUERIES, Params, bench, check, make_engine, write_dataset  # noqa: E402
from pl_colfmt import DAY_NS, quotes  # noqa: E402

GEN = ROOT / "data/platforms/generated/tsbench"
PARAMS = Params(symbol="S007", date=5, t0=5 * DAY_NS + 36_000 * 10**9, t1=5 * DAY_NS + 39_600 * 10**9,
                point_t=5 * DAY_NS + 43_200 * 10**9)


@functools.lru_cache(maxsize=2)
def dataset(symbols: int = 50, days: int = 20, per: int = 1000, trades_per_day: int = 2000, seed: int = 8):
    q = quotes(symbols, days, per).select(["date", "symbol", "ts", "bid", "ask"])
    rng = np.random.default_rng(seed)
    date = q["date"].to_numpy()
    picks = np.concatenate([rng.choice(np.flatnonzero(date == d), trades_per_day, replace=False) for d in range(days)])
    picks.sort()
    sub = q.take(picks)
    side = rng.integers(0, 2, len(picks))
    price = np.where(side == 1, sub["ask"].to_numpy(), sub["bid"].to_numpy())
    t = pa.table({"date": sub["date"], "symbol": sub["symbol"], "ts": pa.array(sub["ts"].to_numpy() + 1),
                  "price": pa.array(price)})
    return q, t


def prepare(root: pathlib.Path = GEN, **kw):
    q, t = dataset(**kw)
    if root.exists():
        shutil.rmtree(root)
    write_dataset(q, t, root)
    return q, t


def engines(root: pathlib.Path = GEN, **kw) -> dict:
    q, t = prepare(root, **kw)
    return {n: make_engine(n, q, t, root) for n in ENGINES}


def run_bench(root: pathlib.Path = GEN, rounds: int = 5, params: Params = PARAMS, **kw) -> list[dict]:
    q, t = prepare(root, **kw)
    return bench(lambda n: make_engine(n, q, t, root), params, rounds)


def answers(root: pathlib.Path = GEN, params: Params = PARAMS, **kw) -> dict:
    e = engines(root, **kw)
    return {"check": check(e, params), "sizes": {qn: len(e["duckdb"].run(qn, params)) for qn in QUERIES},
            "point": e["numpy"].run("point", params)}
