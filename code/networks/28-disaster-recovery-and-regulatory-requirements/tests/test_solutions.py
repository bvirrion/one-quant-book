"""Numbers gate: every number printed in Book 14, chapter 28 (text and solutions)."""
import datetime as dt
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "python"))
import nw_dr as n  # noqa: E402

dr = n.dr


def test_sites():
    s = n.separations()
    assert [round(s[c], 1) for c in n.CANDIDATES] == [0.3, 26.0, 34.2, 1191.1]
    assert [s[c] > n.HAZARD_KM for c in n.CANDIDATES] == [False, False, False, True]
    assert round(dr.sync_penalty_ms(n.HOT, n.SITES), 1) == 17.4
    assert round(dr.sync_penalty_ms(dr.Plan("m", "ny5", "mahwah", (), "sync"), n.SITES), 1) == 0.5


def test_designs():
    r = n.results()
    h, w = r["hot"], r["warm"]
    assert (round(100 * h["p2h"], 1), round(h["median"]), round(h["p95"])) == (99.2, 64, 96)
    assert (round(100 * w["p2h"], 1), round(w["median"]), round(w["p95"])) == (20.3, 148, 237)
    assert (round(1000 * h["rpo_s"]), w["rpo_s"]) == (56, 900.0)
    assert round((h["cost"] - w["cost"]) / 1000, 2) == 1.44 and n.PRIMARY_COST == 3190.0
    steps = tuple(dr.Step(s.name, 22.5 if s.name.startswith("start") else s.median_min, s.sigma) for s in n.WARM.steps)
    p = dr.Plan("w2", n.PRIMARY, "aurora", steps, "snapshot", snapshot_min=15)
    assert round(100 * dr.p_within(p, 120), 1) == 44.1


def test_small_runs():
    assert dr.tested_within(dt.date(2025, 10, 25), dt.date(2026, 9, 28))
    assert not dr.tested_within(dt.date(2025, 10, 25), dt.date(2026, 11, 1))
    assert [s.median_min for s in n.HOT.steps] == [15, 10, 20, 10, 5]
    assert sum(s.median_min for s in n.WARM.steps if not s.name.startswith("start")) == 90
