"""Numbers gate: every numerical answer printed in One Quant Book 15, chapter 12 (text and solutions)."""
import csv
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import pl_parity as P

S = P.S

FIG = pathlib.Path(__file__).resolve().parents[4] / "figdata/platforms/12-simulation-production-parity"


def _csv(name):
    return list(csv.DictReader(open(FIG / name)))


def test_small_runs():
    r = P.run_three(2, S.FIXED, 120.0)
    assert r["vs_sim"].same and r["vs_replay"].same and len(r["prod"].outputs) > 5
    for d in P.DEFECTS:
        r = P.run_three(2, S.Defects(**{d: True}), 120.0)
        assert not r["vs_sim"].same and not r["vs_replay"].same, d


@pytest.mark.reference
def test_full_runs_reproduce_the_tables():
    rows = P.defect_table()
    got = [(r["first"], r["events"], r["affected"], r["outputs"]) for r in rows]
    want = [(int(r["first"]), int(r["events"]), int(r["affected"]), int(r["outputs"])) for r in _csv("defects.csv")]
    assert got == want
    assert all(r["same_sim"] and r["same_replay"] for r in P.clean())


@pytest.mark.reference
def test_float_price_example():
    r = P.run_three(1, S.Defects(float_prices=True), 3600.0)
    p = r["vs_sim"]
    assert (r["prod"].outputs[p.first][4], r["sim"].outputs[p.first][4]) == (999_799, 999_800)
    orders = [x for x in r["prod"].outputs if x[1] == "order"]
    assert (len(orders), sum(x[4] % 100 != 0 for x in orders)) == (1501, 1161)
    assert int((99.99 - 0.01) * 10_000) == 999_799 and int(99.98 * 10_000) == 999_800


def test_named_result_numbers():
    d = {(r["defect"], r["against"]): r for r in _csv("defects.csv")}
    sim = {k[0]: v for k, v in d.items() if k[1] == "sim"}
    assert [int(sim[k]["events"]) for k in ("wall clock", "float prices", "callback order", "ack semantics")] \
        == [175, 126, 203, 2]
    assert [int(sim[k]["affected"]) for k in ("wall clock", "float prices", "callback order", "ack semantics")] \
        == [539, 1686, 387, 8449]
    assert [int(sim[k]["outputs"]) for k in ("wall clock", "float prices", "callback order", "ack semantics")] \
        == [553, 1690, 463, 8452]
    assert [round(float(sim[k]["seconds"]), 1) for k in ("wall clock", "float prices", "callback order")] \
        == [30.0, 24.4, 33.0]
    rep = {k[0]: v for k, v in d.items() if k[1] == "replay"}
    assert [int(rep[k]["affected"]) for k in ("wall clock", "float prices", "callback order", "ack semantics")] \
        == [305, 1161, 416, 8450]
    c = _csv("clean.csv")
    assert len(c) == 10 and all(r["same_sim"] == "1" and r["same_replay"] == "1" for r in c)
    assert sum(int(r["outputs"]) for r in c) == 8887 and sum(int(r["inputs"]) for r in c) == 188_079


@pytest.mark.reference
def test_defect_narratives():
    r = P.run_three(1, S.Defects(wall_clock=True), 3600.0)
    p = r["vs_sim"]
    assert r["prod"].outputs[p.first][1] == "cancel" and r["prod"].outputs[p.first][0] - r["prod"].start == 30 * P.SEC
    assert (72_000 + 30 - 34_199) / 3600 > 10 and 30 * 100 / 60 == 50
    r = P.run_three(1, S.Defects(arrival_order=True), 3600.0)
    p = r["vs_sim"]
    a, b = r["prod"], r["sim"]
    assert [x[1] for x in a.inputs[a.marks[p.first] - 2:a.marks[p.first]]] == ["fill", "book"]
    assert round((b.outputs[p.first][0] - a.outputs[p.first][0]) / 1e9, 2) == 0.19
    r = P.run_three(1, S.Defects(acked_working=True), 3600.0)
    a = r["prod"]
    assert sum(1 for x in a.inputs if x[1] == "reject") == 8406
    assert a.inputs[1][0] - a.inputs[0][0] == 500
