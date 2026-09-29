"""Acceptance tests of firm.posttrade (One Quant Book 15, chapter 22)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_posttrade as PT  # noqa: E402

KEYS = ("symbol", "side", "cp")
TOL = {"price": 1e-4, "qty": 0, "settle": 0}


def t(sym, price, qty=100, settle=1, cp="B1", side=1):
    return {"symbol": sym, "side": side, "cp": cp, "price": price, "qty": qty, "settle": settle}


def test_match_partial_and_unmatched():
    ours = [t("A", 10.12345), t("B", 20.0), t("C", 30.0), t("D", 40.0)]
    theirs = [t("A", 10.1235), t("B", 20.5), t("C", 30.0, settle=2), t("E", 50.0)]
    r = PT.match(ours, theirs, KEYS, TOL)
    assert [o["symbol"] for o, _ in r.matched] == ["A"]
    assert [(o["symbol"], d) for o, _, _, d in r.partial] == [("B", ["price"]), ("C", ["settle"])]
    assert [o["symbol"] for o in r.ours_only] == ["D"] and [x["symbol"] for x in r.theirs_only] == ["E"]
    assert PT.match_rate(r, 4) == 0.25 and r.partial[0][2] == pytest.approx(2 / 3)


def test_best_candidate_is_chosen():
    ours = [t("A", 10.0, qty=200)]
    theirs = [t("A", 10.5, qty=100), t("A", 10.0, qty=200)]
    r = PT.match(ours, theirs, KEYS, TOL)
    assert len(r.matched) == 1 and r.theirs_only[0]["price"] == 10.5


def test_ssi_instruction():
    ssi = PT.SSITable({("B1", "US"): {"agent": "AGENT1", "account": "ACC9"}})
    trade = dict(t("A", 10.0), counterparty="B1", market="US", settle_date=3)
    ins = ssi.instruction(trade, "OURS")
    assert ins["type"] == "receive versus payment" and ins["amount"] == 1000.0 and ins["their_account"] == "ACC9"
    with pytest.raises(KeyError):
        ssi.instruction(dict(trade, counterparty="B2"), "OURS")


def test_reconcile_groups_and_ageing():
    ours = {("F1", "A"): 100, ("F2", "A"): 200, ("F1", "B"): 50}
    theirs = {("BLOCK", "A"): 300, ("F1", "B"): 40, ("F1", "C"): 10}
    brks = PT.reconcile(ours, theirs, groups={("BLOCK", "A"): [("F1", "A"), ("F2", "A")]}, opened=10.0)
    assert [(b.kind, b.key) for b in brks] == [("quantity difference", ("F1", "B")), ("missing in our books", ("F1", "C"))]
    assert PT.age(brks, now=40.0) == {"under 1 day": 0, "1 to 3 days": 2, "3 to 7 days": 0, "over 7 days": 0}
    assert PT.classify(1, None) == "missing at the custodian"
