"""Acceptance tests of firm.tsbench (One Quant Book 15, chapter 5)."""
import pathlib
import sys

import numpy as np
import pyarrow as pa

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_tsbench import ENGINES, QUERIES, Params, bench, check, make_engine, write_dataset

DAY = 86_400 * 10**9


def data(seed=1):
    rng = np.random.default_rng(seed)
    rows = []
    for d in range(3):
        for s in ("AA", "BB", "CC"):
            ts = np.sort(rng.integers(0, 23_400 * 10**9, 300)) + d * DAY + 34_200 * 10**9
            mid = 10_000 + np.cumsum(rng.choice([-100, 0, 100], 300))
            rows += [(d, s, int(t), int(m - 50), int(m + 50)) for t, m in zip(ts, mid, strict=True)]
    q = pa.table({k: [r[i] for r in rows] for i, k in enumerate(("date", "symbol", "ts", "bid", "ask"))})
    pick = rng.choice(len(rows), 60, replace=False)
    t = pa.table({"date": [rows[i][0] for i in pick], "symbol": [rows[i][1] for i in pick],
                  "ts": [rows[i][2] + 1 for i in pick], "price": [rows[i][3] for i in pick]})
    return q, t


P = Params("BB", 1, DAY + 36_000 * 10**9, DAY + 39_600 * 10**9, DAY + 43_200 * 10**9)


def test_all_engines_agree_on_every_shape(tmp_path):
    q, t = data()
    write_dataset(q, t, tmp_path)
    eng = {n: make_engine(n, q, t, tmp_path) for n in ENGINES}
    assert check(eng, P) == {k: True for k in QUERIES}


def test_a_wrong_engine_is_caught(tmp_path):
    q, t = data()
    write_dataset(q, t, tmp_path)
    eng = {n: make_engine(n, q, t, tmp_path) for n in ("duckdb", "numpy")}

    class Off:
        def run(self, query, p):
            r = eng["numpy"].run(query, p)
            return r[:-1] if query == "range" else r

    eng["off"] = Off()
    assert check(eng, P)["range"] is False and check(eng, P)["point"] is True


def test_asof_returns_the_quote_one_nanosecond_before(tmp_path):
    q, t = data()
    write_dataset(q, t, tmp_path)
    rows = make_engine("duckdb", q, t, tmp_path).run("asof", P)
    assert all(price == bid for _s, _ts, price, bid, _ask in rows)


def test_bench_reports_cold_and_warm(tmp_path):
    q, t = data()
    write_dataset(q, t, tmp_path)
    res = bench(lambda n: make_engine(n, q, t, tmp_path), P, rounds=2, engines=("sqlite", "numpy"))
    assert len(res) == 2 * len(QUERIES) and all(r["cold"] > 0 and r["median"] > 0 for r in res)
