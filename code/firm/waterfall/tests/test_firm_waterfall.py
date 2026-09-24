"""Acceptance tests of the Book 2, Chapter 25 build (CLO waterfall)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_waterfall import Deal, Note, cutoff_cdr, equity_irr, pay_down, run


def deal(**kw) -> Deal:
    notes = [Note("AAA", 310, 0.013, False), Note("AA", 55, 0.018, False), Note("A", 30, 0.022),
             Note("BBB", 30, 0.032), Note("BB", 25, 0.060)]
    args = dict(notes=notes, par=500.0, loan_spread=0.035, rate=0.04, fee=0.0045,
                oc={1: 1.25, 2: 1.18, 3: 1.10, 4: 1.05}, ic={1: 1.20})
    args.update(kw)
    return Deal(**args)


def test_pay_down_in_order():
    notes = [Note("A", 10, 0.0), Note("B", 10, 0.0)]
    assert pay_down(notes, 15) == 0 and [n.balance for n in notes] == [0, 5]
    assert pay_down(notes, 8) == 3


def test_no_defaults_everyone_is_paid():
    periods = run(deal(), 0.0)
    assert all(p.diverted == 0 for p in periods)
    assert periods[-1].balances == [0, 0, 0, 0, 0]
    q_equity = (500 * 0.075 - 500 * 0.0045) / 4 - sum(b * (0.04 + s) / 4 for b, s in
                                                      [(310, .013), (55, .018), (30, .022), (30, .032), (25, .06)])
    assert abs(periods[0].equity - q_equity) < 1e-9
    assert abs(periods[-1].equity - (q_equity + 50)) < 1e-9


def test_cash_is_conserved():
    d = deal()
    for cdr in (0.02, 0.06, 0.12):
        periods = run(d, cdr)
        assert all(p.equity >= 0 and p.diverted >= 0 for p in periods)
        assert all(min(p.balances) >= 0 for p in periods)


def test_tests_divert_and_cutoff_is_monotone():
    d = deal()
    c = cutoff_cdr(d)
    assert any(p.equity == 0 for p in run(d, c + 1e-4)[:-1])
    assert all(p.equity > 0 for p in run(d, c - 1e-4)[:-1])
    assert equity_irr([p.equity for p in run(d, 0.0)], 50) > equity_irr([p.equity for p in run(d, 0.05)], 50)
