"""Acceptance tests of firm.tradecap (One Quant Book 15, chapter 21)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_tradecap as T  # noqa: E402

A, B, C = "5493001KJTIIGC8Y1R12", "549300ZCCP000CLEAR07", "5493000DEALER0000101"


def ticket(**kw):
    t = {"uti": T.uti(A, 7), "trade_id": "S1", "buyer": A, "seller": B, "book": "Rates", "trade_date": 0,
         "settle_date": 2, "instrument": {"type": "IRSwap", "years": 5}, "quantity": 100.0, "price": 0.0, "ts": 1.0}
    t.update(kw)
    return t


def test_uti_and_validation():
    u = T.uti(A, 42)
    assert len(u) == 52 and u.startswith(A) and u.endswith("42") and T.validate(ticket()) == []
    with pytest.raises(ValueError):
        T.uti("not-an-lei", 1)
    errs = T.validate(ticket(seller=A, settle_date=-1, quantity=0, uti="lower-case"))
    assert len(errs) == 4
    assert T.validate({"trade_id": "x"})[0] == "missing uti"


def test_lifecycle_versions_and_as_of():
    s = T.TradeStore()
    s.apply(T.from_ticket(ticket()))
    s.apply(T.Event(2.0, "amend", "S1", {"quantity": 150.0}))
    s.apply(T.Event(3.0, "novate", "S1", {"side": "seller", "new": C}))
    s.apply(T.Event(4.0, "terminate", "S1", {"quantity": 60.0}))
    assert [v for _, v in s.versions("S1")] == [1, 2, 3, 4]
    assert s.as_of("S1", 2.5)["quantity"] == 150.0 and s.as_of("S1", 2.5)["seller"] == B
    assert s.as_of("S1")["quantity"] == 90.0 and s.as_of("S1")["seller"] == C and s.as_of("S1", 0.5) is None
    s.apply(T.Event(5.0, "terminate", "S1", {"quantity": 90.0}))
    assert s.as_of("S1")["status"] == "terminated"
    with pytest.raises(ValueError):
        s.apply(T.Event(1.0, "amend", "S2", {}))


def test_exercise_cancel_allocate_and_execution_capture():
    s = T.TradeStore()
    s.apply(T.from_ticket(ticket(trade_id="O1")))
    s.apply(T.Event(2.0, "exercise", "O1", {"into": {"type": "IRSwap", "years": 5}}))
    assert s.as_of("O1")["status"] == "exercised"
    e = T.from_execution({"side": 1, "qty": 300, "price": 1_000_100, "ts": 5.0, "date": 0}, A, B, "EQ", 3,
                         {"type": "Equity"})
    assert e.data["buyer"] == A and e.data["seller"] == B and T.validate(e.data) == []


def test_allocation_rules():
    fills = [(4000, 100.0), (5900, 101.0)]
    w = {"a": 0.5, "b": 0.3, "c": 0.2}
    lr, r1 = T.allocate(fills, w, "largest-remainder", 100)
    fl, r2 = T.allocate(fills, w, "floor-then-largest", 100)
    re_, r3 = T.allocate(fills, w, "round-each", 100)
    assert {f: q for f, (q, _) in lr.items()} == {"a": 4900, "b": 3000, "c": 2000} and r1 == 0
    assert {f: q for f, (q, _) in fl.items()} == {"a": 5000, "b": 3000, "c": 1900} and r2 == 0
    assert r3 == -100
    assert lr["a"][1] == pytest.approx((4000 * 100.0 + 5900 * 101.0) / 9900)


def test_booking_model():
    m = T.BookingModel({("IRSwap", "rates"): "Rates/swaps"})
    assert m.book({"type": "IRSwap"}, "rates") == "Rates/swaps"
    with pytest.raises(KeyError):
        m.book({"type": "Bond"}, "rates")
