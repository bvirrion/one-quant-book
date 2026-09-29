"""Numbers gate for Book 18, chapter 27: every .sql answer is run on DuckDB and, where the dialect allows, on
SQLite, and compared with a pandas or numpy computation on the same generated fixtures (planted NULLs, a planted
duplicate quote timestamp and a trade inside it)."""
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
from iv_sql import asof_numpy, asof_pandas, asof_polars, fixtures, run_duckdb, run_sqlite

T = fixtures()
TR, QU = T["trades"], T["quotes"]


def both(name):
    return run_duckdb(name, T), run_sqlite(name, T)


def test_q1_join_counts():
    d, s = both("join_counts")
    assert d.iloc[0].tolist() == s.iloc[0].tolist() == [56, 61, 5]
    assert (~TR["account"].isin(T["accounts"]["account"])).sum() == 5


def test_q2_nulls():
    d, s = both("null_aggregates")
    assert d.iloc[0]["n_rows"] == 61 and d.iloc[0]["n_qty"] == 59 and d.iloc[0]["total_qty"] == 60_100
    assert round(d.iloc[0]["avg_qty"], 2) == round(60_100 / 59, 2) == 1018.64
    assert round(60_100 / 61, 2) == 985.25  # what treating NULL as zero would give
    assert s.iloc[0]["n_qty"] == 59


def test_q3_having():
    d, s = both("having")
    assert d["desk"].tolist() == s["desk"].tolist() == ["delta1"] and d["volume"].tolist() == [41_000]
    m = TR.merge(T["accounts"], on="account").groupby("desk")["qty"].sum()
    assert m["delta1"] == 41_000 and m["vol"] <= 20_000


def test_q4_duplicate_join():
    d, s = both("duplicate_join")
    assert d.iloc[0].tolist() == s.iloc[0].tolist() == [83, 81]


def test_q5_top2():
    d, s = both("top2")
    assert d.values.tolist() == s.values.tolist()
    ref = TR.dropna(subset=["qty"]).sort_values(["sym", "qty", "ts"], ascending=[True, False, True]).groupby("sym").head(2)
    assert d[["sym", "ts", "qty"]].values.tolist() == ref[["sym", "ts", "qty"]].values.tolist()


def test_q6_drawdown():
    d, s = both("drawdown")
    assert np.allclose(d["drawdown"], s["drawdown"])
    p = T["pnl"].sort_values(["account", "day"])
    cum = p.groupby("account")["pnl"].cumsum()
    dd = cum - cum.groupby(p["account"]).cummax()
    assert np.allclose(d["drawdown"].to_numpy(), dd.to_numpy())
    assert d.groupby("account")["drawdown"].min().round(1).to_dict() == {"A1": -8.9, "A2": -32.3}


def test_q7_lag():
    d, s = both("lag_returns")
    ref = TR.sort_values(["sym", "ts"]).groupby("sym")["px"].pct_change()
    assert np.allclose(d["ret"].to_numpy(), ref.to_numpy(), equal_nan=True)
    assert np.allclose(s["ret"].astype(float).to_numpy(), ref.to_numpy(), equal_nan=True)


def test_q8_vwap():
    d, s = both("vwap")
    t = TR.dropna(subset=["qty"]).assign(bucket=lambda x: x["ts"] // 300, n=lambda x: x["px"] * x["qty"])
    g = t.groupby(["sym", "bucket"]).agg(n=("n", "sum"), q=("qty", "sum")).reset_index()
    assert np.allclose(d["vwap"].to_numpy(), (g["n"] / g["q"]).astype(float).to_numpy())
    assert np.allclose(s["vwap"].to_numpy(), d["vwap"].to_numpy())


def test_q9_islands():
    d, s = both("islands")
    assert d.values.tolist() == s.values.tolist() == [["A1", 10], ["A2", 7]]
    for acc, want in (("A1", 10), ("A2", 7)):
        x = (T["pnl"][T["pnl"]["account"] == acc].sort_values("day")["pnl"] > 0).astype(int).tolist()
        best = run = 0
        for v in x:
            run = run + 1 if v else 0
            best = max(best, run)
        assert best == want


def test_q10_asof_and_ties():
    ref = asof_numpy(TR, QU)  # last of equal timestamps
    duck = run_duckdb("asof_duckdb", T)
    lite = run_sqlite("asof_portable", T)
    tie_row = TR["ts"].to_numpy() == 125
    same = np.isclose(duck["bid"], ref) | (duck["bid"].isna() & np.isnan(ref))
    assert same[~tie_row].all()  # everywhere except inside the tie
    assert duck["bid"][tie_row].iloc[0] in (100.40, 100.45)  # a tie: the engine's pick is not specified
    assert np.isclose(lite["bid"].astype(float), ref, equal_nan=True).all()  # rowid tie-break: last inserted
    assert int(np.isnan(ref).sum()) == 2  # trades before the first quote of their symbol


def test_q11_lookahead():
    la = run_duckdb("lookahead", T)
    assert int((la["quote_ts"] > la["ts"]).sum()) == 56 and int((la["quote_ts"] == la["ts"]).sum()) == 4


def test_q12_halts():
    d, s = both("halts")
    assert d.values.tolist() == s.values.tolist() == [["AAA", 100, 160], ["AAA", 400, 470], ["BBB", 300, 360]]


def test_q13_array_versions():
    ref = asof_numpy(TR, QU)
    pdv = asof_pandas(TR, QU).sort_values("ts", kind="stable")["bid"].to_numpy()
    plv = asof_polars(TR, QU).sort_values("ts", kind="stable")["bid"].to_numpy()
    assert np.allclose(pdv, ref, equal_nan=True) and np.allclose(plv, ref, equal_nan=True)
