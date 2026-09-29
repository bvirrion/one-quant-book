"""Numbers gate: every numerical answer printed in One Quant Book 15, chapter 10 (text and solutions)."""
import csv
import pathlib
import sys

import duckdb
import pandas as pd
import polars as pl
import pyarrow.compute as pc

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "marketdf"))
import firm_marketdf as M
import pl_dataframes as P

FIG = pathlib.Path(__file__).resolve().parents[4] / "figdata/platforms/10-dataframes"
SMALL = {"trades_per_day": 400, "days": 6, "symbols": 6, "per": 100}


def test_small_runs(tmp_path):
    root = P.write_month(tmp_path / "m", **SMALL)
    outs = [P.run_engine(e, root) for e in P.ENGINES]
    assert all(o == outs[0] for o in outs) and len(outs[0]["avg_rank"]) == 6
    plan = P.plan_text(root)
    assert "date=5" in plan and "date=4" not in plan and "PROJECT 4/6 COLUMNS" in plan and "SELECTION" in plan


def test_conventions_example():
    c = P.conventions()
    assert (c["trades"], c["on_edge"], c["bars_left"], c["bars_right"], c["bars_filled"]) == (375, 2, 74, 74, 78)
    assert (c["volume_differs"], c["common_bars"], c["moved_volume"]) == (4, 74, 600)
    assert (c["returns_dropped"], c["returns_filled"], c["label_gap"]) == (73, 77, 5 * P.MIN)


def test_month_sizes():
    q, t = P.month(**P.BIG)
    assert (q.num_rows, t.num_rows) == (3_000_000, 1_200_000)


def test_exercise_1_and_4_edges():
    w = 5 * P.MIN
    t = pd.DataFrame({"symbol": ["A"], "ts": [2 * w], "price": [100], "qty": [100], "seq": [0]})
    left, right = M.bars(t, w, "left", "left"), M.bars(t, w, "right", "right")
    assert left["bar"].iloc[0] == 2 * w and right["bar"].iloc[0] == 2 * w      # same label, different intervals
    assert M._bucket_pd(pd.Series([2 * w]), w, "left").iloc[0] == 2
    assert M._bucket_pd(pd.Series([2 * w]), w, "right").iloc[0] == 1
    assert (-7 // 5, int(-7 / 5)) == (-2, -1)                                   # floor versus truncation
    assert duckdb.sql("SELECT -7 // 5").fetchone()[0] == -1                     # DuckDB's // truncates


def test_exercise_7_engines_and_conventions():
    _, t = P.month()
    d = t.filter(pc.equal(t["symbol"], "S003")).to_pandas()
    d["ts"] = d["ts"] // P.S * P.S
    assert len(d) == 7_960
    vols = set()
    for label, closed in (("left", "left"), ("right", "right"), ("left", "right"), ("right", "left")):
        out = [M.bars(d, P.MIN, label, closed, engine=e) for e in M.ENGINES]
        assert all(o.equals(out[0]) for o in out)
        vols.add(int(out[0]["volume"].sum()))
    assert vols == {int(d["qty"].sum())}


def test_example_ties():
    _, t = P.month()
    b = (pl.from_arrow(t).with_columns((pl.col("ts") // P.MIN).alias("bar")).sort(["symbol", "ts", "seq"])
         .group_by(["symbol", "bar"]).agg(pl.col("price").last().alias("close")).sort(["symbol", "bar"])
         .with_columns(pl.col("close").log().diff().over("symbol").alias("ret")).drop_nulls("ret"))
    assert len(b) == 222_621 and round(100 * float((b["ret"] == 0).mean()), 1) == 10.8
    g = b.group_by(["bar", "ret"]).len()
    assert int((g["len"] > 1).sum()) == 6_467 and b["bar"].n_unique() == 7_808
    d = pd.DataFrame({"m": [0] * 4, "r": [0.1, 0.2, 0.2, 0.3]})
    assert [list(M.xs_rank(d, "m", "r", engine=e)) for e in M.ENGINES] == [[1, 2.5, 2.5, 4]] * 3


def test_measured_numbers_in_text():
    r = {x["engine"]: (float(x["seconds"]), float(x["extra_mb"])) for x in csv.DictReader(open(FIG / "measured_engines.csv"))}
    assert [round(r[e][1]) for e in P.ENGINES] == [895, 769, 654, 614, 317]
    assert round(r["pandas"][0], 1) == 1.3 and round(r["polars streaming"][0], 2) == 0.82
    assert 0.8 <= min(x[0] for x in r.values()) and max(x[0] for x in r.values()) < 1.35
    assert min(r, key=lambda e: r[e][1]) == "duckdb" and max(r, key=lambda e: r[e][1]) == "pandas"
    assert min(r, key=lambda e: r[e][0]) == "polars streaming"
    assert round(r["pandas"][1] / r["duckdb"][1], 1) == 2.8
    meta = (FIG / "measured_engines.csv.meta").read_text()
    assert "155 MB" in meta
