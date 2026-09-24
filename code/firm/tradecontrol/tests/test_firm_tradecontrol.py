import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_tradecontrol as f


def trade(i, **kw):
    base = dict(trade_id=f"T{i}", trader="A", executed=10.0, booked=10.5, price=100.0, mid=100.0, spread=0.1,
                counterparty="EXT:X", mirror=None, settle_days=2)
    base.update(kw)
    return f.Trade(**base)


def test_each_rule():
    assert f.late_booking(trade(1, booked=20.0)) and not f.late_booking(trade(2))
    assert f.cancel_amend_near(trade(3, status="cancelled", status_time=100.0), [110.0])
    assert not f.cancel_amend_near(trade(4, status="cancelled", status_time=100.0), [200.0])
    assert f.off_market(trade(5, price=100.5)) and not f.off_market(trade(6, price=100.2))
    assert f.internal_unmatched(trade(7, counterparty="INT:B", mirror="T99"), {"T7"})
    assert not f.internal_unmatched(trade(8, counterparty="INT:B", mirror="T9"), {"T8", "T9"})
    assert f.deferred_settlement(trade(9, settle_days=90))


def test_evaluation_and_audit_log():
    blotter = [trade(1, booked=30.0, fraud=True), trade(2), trade(3, price=101.0)]
    ev = f.evaluate(blotter, f.run_rules(blotter, []))
    assert ev["late booking"] == {"hit": 1.0, "false": 0.0} and ev["combined"]["false"] == 0.5
    log = f.AuditLog()
    for t in blotter:
        log.append(f.trade_event(t))
    assert log.verify()
    log.entries[1]["event"]["price"] = 99.0
    assert not log.verify()
