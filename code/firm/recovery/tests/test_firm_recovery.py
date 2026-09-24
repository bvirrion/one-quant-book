"""Acceptance tests of the Book 2, Chapter 26 build (exchange offers, holdouts, loss absorption)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_recovery import Holdout, Offer, absorb, bond_pv, breakeven_participation, holdout_payoff, npv_haircut

H = Holdout(paid_soon=91.74, lawsuit_prob=0.3, lawsuit_pv=77.5, stuck=15.0)


def test_bond_pv_par_and_haircut():
    assert abs(bond_pv(100, 0.05, 10, 0.05) - 100) < 1e-9
    assert npv_haircut(40.0) == 0.6


def test_offer_value_falls_with_exit_yield():
    o = Offer(50, 0.04, 15, cash=5)
    assert o.value(0.06) > o.value(0.09) > o.value(0.12) > 5


def test_holdout_value_rises_with_participation_and_cac_binds():
    assert H.value(0.2) < H.value(0.6) < H.value(0.9)
    assert holdout_payoff(0.8, H, 30.0, 0.75) == 30.0 and holdout_payoff(0.8, H, 30.0, None) == H.value(0.8)


def test_breakeven():
    t = 35.0
    p = breakeven_participation(H, t)
    assert abs(H.value(p) - t) < 1e-9 and 0 < p < 1


def test_absorb_order():
    stack = [("equity", 10.0), ("AT1", 5.0), ("T2", 5.0)]
    assert absorb(stack, 12.0) == {"equity": 0.0, "AT1": 3.0, "T2": 5.0}
    assert absorb([("AT1", 5.0), ("equity", 10.0)], 5.0) == {"AT1": 0.0, "equity": 10.0}
