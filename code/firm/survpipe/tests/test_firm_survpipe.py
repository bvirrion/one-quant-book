"""Acceptance tests of firm.survpipe (One Quant Book 15, chapter 30)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_survpipe as S  # noqa: E402


def test_features_from_events():
    ev = [(1.0, "a", 0, 1, "B", "small", "place"), (1.1, "a", 0, 2, "S", "large", "place"),
          (2.0, "a", 0, 1, "B", "small", "fill"), (2.5, "a", 0, 2, "S", "large", "cancel"),
          (3.0, "a", 0, 3, "S", "large", "place"), (9.0, "a", 0, 3, "S", "large", "cancel")]
    f = S.features(ev)[("a", 0)]
    assert f == {"n_small": 1, "n_large": 2, "f_small": 1, "f_large": 0, "c_large": 2, "linked": 1}


def test_queue_policies():
    day0 = [S.Alert(i, 0, f"x{i}", "d", float(i)) for i in range(5)]
    day1 = [S.Alert(5, 1, "y", "d", 99.0, planted=True)]
    fifo = S.work_queue([day0, day1], per_day=2, policy="oldest")
    top = S.work_queue([day0, day1], per_day=2, policy="score")
    assert fifo.backlog == [3, 2] and [a.aid for a, _ in fifo.reviewed] == [0, 1, 2, 3]
    assert [a.aid for a, _ in top.reviewed] == [4, 3, 5, 2]          # the planted alert is reviewed on day 1


def test_archive_search_and_retention():
    msgs = [{"id": 1, "day": 0, "sender": "p1", "conv": "c1", "text": "Let's take this to WhatsApp"},
            {"id": 2, "day": 0, "sender": "p2", "conv": "c2", "text": "risk is flat"},
            {"id": 3, "day": 90, "sender": "p3", "conv": "c3", "text": "call my cell"}]
    assert S.search(msgs, [r"whats\s?app", r"call my cell"]) == [1, 3]
    kept = S.retention(msgs, now=100, keep_days=30, holds={"p1"})
    assert [m["id"] for m in kept] == [1, 3]


def test_identifiers_validation_reconciliation():
    lei, isin = S.make_lei("TEST00000000000000"), S.make_isin("XS000000001")
    assert S.lei_ok(lei) and S.isin_ok(isin) and S.isin_ok("US0378331005") and not S.isin_ok("US0378331006")
    assert S.lei_ok("5493001KJTIIGC8Y1R12") and not S.lei_ok("5493001KJTIIGC8Y1R13")
    r = {"status": "NEWT", "trn": "T1", "executing_entity": lei, "buyer": lei, "seller": lei, "isin": isin,
         "venue": "XSIM", "quantity": 100, "price": 10.5, "time": "2026-09-21T10:00:00Z"}
    assert S.validate(r) == []
    assert S.validate(dict(r, buyer="", isin=isin[:-1] + "0" if isin[-1] != "0" else isin[:-1] + "1",
                           quantity=0, time="21/09/2026")) == ["buyer", "isin", "quantity", "time"]
    trades = {"T1": {"quantity": 100, "price": 10.5}, "T2": {"quantity": 200, "price": 10.5}}
    reports = [r, dict(r, trn="T2", quantity=300), dict(r, trn="T2", status="CANC"), dict(r, trn="T2", quantity=200),
               dict(r, trn="T9"), dict(r)]
    rec = S.reconcile(reports, trades)
    assert rec == {"missing": [], "extra": ["T1#dup", "T9"], "mismatched": []}
    assert S.reconcile([r], trades)["missing"] == ["T2"]
