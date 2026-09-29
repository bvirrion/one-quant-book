import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_drplan as dr  # noqa: E402

T = {s.id: s for s in dr.gm.load_sites(dr.HERE.parents[2] / "data" / "networks" / "sites.csv")}


def test_deterministic_runbook():
    p = dr.Plan("x", "ny5", "aurora", (dr.Step("a", 30.0, 0.0), dr.Step("b", 45.0, 0.0)), "sync")
    assert set(dr.rto_samples(p, n=5)) == {75.0} and dr.p_within(p, 75.0, n=5) == 1.0 and dr.p_within(p, 74.0, n=5) == 0.0


def test_rpo_and_separation():
    s = dr.Plan("s", "ny5", "aurora", (), "sync")
    a = dr.Plan("a", "ny5", "aurora", (), "async", lag_ms=50.0)
    w = dr.Plan("w", "ny5", "aurora", (), "snapshot", snapshot_min=15.0)
    assert dr.rpo(s, T) == 0.0 and dr.rpo(w, T) == 900.0 and 0.05 < dr.rpo(a, T) < 0.06
    assert 1000 < dr.separation_km("ny5", "aurora", T) < 1200 and dr.outside_hazard(s, 100.0, T)
    assert not dr.outside_hazard(dr.Plan("n", "ny5", "ny4", (), "sync"), 1.0, T)
    assert 15 < dr.sync_penalty_ms(s, T) < 20


def test_calendar():
    assert dr.tested_within(dt.date(2025, 10, 25), dt.date(2026, 9, 28))
    assert not dr.tested_within(dt.date(2025, 9, 1), dt.date(2026, 9, 28))
    assert len(dr.load_calendar()) == 3
