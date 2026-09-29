"""Numbers gate: every numerical answer printed in One Quant Book 15, chapter 4 (text and solutions)."""
import csv
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "tickstore"))
from firm_tickstore import EVENT_V1, EVENT_V2
from pl_tickstore import GEN, asof_all, build, evolution, flat_summary, store, window

MEASURED = pathlib.Path(__file__).resolve().parents[4] / (
    "figdata/platforms/04-a-tick-store-on-open-formats/measured_tickstore.csv")


def test_small_runs(tmp_path):
    info = build(tmp_path / "store", days=5, hours=0.01, gen=tmp_path / "gen")
    assert [info[k]["version"] for k in range(5)] == [1, 1, 1, 2, 2]
    assert all("compacted" in info[k] for k in range(4)) and "compacted" not in info[4]
    a = asof_all(tmp_path / "store")
    assert a["duck_polars"] and a["duck_reference"] and a["trades"] == sum(info[k]["trades"] for k in range(5))
    s = store(tmp_path / "store")
    r = s.sql("SELECT date, count(*) n, count(venue) v FROM quotes GROUP BY date ORDER BY date").to_pylist()
    assert [x["v"] == 0 for x in r] == [True, True, True, False, False]
    assert sum(x["n"] for x in r) == sum(info[k]["quotes"] for k in range(5))
    assert evolution()["v1_to_v2"] == [] and EVENT_V1.itemsize == 56 and EVENT_V2.itemsize == 64


@pytest.mark.reference
def test_week():
    root = GEN / "store_week"
    info = build(root)
    ev = [info[k]["events"] for k in range(5)]
    assert ev == [258535, 47472, 50266, 78584, 129305] and sum(ev) == 564162
    assert sum(info[k]["quotes"] for k in range(5)) == 96206 and sum(info[k]["trades"] for k in range(5)) == 17281
    assert info[0]["flat_bytes"] == 14478152 and info[0]["flat_bytes"] - 258535 * 56 == 192
    assert info[4]["flat_bytes"] - 129305 * 64 == 256 and 256 + 258535 * 64 == 16546496
    pq0 = sum(v["bytes"] for v in info[0]["compacted"].values())
    intraday0 = info[0]["flat_bytes"] + info[0]["ipc_bytes"]
    assert round(pq0 / 1e6, 2) == 6.15 and round(intraday0 / 1e6, 1) == 17.5 and round(intraday0 / pq0, 2) == 2.85
    assert info[0]["compacted"]["events"]["files"] == 3 and round(info[0]["compacted"]["events"]["bytes"] / 258535, 1) == 20.0
    a = asof_all(root)
    assert (a["trades"], a["duck_polars"], a["duck_reference"], a["ts_join_differs"]) == (17281, True, True, 223)
    assert round(100 * 223 / 17281, 1) == 1.3
    w = window(root).to_pylist()
    assert [(x["n"], x["with_venue"]) for x in w] == [(12291, 0), (996, 0), (1388, 0), (1197, 1197), (4473, 4473)]
    assert flat_summary(root / "intraday/2026-09-25/events.flat") == {
        0: (4, 0, 129307), 1: (27157, 84000, 129305), 2: (102144, 367600, 129306)}


def test_measured_csv_matches_text():
    rows = {r["task"]: r for r in csv.DictReader(open(MEASURED))}
    c = rows["compaction of the busiest day"]
    rate = int(c["rows"]) / float(c["seconds"])
    # printed: 0.12 s; about 2.2 million events a second; 4.7 billion events in 35 minutes (update after re-measuring)
    assert round(float(c["seconds"]), 2) == 0.12 and round(rate / 1e6, 1) == 2.2
    assert round(rate * 35 * 60 / 1e9, 1) == 4.7 and round(311e9 / (rate * 35 * 60)) == 66
    ms = {k: round(1000 * float(v["seconds"]), 1) for k, v in rows.items()}
    assert (ms["window: SIM2 09:32-09:35; five days"], ms["as-of join; DuckDB"], ms["as-of join; Polars"]) == (17.8, 16.1, 44.5)
    assert (ms["as-of join; reference (Python)"], ms["scan of a day; flat file (mmap)"], ms["scan of a day; Parquet"]) == (
        165.7, 0.8, 2.1)
    duck, pol = float(rows["as-of join; DuckDB"]["seconds"]), float(rows["as-of join; Polars"]["seconds"])
    ref = float(rows["as-of join; reference (Python)"]["seconds"])
    assert duck < pol < ref
    assert float(rows["scan of a day; flat file (mmap)"]["seconds"]) < float(rows["scan of a day; Parquet"]["seconds"])
