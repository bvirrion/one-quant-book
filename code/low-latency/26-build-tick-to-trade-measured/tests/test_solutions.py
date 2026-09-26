"""Numbers gate, Book 13 chapter 26."""
import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
FIG = ROOT / "figdata/low-latency/26-build-tick-to-trade-measured"
sys.path.insert(0, str(HERE / "python"))
import ll_t2t as L  # noqa: E402


def rows(name):
    with open(FIG / name, newline="", encoding="utf8") as f:
        return list(csv.DictReader(f))


def stages():
    return {r["stage"]: {k: float(r[k]) for k in ("p50_ns", "p99_ns", "p999_ns")} for r in rows("measured_stages.csv")}


def test_stages_and_totals():
    s = stages()
    m = {k: v["p50_ns"] for k, v in s.items()}
    assert round(m["receive"] / 1000, 1) == 1.4 and round(m["decode"], -1) == 440 and round(m["ring"] / 1000, 2) == 0.76
    assert round(m["book"], -1) == 160 and round(m["strategy"], -1) == 100 and round(m["risk"]) == 47
    assert round(m["gateway"]) == 33 and round(m["transmit"] / 1000, 1) == 2.9
    assert round(m["tick to trade"] / 1000, 1) == 8.8 and round(m["tick to trade"] / 1000) == 9
    assert round(m["in process"] / 1000, 1) == 3.7
    t = s["tick to trade"]
    assert round(t["p99_ns"] / 1000) == 79 and round(t["p999_ns"] / 1e6, 1) == 3.5
    ip = s["in process"]
    assert round(ip["p99_ns"] / 1000) == 42 and round(ip["p999_ns"] / 1e6, 1) == 3.5
    assert max(m, key=lambda k: m[k] if k not in ("tick to trade", "in process") else 0) == "transmit"
    tails = {k: v["p999_ns"] for k, v in s.items() if k not in ("tick to trade", "in process")}
    assert max(tails, key=tails.get) == "ring" and round(tails["ring"] / 1e6, 1) == 3.5
    assert all(s[k]["p99_ns"] < 1000 for k in ("book", "risk", "gateway"))           # well under a microsecond
    comp = sum(m[k] for k in ("book", "strategy", "risk", "gateway"))
    inproc = sum(m[k] for k in ("decode", "ring", "book", "strategy", "risk", "gateway"))
    assert round(comp, -1) == 340 and round(inproc / 1000, 1) == 1.5 and comp / inproc < 0.25
    assert round((inproc + 1_700) / 1_000, 1) == 3.2                                 # the projection
    assert round((100 + 160 + 100 + 50 + 30 + 1_700) / 1_000, 1) == 2.1
    assert round((inproc - comp) / 1000, 1) == 1.2 and 0.6 <= (m["ring"] + m["decode"] - 100) / inproc <= 0.75
    ch5 = {r["clock"]: float(r["ns_per_call"]) for r in csv.DictReader(open(
        ROOT / "figdata/low-latency/05-measuring-latency/measured_clocks.csv"))}
    assert round(ch5["rdtscp"]) == 11                                                # the cost of a point


def test_budget_table():
    b = {r["stage"]: r for r in rows("measured_budget.csv")}
    assert {k for k, r in b.items() if r["ok"] == "True"} == {"strategy", "risk"}
    assert [int(b[k]["target_ns"]) for k in ("receive", "decode", "book", "strategy", "risk", "transmit")] == \
        [900, 60, 120, 200, 50, 800]
    meas = {k: float(r["measured_ns"]) for k, r in b.items()}
    assert [round(meas[k], -2) for k in ("receive", "transmit", "end-to-end")] == [1_400, 2_900, 7_400]
    assert [round(meas[k], -1) for k in ("decode", "book", "strategy")] == [440, 160, 100] and round(meas["risk"]) == 47
    assert round(meas["decode"] / 60) == 7 and round(meas["receive"] / 900, 1) == 1.6 and round(meas["transmit"] / 800, 1) == 3.6
    assert round(meas["book"] / 120, 1) == 1.3                                         # by a third
    assert L.budget().end_to_end == {0.5: 3_000}


def test_run_metadata():
    meta = (FIG / "measured_stages.csv.meta").read_text()
    want = (ROOT / "code/firm/ticktotrade/data/expected.txt").read_text().split()[-1]
    assert f"order_hashes: {want}" in meta and "allocations_after_warmup: 0 0 0 0 0 0 0 0 0 0" in meta
    assert int(rows("measured_stages.csv")[-1]["n"]) == 10_500
