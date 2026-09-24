"""Tests of the Chapter 23 teaching module (Book 3)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
import m3_defi as m


def test_curve_and_health():
    rows = {round(100 * u): (rb, rs) for u, rb, rs in m.rate_curve()}
    assert round(rows[90][0], 4) == 0.04 and round(rows[100][0], 4) == 0.64
    h = dict(m.health_path())
    assert round(h[3_000], 4) == 1.0312 and h[2_900] < 1 < h[2_950]


def test_flash_liquidation():
    r = m.flash_liquidation()
    assert r["seized"] == 45.0 and round(r["usdc"], 2) == 124_504.82 and round(r["profit"], 2) == 4_444.82
    assert r["health_after"] > 1


def test_pump():
    k = m.pump_needed(50e6, 5e6, 0.6)
    assert round(k, 2) == 16.67
    spent, frac = m.pump_cost(2e6, k)
    assert round(spent / 1e6, 2) == 6.16 and round(frac * 2e6 / 1e6, 2) == 1.51
    assert round(m.pump_attack(k) / 1e6, 2) == 38.84
    assert m.pump_attack(40) < m.pump_attack(k)
