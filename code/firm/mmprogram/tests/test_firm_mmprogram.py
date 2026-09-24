"""Acceptance tests of the Book 3, Chapter 25 build (market-maker programme monitor)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "ratelimit"))
from firm_mmprogram import Snapshot, VolTier, compliant, monthly_fees, rebate, requote_budget, tier_for, uptime
from firm_ratelimit import binance_like

TIERS = [VolTier(0, 10, 10), VolTier(1e6, 9, 10), VolTier(20e6, 4, 6), VolTier(150e6, 2.5, 3.1)]


def test_tiers_and_fees():
    assert tier_for(5e5, TIERS).maker_bp == 10 and tier_for(2e8, TIERS).maker_bp == 2.5
    assert monthly_fees(100e6, 0.7, TIERS) == 100e6 * (0.7 * 4 + 0.3 * 6) / 1e4
    assert monthly_fees(100e6, 0.7, TIERS, matched=VolTier(0, 2.5, 3.1)) < monthly_fees(100e6, 0.7, TIERS)
    assert monthly_fees(100e6, 0.7, TIERS, matched=VolTier(0, 9, 10)) == monthly_fees(100e6, 0.7, TIERS)


def test_uptime_and_rebate():
    ok = Snapshot(100.0, 99.95, 100.05, 60_000, 60_000)
    wide = Snapshot(100.0, 99.0, 101.0, 60_000, 60_000)
    thin = Snapshot(100.0, 99.95, 100.05, 60_000, 10_000)
    off = Snapshot(100.0, None, 100.05, 0, 60_000)
    assert compliant(ok, 20, 50_000) and not compliant(wide, 20, 50_000) and not compliant(thin, 20, 50_000)
    assert uptime([ok, ok, ok, wide, off], 20, 50_000) == 0.6
    assert rebate(1e8, 0.5, 0.95, 0.90) == 5_000 and rebate(1e8, 0.5, 0.85, 0.90) == 0


def test_requote_budget():
    # the daily rule (200,000 a day, 2.31 a second) binds before the 100-per-10-seconds rule
    assert round(requote_budget(binance_like(), 5), 4) == round(200_000 / 86_400 / 5, 4)
