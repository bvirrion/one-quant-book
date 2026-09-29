"""Numbers gate: every numerical answer printed in One Quant Book 15, chapter 21 (text and solutions)."""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import pl_tradecap as P

FIG = pathlib.Path(__file__).resolve().parents[4] / "figdata/platforms/21-trade-capture-and-booking"


def _csv(name):
    return list(csv.DictReader(open(FIG / name)))


def test_small_runs():
    st, ev = P.week(n=20)
    d = P.downstream(st, ev)
    assert d["n"] == 20 and all(st.as_of(e.trade_id) is not None for e in ev)


def test_block_and_allocation():
    f = P.block_fills()
    assert (len(f), sum(q for q, _, _ in f)) == (57, 9900)
    a = P.allocations(f)
    assert round(a["largest-remainder"]["avg"] / 1e4, 4) == 100.0783
    rows = {r["rule"]: r for r in _csv("allocation.csv")}
    assert [(r["fund_a"], r["fund_b"], r["fund_c"], r["residual"], r["max_dev"]) for r in rows.values()] == [
        ("4900", "3000", "2000", "0", "50"), ("5000", "3000", "1900", "0", "80"), ("5000", "3000", "2000", "-100", "50")]
    _events, store = P.capture_block(f)
    assert len(store.log) == 57 and all(P.T.validate(e.data) == [] for e in store.log)


def test_week_and_downstream():
    st, ev = P.week()
    kinds = {}
    for e in ev:
        kinds[e.kind] = kinds.get(e.kind, 0) + 1
    assert kinds == {"new": 200, "amend": 69, "novate": 26, "terminate": 41} and len(ev) == 336
    d = P.downstream(st, ev)
    assert d["wrong"] == {"risk": 25, "confirmation": 60, "settlement": 71} and d["disagree"] == 109
    v = {n: d["views"][n]["S000"] for n in d["views"]}
    assert [(x["version"], x["quantity"]) for x in v.values()] == [(3, 150e6), (2, 150e6), (4, 90e6)]
    assert v["confirmation"]["seller"] != d["golden"]["S000"]["seller"] == v["risk"]["seller"]
    assert d["golden"]["S000"]["version"] == 4 and [x for _, x in st.versions("S000")] == [1, 2, 3, 4]
    rows = {r["system"]: r for r in _csv("downstream.csv")}
    assert rows["any disagreement"]["copy_wrong"] == "109" and all(r["events_wrong"] == "0" for r in rows.values())


def test_exercises():
    st, ev = P.week()
    assert P.downstream(st, ev, hours=(12, 18))["wrong"]["risk"] == 2
    got = {r: P.T.allocate([(1000, 100.0)], {"a": 1, "b": 1, "c": 1}, r, 100) for r in
           ("largest-remainder", "floor-then-largest", "round-each")}
    assert [{f: q for f, (q, _) in a.items()} for a, _ in got.values()] == [{"a": 400, "b": 300, "c": 300}] * 2 + [
        {"a": 300, "b": 300, "c": 300}]
    assert [res for _, res in got.values()] == [0, 0, 100]
    assert P.T.uti(P.FIRM_LEI, 7) == P.FIRM_LEI + "0" * 31 + "7"
