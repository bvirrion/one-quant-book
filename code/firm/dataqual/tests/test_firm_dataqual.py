"""Acceptance tests of firm.dataqual (One Quant Book 15, chapter 7)."""
import pathlib
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_dataqual import Lineage, Quarantine, Rule, clean, run

S = 10**9


def trades(n=200, seed=1):
    rng = np.random.default_rng(seed)
    price = 10_000 + np.cumsum(rng.choice([-1, 0, 0, 1], n)) * 10
    return pd.DataFrame({"seq": np.arange(1, n + 1), "ts": np.arange(n) * S, "symbol": "X", "price": price,
                         "qty": 100, "match": np.arange(n) + 1000})


def test_each_kind_finds_its_defect_and_nothing_else():
    t = trades()
    t.loc[50, "price"] *= 10                                   # a decimal slip
    t = t.drop(index=range(100, 104))                         # a gap of four
    t.loc[150:, "ts"] += 45 * S                               # a silence
    rules = {"t": [Rule("seq", "sequence", "error", params={"column": "seq"}),
                   Rule("spike", "spike", "error", params={"column": "price", "k": 8, "window": 30, "floor": 1e-3,
                                                            "confirm": True, "by": "symbol"}),
                   Rule("stale", "stale", params={"time": "ts", "max_gap": 30 * S, "by": "symbol"}),
                   Rule("bust", "busted", "error", params={"key": "match", "busted": [1170]}),
                   Rule("pos", "bounds", "error", params={"column": "qty", "lo": 1, "hi": 10**6})]}
    f = run(rules, {"t": t})
    by = {r: sorted(x.row for x in f if x.rule == r) for r in ("seq", "spike", "stale", "bust", "pos")}
    assert by == {"seq": [104], "spike": [50], "stale": [150], "bust": [170], "pos": []}
    assert "gap of 4" in [x.detail for x in f if x.rule == "seq"][0]
    kept = clean(t, f, "t", ("error",))
    assert 50 not in kept.index and 170 not in kept.index and 150 in kept.index


def test_confirm_spares_a_level_shift_and_exempt_spares_a_halt():
    t = trades()
    t.loc[120:, "price"] = (t.loc[120:, "price"] * 1.05).round()
    naive = {"t": [Rule("s", "spike", params={"column": "price", "k": 8, "window": 30, "floor": 1e-3})]}
    aware = {"t": [Rule("s", "spike", params={"column": "price", "k": 8, "window": 30, "floor": 1e-3, "confirm": True})]}
    assert len(run(naive, {"t": t})) > 5 and run(aware, {"t": t}) == []
    t.loc[80:, "ts"] += 60 * S
    stale = {"t": [Rule("st", "stale", params={"time": "ts", "max_gap": 30 * S, "by": "symbol",
                                                "exempt": [("X", 79 * S + 1, 80 * S + 60 * S)]})]}
    assert run(stale, {"t": t}) == []


def test_cross_source_counts_by_bucket():
    t = trades(120)
    ref = t.copy()
    mine = t.drop(index=range(70, 80))
    r = {"t": [Rule("x", "cross_source", params={"time": "ts", "bucket": 60 * S, "tol": 0.02, "reference": ref})]}
    f = run(r, {"t": mine})
    assert len(f) == 1 and "50 rows against 60" in f[0].detail


def test_quarantine_and_release():
    q = Quarantine()
    assert q.apply("p1", []) == "published" and q.readable("p1")
    t = trades()
    t.loc[3, "qty"] = 0
    f = run({"t": [Rule("pos", "bounds", "error", params={"column": "qty", "lo": 1, "hi": 10**6})]}, {"t": t})
    assert q.apply("p2", f) == "quarantined" and not q.readable("p2")
    q.release("p2", "on-call", "checked")
    assert q.readable("p2") and q.log[-1][1:] == ("released", "checked", "on-call")
    with pytest.raises(ValueError):
        q.release("p1", "x", "y")


def test_lineage_names_what_a_correction_makes_stale():
    lin = Lineage()
    a = lin.add("closes", {"x": 1})
    b = lin.add("marks", {"x": 1.0}, [a])
    c = lin.add("pnl", {"d": 2.0}, [b])
    d = lin.add("bars", {"n": 3})
    assert lin.stale_after("closes", a[1]) == {b, c} and lin.upstream(c) == {a, b} and lin.downstream(d) == set()
    assert lin.add("closes", {"x": 2}) != a
