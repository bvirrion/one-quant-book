"""Acceptance tests of firm.posservice (One Quant Book 15, chapter 17)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_posservice as P  # noqa: E402


def ex(i, side, qty, price, ts, td=0, sd=1, fee=0, sym="X"):
    return P.Execution(f"e{i}", "A", sym, side, qty, price, ts, td, sd, fee)


def test_idempotent_merge_and_status():
    s = P.PositionService()
    assert s.on_execution("session", ex(1, 1, 100, 1_000_000, 10))
    assert not s.on_execution("dropcopy", ex(1, 1, 100, 1_000_000, 10))
    assert s.position("A", "X").quantity == 100 and s.status("A", "X") == "agreed"
    s.on_execution("dropcopy", ex(2, 1, 200, 1_000_100, 20))
    assert s.status("A", "X") == "pending" and s.missing("session") == {"e2"} and s.position("A", "X").quantity == 300
    s.on_execution("session", ex(2, 1, 200, 1_000_100, 20))
    assert s.status("A", "X") == "agreed"


def test_exact_pnl_and_order_independence():
    a, b = P.PositionService(), P.PositionService()
    es = [ex(1, 1, 100, 1_000_000, 1, fee=50), ex(2, -1, 300, 1_000_200, 2), ex(3, 1, 100, 999_900, 3)]
    for e in es:
        a.on_execution("session", e)
    for e in reversed(es):
        b.on_execution("dropcopy", e)
    total, realised, unreal = a.pnl("A", "X", 1_000_000)
    assert (total, realised, unreal) == b.pnl("A", "X", 1_000_000)
    p = a.position("A", "X")
    assert p.quantity == -100 and total == p.cash + p.quantity * 1_000_000 - 50
    assert realised == 100 * 200 + 100 * 300 and total == realised + unreal - 50


def test_bust_and_correction_are_events():
    s = P.PositionService()
    s.on_execution("session", ex(1, 1, 100, 1_000_000, 10))
    s.on_execution("session", ex(2, 1, 100, 1_000_000, 20))
    s.on_bust("e2", 100)
    s.on_correction("e1", 200, qty=50)
    assert s.position("A", "X", as_of=50).quantity == 200
    assert s.position("A", "X", as_of=150).quantity == 100 and s.position("A", "X").quantity == 50


def test_views_days_and_reconciliation():
    s = P.PositionService()
    s.on_execution("session", ex(1, 1, 100, 1_000_000, 10, td=0, sd=1))
    s.on_execution("session", ex(2, 1, 100, 1_000_000, 20, td=1, sd=2))
    assert s.position("A", "X", view="settlement", date=0).quantity == 0
    assert s.position("A", "X", view="settlement", date=1).quantity == 100 and s.position("A", "X").quantity == 200
    eod = s.end_of_day(1, {"X": 1_000_500})
    assert eod[("A", "X")] == (200, 1_000_500, 200 * 500) and s.start_of_day(2) == eod and s.start_of_day(1) == {}
    assert P.reconcile(s, {("A", "X"): 200}) == [] and P.reconcile(s, {("A", "X"): 100}) == [("A", "X", 200, 100)]
