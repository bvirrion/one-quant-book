"""Tests of the Chapter 20 teaching module (Book 3)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import m3_amm as m


def test_impermanent_loss():
    assert round(100 * m.impermanent_loss(2), 1) == -5.7 and round(100 * m.impermanent_loss(0.5), 1) == -5.7
    assert m.impermanent_loss(1) == 0
    assert m.impermanent_loss_range(1.05, 0.1) < m.impermanent_loss(1.05)      # narrower range loses faster
    assert abs(m.range_value(1.0, 1 / 1.1, 1.1) - 2 * (1 - (1 / 1.1) ** 0.5)) < 1e-12


def test_lvr_matches_closed_form():
    acc, _ = m.lvr_mean()
    assert abs(1e4 * acc[-1] - 1e4 * 0.36 / 8 * 30 / 365) < 1.0                  # within 1 bp of 37.0 bp


def test_breakeven_and_stableswap():
    assert round(100 * m.breakeven_turnover(0.6, 0.003), 2) == 4.11
    pts = dict(m.stableswap_curve())
    assert abs(pts[5.0] - 5.0) < 1e-6 and pts[4.0] < 6.1 and pts[1.0] > 9.0
