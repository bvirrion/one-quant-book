"""Numbers gate: every numerical answer printed in Book 16, chapter 22 (text and solutions)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))

import fm_data as m  # noqa: E402

db = m.db


def r(x, d=0):
    return round(float(x), d)


def test_budget():
    b = m.the_budget()
    assert {k: r(v) for k, v in b.items()} == {"market data": 564, "terminals": 750, "reference data": 460,
                                                "alternative data": 300}
    assert r(sum(b.values())) == 2074 and r(100 * 750 / 2074, 1) == 36.2


def test_enterprise():
    p = m.PRODUCTS[4]
    assert db.enterprise_breakeven(p) == 50 and db.annual_cost(p, db.Usage(users=60)) == 480.0
    assert db.annual_cost(p, db.Usage(users=60), True) == 400.0


def test_audit():
    fees, a = m.audit()
    assert (r(fees), r(a["principal"]), r(a["interest"]), r(a["total"])) == (774, 410, 81, 490)
    assert r(100 * a["total"] / fees) == 63 and r(774 * 0.15 / 0.85, 1) == 136.6
    assert r(m.audit(0.30)[1]["total"]) == r(db.audit_exposure(774, 0.30, 3, 0.01)["total"])


def test_allocation_and_alt():
    a = m.allocation()
    assert {k: r(v, 1) for k, v in a.items()} == {"market making": 933.3, "statistical arbitrage": 622.2,
                                                  "event-driven": 311.1, "macro": 207.4}
    assert r(m.alt_value(), 1) == 368.6


def test_small_runs():
    assert db.allocate(10.0, {"a": 1, "b": 3}) == {"a": 2.5, "b": 7.5}


def test_exercises():
    assert r(m.db.alt_breakeven(0.02, 50_000.0, 0.005, 1.0, 3)) == 162
    a5, a30 = m.audit(0.05)[1], m.audit(0.30)[1]
    assert (r(a5["total"]), r(a30["total"] / 10) * 10) == (146, 1190)
