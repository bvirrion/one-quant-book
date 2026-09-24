"""Numbers gate: every numerical answer printed in Book 3, Chapter 1 (text and solutions)."""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "python"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/physdeal"))
from firm_physdeal import formula_price, netback
from m3_physical import VOLUME, back_to_back, differential_stats, hedged_sd_theory, simulate_cargo, unhedged_sd_usd


def test_text():
    assert 3.40 * 100_000 == 340_000 and round((82.00 - 79.10) * 100_000) == 290_000
    assert 700_000 * 80 == 56_000_000
    assert round(netback(81.30, 1.10, 0.03), 2) == 80.17 and round(netback(83.10, 3.05, 0.03), 2) == 80.02
    s = simulate_cargo()
    assert round(float(s["unhedged"].std()), 2) == 8.13 and round(float(s["hedged"].std()), 2) == 0.54
    assert round(float(s["unhedged"].std()) * VOLUME / 1e6, 1) == 5.7
    st = differential_stats()
    assert st["min"][0] == "2011-09" and round(st["min"][1], 2) == -27.31
    from m3_physical import load_differential
    apr = [w - b for m, w, b in load_differential() if m == "2026-04"][0]
    assert round(apr, 2) == -17.66


def test_exercises():
    assert round(formula_price({1: 81.20, 2: 80.70, 3: 79.90, 4: 80.40, 5: 81.05}, [1, 2, 3, 4, 5], 0.35), 2) == 81.00
    assert round(78.40 + 1.35 + 0.04, 2) == 79.79
    assert round(netback(84.10, 2.20, 0.05, 0.002), 2) == 81.68
    assert 700_000 // 1000 == 700 and 700 / 5 == 140 and 700 / 4 == 175
    assert round(2 * hedged_sd_theory(), 2) == 1.08
    assert round(netback(81.30, 1.10, 0.03) - netback(83.10, 3.05, 0.03), 2) == 0.15 and round(83.10 + 0.15, 2) == 83.25
    st = differential_stats()
    assert st["since2011_above"] == 4 and st["above"] == 115 and st["n"] == 320


def test_problem():
    bb = back_to_back()
    assert bb["days_full"] == 16 and bb["trades"][8] == -140 and bb["trades"][28] == 140
    held = sum(q for d, q in bb["trades"].items() if d <= 20)
    assert held == -700
    assert round(bb["margin"], 2) == 0.22 and round(bb["margin_usd"]) == 154_000
    assert round(unhedged_sd_usd() / 1e6, 2) == 5.63
    assert math.isclose(1.80 * math.sqrt(20) * 700_000, unhedged_sd_usd())
