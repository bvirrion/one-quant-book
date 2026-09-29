"""Numbers gate: every numerical answer printed in One Quant Book 15, chapter 20 (text and solutions)."""
import csv
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import pl_riskgrid as P

FIG = pathlib.Path(__file__).resolve().parents[4] / "figdata/platforms/20-the-risk-grid"


def _csv(name):
    return list(csv.DictReader(open(FIG / name)))


def _s32():
    return {int(r["scen_batch"]): r for r in _csv("sweep_32.csv")}


def test_small_runs():
    small = [t for t in P.book() if t.kind != "autocallable"][:2000] + [P.book()[-1]]
    r = P.G.run(P.G.plan(small, 50, 0.5, 10, 5.0), 1, 4)
    assert r.makespan > 0 and r.lost_cells == 50 * 1 * 0 + 50 * sum(t.fails for t in small)


def test_costs_and_book():
    c = P.costs()
    assert [round(c[k] * 1e6, 1) for k in ("swap", "swaption", "option")] == [14.5, 10.2, 5.1]
    assert round(c["autocallable"] * 1e3, 1) == 22.2
    assert round(sum(P.COUNTS[k] * c[k] for k in P.COUNTS), 1) == 112.2
    assert round(c["autocallable"] * P.SLOW_FACTOR, 2) == 4.88
    rows = {r["kind"]: float(r["seconds"]) for r in _csv("measured_costs.csv")}
    assert (round(rows["swap deltas by bump"] * 1e6), round(rows["swap deltas by adjoint"] * 1e6)) == (388, 66)
    assert round(rows["swap deltas by bump"] / rows["swap deltas by adjoint"], 1) == 5.9


@pytest.mark.reference
def test_sweep_reproduces_the_figures():
    got = {(r["cores"], r["scen_batch"], r["cost_aware"]): round(r["makespan"] / 3600, 4) for r in P.sweep()}
    for r in _csv("sweep_32.csv"):
        assert got[(32, int(r["scen_batch"]), False)] == float(r["naive_h"])


def test_named_result_numbers():
    s32 = {int(r["scen_batch"]): r for r in _csv("sweep_32.csv")}
    s64 = {int(r["scen_batch"]): r for r in _csv("sweep_64.csv")}
    assert (int(s32[1000]["naive_s"]), int(s64[1000]["naive_s"])) == (8468, 6922)
    assert (int(s32[1000]["aware_s"]), int(s32[250]["aware_s"]), int(s32[100]["naive_s"])) == (4123, 3846, 4298)
    assert (int(s32[5]["naive_s"]), int(s32[5]["tasks"]), int(s32[1000]["tasks"])) == (10533, 44000, 220)
    assert sorted(b for b, r in s32.items() if int(r["naive_s"]) <= P.WINDOW) == [20, 50, 100, 250]
    assert sorted(b for b, r in s32.items() if int(r["aware_s"]) <= P.WINDOW) == [20, 50, 100, 250, 500, 1000]
    f = {r["policy"]: r for r in _csv("failures.csv")}
    assert (int(f["task"]["makespan_s"]), int(f["task"]["wasted_s"]), int(f["task"]["lost_cells"])) == (4095, 1100, 38263000)
    assert (int(f["trade"]["makespan_s"]), int(f["trade"]["wasted_s"]), int(f["trade"]["lost_cells"])) == (4035, 0, 1000)
    assert P.pricing_calls() == {"bump": 1_020_000, "adjoint_runs": 60_000, "full_grid": 105_105_000}
    assert P.intraday() == {"repriced": 1500, "calls": 1_500_000, "full_calls": 105_000_000}
    assert P.G.hours(P.START + 8468) == "6:51" and P.G.hours(P.START + 6922) == "6:25"
    assert P.G.hours(P.START + 4123) == "5:38" and P.G.hours(P.START + 5384) == "5:59"
    assert P.G.hours(P.START + 3846) == "5:34" and P.G.hours(P.START + 4298) == "5:41"


def test_exercises():
    s64 = {int(r["scen_batch"]): r for r in _csv("sweep_64.csv")}
    assert sorted(b for b, r in s64.items() if int(r["naive_s"]) <= P.WINDOW) == [5, 10, 20, 50, 100, 250, 500]
    assert sorted(b for b, r in s64.items() if int(r["aware_s"]) <= P.WINDOW) == [5, 10, 20, 50, 100, 250, 500, 1000]
    assert min(s64, key=lambda b: int(s64[b]["naive_s"])) == 50 and min(s64, key=lambda b: int(s64[b]["aware_s"])) == 250
    ts = P.G.plan(P.book(), P.N_SCEN, P.TRADE_TARGET, 100, P.OVERHEAD)
    assert (len(ts), round(P.G.lower_bound(ts, 32)), len(ts) * 5) == (2200, 4001, 11000)
    assert round(len(ts) * 5 / sum(P.COUNTS[k] * P.costs()[k] * P.N_SCEN for k in P.COUNTS), 2) == 0.10
    assert 5400 - int(_s32()[20]["naive_s"]) == 16
    coarse = P.G.plan(P.book(), P.N_SCEN, P.TRADE_TARGET, 1000, P.OVERHEAD)
    assert round(max(t.duration for t in coarse)) == 5375
    slow = [t for t in P.G.plan([P.G.GridTrade(t.trade_id, t.kind, t.true, t.cost, t.fails) for t in P.book()], P.N_SCEN,
                                P.TRADE_TARGET, 1000, P.OVERHEAD, 600.0) if any(x.cost for x in t.trades)]
    assert {t.scenarios for t in slow[:-1]} == {122}
