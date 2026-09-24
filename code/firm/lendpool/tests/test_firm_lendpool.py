"""Acceptance tests of the Book 3, Chapter 23 build (lending pool engine)."""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from firm_lendpool import Account, Pool, RateModel, Reserve

M = RateModel(0.0, 0.04, 0.60, 0.90)


def pool():
    p = Pool({"USDC": Reserve(M), "ETH": Reserve(M)}, {"USDC": 1.0, "ETH": 3_000.0},
             ltv={"ETH": 0.80, "USDC": 0.0}, threshold={"ETH": 0.825, "USDC": 0.0}, bonus={"ETH": 0.05, "USDC": 0.0})
    p.supply("USDC", 1_000_000)
    return p


def test_kinked_rate():
    assert M.borrow_rate(0.45) == 0.02 and M.borrow_rate(0.90) == 0.04
    assert round(M.borrow_rate(0.95), 6) == 0.34


def test_borrow_health_and_accrual():
    p, a = pool(), Account({"ETH": 100.0})
    p.borrow(a, "USDC", 200_000)
    assert round(p.health(a), 6) == round(100 * 3_000 * 0.825 / 200_000, 6)
    with pytest.raises(ValueError):
        p.borrow(a, "USDC", 50_000)                          # beyond 80% of 300,000
    r = p.reserves["USDC"]
    rb, rs = r.rates()
    assert round(r.utilisation(), 6) == 0.2 and round(rs, 8) == round(rb * 0.2 * 0.9, 8)
    r.accrue(1.0)
    assert round(p.owed(a, "USDC"), 4) == round(200_000 * (1 + rb), 4)


def test_liquidation_close_factor_and_bonus():
    p, a = pool(), Account({"ETH": 100.0})
    p.borrow(a, "USDC", 240_000)
    with pytest.raises(ValueError):
        p.liquidate(a, "USDC", "ETH", 1_000)
    p.prices["ETH"] = 2_800.0                                  # health 0.9625
    seized = p.liquidate(a, "USDC", "ETH", 1e9)
    assert round(seized, 6) == round(120_000 / 2_800 * 1.05, 6)
    assert round(p.owed(a, "USDC"), 6) == 120_000


def test_flash_loan_reverts_unless_repaid():
    p = pool()
    fee = p.flash_loan("USDC", 500_000, lambda x: x * 1.0005)
    assert round(fee, 6) == 250.0
    with pytest.raises(ValueError):
        p.flash_loan("USDC", 500_000, lambda x: x)
