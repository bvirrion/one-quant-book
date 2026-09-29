"""Acceptance tests of firm.entitle (One Quant Book 15, chapter 23)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import firm_entitle as E  # noqa: E402


def _ents():
    ents = E.EntitlementSystem()
    ents.grant(E.Entitlement("app:a", "SRC", "non-display"), 0.0)
    ents.grant(E.Entitlement("user:u", "SRC", "display"), 0.0)
    ents.revoke(E.Entitlement("user:u", "SRC", "display"), 5.0)
    return ents


def test_entitlement_checks():
    ents = _ents()
    assert ents.check("app:a", "SRC", "non-display", 1.0)
    assert not ents.check("app:a", "SRC", "display", 1.0)              # the use matters
    assert ents.check("user:u", "SRC", "display", 4.9) and not ents.check("user:u", "SRC", "display", 5.0)
    bus = E.Bus(ents)
    assert not bus.subscribe("x", "app:b", "SRC", "non-display", ["T"], 0.0)


def test_queue_all_and_conflate():
    ups = [(0.0, "T", 1), (0.0, "T", 2), (0.0, "U", 3), (0.0, "T", 4)]
    for pol, delivered, depth in (("all", 4, 3), ("conflate", 3, 2)):   # the first is served at once
        bus = E.Bus(_ents())
        bus.subscribe("s", "app:a", "SRC", "non-display", ["T", "U"], 1.0, pol)
        st = bus.run(ups)["s"]
        assert (st.delivered, st.max_depth) == (delivered, depth)
    assert st.max_age == pytest.approx(3.0)                   # T1, then U, then the latest T (T2 dropped)


def test_busy_subscriber_is_scheduled():
    bus = E.Bus(_ents())
    bus.subscribe("s", "app:a", "SRC", "non-display", ["T"], 1.0)
    st = bus.run([(0.0, "T", 1), (0.5, "T", 2), (3.0, "T", 3)])["s"]
    assert st.delivered == 3 and st.max_age == pytest.approx(1.5)


def test_revocation_at_delivery():
    ups = [(float(t), "T", t) for t in range(10)]
    for check, delivered, denied in ((True, 5, 5), (False, 10, 0)):
        bus = E.Bus(_ents(), check_on_delivery=check)
        bus.subscribe("scr", "user:u", "SRC", "display", ["T"], 0.1)
        st = bus.run(ups)["scr"]
        assert (st.delivered, st.denied) == (delivered, denied)


def test_usage_report_and_audit():
    log = E.UsageLog()
    for m in range(2):
        for uid in ("u1", "u1", "u2", "u2b"):                     # one person, two identifiers: two units
            log.record(m, "SRC", "display", uid, uid[:2])
        for d in range(m + 1):
            log.record(m, "SRC", "non-display", f"host{d}", "app")
    assert E.usage_report(log, 1, "SRC") == {"display": 3, "non-display": 2}
    rows = E.audit(log, "SRC", range(2), {"display": 2}, {"display": lambda n: 10 * n, "non-display": lambda n: 100 * n})
    assert [r.owed for r in rows] == [110.0, 210.0] and rows[1].shortfall == {"display": 1, "non-display": 2}
